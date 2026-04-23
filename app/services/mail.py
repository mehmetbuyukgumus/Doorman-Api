import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Inter', sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #ffffff; }
        .header { border-bottom: 2px solid #002a35; padding-bottom: 20px; margin-bottom: 25px; text-align: center; }
        .logo { height: 100px; width: auto; max-width: 100%; object-fit: contain; }
        .content { margin-bottom: 20px; }
        .property-card { background: #fcfcfc; border: 1px solid #eee; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .property-image { width: 100%; border-radius: 8px; margin-bottom: 15px; display: block; }
        .neighborhood { color: #002a35; margin: 0 0 10px 0; font-size: 1.2em; font-weight: bold; }
        .details { display: table; width: 100%; border-spacing: 0 8px; font-size: 0.95em; }
        .detail-row { display: table-row; }
        .detail-label { display: table-cell; font-weight: bold; width: 40%; color: #666; padding: 4px 0; }
        .detail-value { display: table-cell; font-weight: bold; color: #111; padding: 4px 0; }
        .footer { font-size: 0.8em; color: #999; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; line-height: 1.5; }
        .btn-container { text-align: center; margin-top: 20px; }
        .btn { display: inline-block; padding: 14px 30px; background: #002a35; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 1rem; }
        .eval-msg { margin-top: 25px; padding: 20px; background-color: #f9f9f9; border-left: 4px solid #f2d17d; font-style: italic; color: #444; border-radius: 4px; line-height: 1.7; }
        
        @media only screen and (max-width: 600px) {
            .container { width: 95% !important; margin: 10px auto !important; padding: 15px !important; }
            .logo { height: 80px !important; }
            .details, .detail-row, .detail-label, .detail-value { display: block !important; width: 100% !important; }
            .detail-label { padding-bottom: 0 !important; }
            .detail-value { padding-top: 0 !important; margin-bottom: 10px !important; }
            .btn { width: 100%; box-sizing: border-box; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="https://doorman.fr/doormanlogo.webp" alt="Doorman Real Estate" class="logo">
        </div>
        
        <div class="content">
            <h2 style="margin-top: 0; color: #002a35; text-align: center;">Yeni Yatırım Fırsatı</h2>
            <p>Sayın {{ investor_name }},</p>
            <p>Güncel gayrimenkul fırsatını aşağıda inceleyebilirsiniz:</p>
            
            <div class="property-card">
                {% if image_url %}
                <img src="{{ image_url }}" alt="Property" class="property-image">
                {% endif %}
                
                <h3 class="neighborhood">{{ listing.neighborhood }} / {{ listing.zip_code }}</h3>
                
                <div class="details">
                    <div class="detail-row">
                        <div class="detail-label">Fiyat:</div>
                        <div class="detail-value">{{ price_formatted }} €</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Alan:</div>
                        <div class="detail-value">{{ listing.square_meters }} m²</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">M² Fiyatı:</div>
                        <div class="detail-value">{{ price_per_sqm_formatted }} €/m²</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Oda Sayısı:</div>
                        <div class="detail-value">{{ listing.rooms }}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Enerji Sınıfı:</div>
                        <div class="detail-value">{{ listing.dpe or 'N/A' }}</div>
                    </div>
                </div>
                
                <div class="btn-container">
                    <a href="{{ listing.url }}" class="btn">İlan Detaylarını Gör</a>
                </div>
            </div>
            
            {% if additional_message %}
            <div class="eval-msg">
                {{ additional_message }}
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            &copy; 2026 Doorman. Tüm hakları saklıdır.<br>
            Bu e-posta yatırım projeniz için oluşturulmuştur.<br><br>
            <a href="https://api.doorman.fr/unsubscribe?email={{ investor_email }}&name={{ investor_name }}" style="font-size: 0.85em; opacity: 0.8; color: #999; text-decoration: underline;">
                Bu bülteni artık almak istemiyorsanız, lütfen buraya tıklayın. / 
                Si vous ne souhaitez plus recevoir cette newsletter, veuillez cliquer ici.
            </a>
        </div>
    </div>
</body>
</html>
"""

async def send_email(to_email: str, subject: str, body: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    from_name = os.getenv("SMTP_FROM_NAME", "Doorman")

    message = MIMEMultipart()
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    # Determine if we should use SSL/TLS directly (port 465) or STARTTLS (port 587)
    use_tls = True if smtp_port == 465 else False
    start_tls = True if smtp_port == 587 else False

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=use_tls,
            start_tls=start_tls,
            validate_certs=False,
            timeout=10
        )
        return True
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Auth Error for {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"General SMTP Error for {to_email} ({type(e).__name__}): {e}")
        return False

def format_currency(value):
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except:
        return value

async def send_research_listing_to_investors(investors, listing, image_url, additional_message):
    template = Template(HTML_TEMPLATE)
    
    price_formatted = format_currency(listing.price)
    price_per_sqm_formatted = format_currency(listing.price_per_sqm)
    
    subject = f"Yeni Yatırım Fırsatı: {listing.neighborhood} - {price_formatted} €"
    
    success_count = 0
    for investor in investors:
        html_content = template.render(
            investor_name=investor.full_name,
            investor_email=investor.email,
            listing=listing,
            image_url=image_url,
            additional_message=additional_message,
            price_formatted=price_formatted,
            price_per_sqm_formatted=price_per_sqm_formatted
        )
        success = await send_email(investor.email, subject, html_content)
        if success:
            success_count += 1
            
    return success_count
