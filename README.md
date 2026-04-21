# Doorman Real Estate Backend

Professional digital management center backend for **Doorman SAS**. Built with FastAPI, this robust API provides the foundation for real estate property management, blog editorial systems, and internal research tools.

## 🚀 Features

- **Core Property Management**: Full CRUD operations for property listings with advanced filtering (price, location, type, etc.).
- **Professional Auth System**: JWT-based authentication with Role-Based Access Control (RBAC) including `superuser` and `editor` roles.
- **Editorial Infrastructure**: Comprehensive blog system with ownership checks and approval workflows for content curators.
- **Cloud Media Integration**: Seamless image management integrated with Cloudinary (upload, delete, optimize).
- **Internal Research Tools**: Management system for research listings, buyers, and market analysis tags.
- **Client Engagement**: Automated contact form message handling and management.
- **Security & Stability**:
  - Rate limiting (SlowAPI) to prevent abuse.
  - Resource protection via RBAC.
  - Automated CI/CD with Git tagging and Docker Hub synchronization.

## 🛠️ Technology Stack

- **Lanuage**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: OAuth2 with JWT (Jose)
- **Image Storage**: Cloudinary
- **Deployment**: Docker, CapRover

## 📦 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Docker (optional for local development)

### Installation

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd backend
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in your credentials.

   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`. Documentation (Swagger) is available at `/docs`.

## 🚢 Deployment

The project is configured for automated deployment via **GitHub Actions** to **CapRover**.

### Continuous Integration (CI)

Upon pushing to the `main` branch, the workflow:

1. Automatically increments the version and creates a **GitHub Release**.
2. Builds and pushes the Docker image to **Docker Hub** with version-specific tags.
3. Triggers a deployment on **CapRover** (Application: `backend-apartments`).

## 📁 Project Structure

```text
├── .github/workflows/   # CI/CD pipelines
├── app/                 # Main application logic (if refactored)
├── auth.py              # JWT and Authentication utilities
├── crud.py              # Database operations
├── database.py          # SQLAlchemy setup
├── main.py              # FastAPI entry point and routes
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic validation schemas
├── requirements.txt     # Dependencies
└── Dockerfile           # Container configuration
```

## 📄 License

This project is proprietary and confidential. All rights are reserved by **Doorman SAS**. See the [LICENSE](LICENSE) file for more information.
