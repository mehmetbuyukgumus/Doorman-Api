import os
import io
import json
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from PIL import Image, ImageOps
import pillow_heif

logger = logging.getLogger(__name__)

# Register HEIC/HEIF opener with Pillow for iPhone photo support
pillow_heif.register_heif_opener()

# Allowed image formats & extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".tiff", ".gif"}

# MinIO / S3 Configuration from Environment Variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "doorman-media")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "t")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")

def get_s3_client():
    protocol = "https" if MINIO_SECURE else "http"
    endpoint_url = MINIO_ENDPOINT
    if not endpoint_url.startswith("http://") and not endpoint_url.startswith("https://"):
        endpoint_url = f"{protocol}://{endpoint_url}"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

def ensure_bucket_exists():
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=MINIO_BUCKET_NAME)
        logger.info(f"MinIO bucket '{MINIO_BUCKET_NAME}' exists.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            logger.info(f"Creating MinIO bucket '{MINIO_BUCKET_NAME}'...")
            s3.create_bucket(Bucket=MINIO_BUCKET_NAME)
        else:
            logger.error(f"Error checking bucket '{MINIO_BUCKET_NAME}': {e}")
            raise e

    # Apply public read policy so uploaded images can be accessed directly via URL
    public_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{MINIO_BUCKET_NAME}/*"],
            }
        ],
    }
    try:
        s3.put_bucket_policy(
            Bucket=MINIO_BUCKET_NAME,
            Policy=json.dumps(public_policy)
        )
        logger.info(f"Public read policy set on bucket '{MINIO_BUCKET_NAME}'.")
    except Exception as e:
        logger.warning(f"Could not set bucket policy on '{MINIO_BUCKET_NAME}': {e}")

def process_and_convert_to_webp(file_content: bytes, original_filename: str) -> tuple[bytes, str]:
    ext = os.path.splitext(original_filename.lower())[1] if original_filename else ""
    if ext and ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join([e.replace(".", "").upper() for e in sorted(ALLOWED_EXTENSIONS)])
        raise ValueError(f"File type '{ext}' not allowed. Allowed formats: {allowed_list}")

    try:
        image = Image.open(io.BytesIO(file_content))
        
        # Auto-rotate based on EXIF orientation tag (e.g. mobile phone photos)
        image = ImageOps.exif_transpose(image)
        
        # Convert palette/CMYK modes to RGB or RGBA for WebP saving
        if image.mode in ("P", "CMYK", "1", "LA"):
            image = image.convert("RGBA" if "transparency" in image.info or image.mode == "LA" else "RGB")

        # Resize large property photos to max 1920x1920 while preserving aspect ratio
        max_dimension = (1920, 1920)
        image.thumbnail(max_dimension, Image.Resampling.LANCZOS)

        # Save to WebP format in memory with optimized quality
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="WEBP", quality=82, optimize=True)
        webp_bytes = output_buffer.getvalue()

        # Generate unique file key with .webp extension
        file_key = f"{uuid.uuid4()}.webp"
        return webp_bytes, file_key
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Image processing failed for {original_filename}: {e}")
        raise ValueError("Invalid image file or unsupported image structure.")

def upload_file(file_content: bytes, original_filename: str, content_type: str = "image/jpeg") -> dict:
    # Validate format and convert image to WebP
    webp_content, file_key = process_and_convert_to_webp(file_content, original_filename)

    s3 = get_s3_client()
    s3.put_object(
        Bucket=MINIO_BUCKET_NAME,
        Key=file_key,
        Body=webp_content,
        ContentType="image/webp"
    )

    public_base = MINIO_PUBLIC_URL.rstrip("/")
    if public_base.endswith("/media") or "/media" in public_base:
        public_url = f"{public_base}/{file_key}"
    else:
        public_url = f"{public_base}/{MINIO_BUCKET_NAME}/{file_key}"

    return {
        "url": public_url,
        "public_id": file_key
    }

def get_file(file_key: str) -> tuple[bytes | None, str]:
    if not file_key:
        return None, "image/webp"
    # Normalize key (strip leading paths or bucket name if passed)
    clean_key = file_key.split("/")[-1]
    s3 = get_s3_client()
    try:
        response = s3.get_object(Bucket=MINIO_BUCKET_NAME, Key=clean_key)
        file_bytes = response["Body"].read()
        content_type = response.get("ContentType", "image/webp")
        return file_bytes, content_type
    except Exception as e:
        logger.error(f"Failed to fetch file '{clean_key}' from MinIO: {e}")
        return None, "image/webp"

def delete_file(file_key: str) -> bool:
    if not file_key:
        return False
    clean_key = file_key.split("/")[-1]
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=MINIO_BUCKET_NAME, Key=clean_key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete file '{clean_key}' from MinIO: {e}")
        return False
