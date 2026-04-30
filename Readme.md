# Coworking Space Booking System

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![CI](https://github.com/yourusername/coworker-rooms-app/actions/workflows/ci.yml/badge.svg)

A robust, scalable, and stateless web application for managing and booking rooms across multiple coworking spaces. This project is built with a strong focus on **enterprise-grade architecture**, **observability**, and **deployment best practices** following the 12-Factor App methodology.

## 🏢 Project Theme & Main Idea
The core idea of this platform is to provide a seamless booking experience for coworking space users while ensuring zero double-bookings. The system supports multiple coworking locations, individual room capacities, and time-slot reservations. 

Under the hood, the application is designed to be fully **stateless** and horizontally scalable, utilizing a central database and caching layer to synchronize state across multiple backend instances.

## 🚀 Technologies Used

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
- **Database ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) with PostgreSQL
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)
- **Caching & State:** [Redis](https://redis.io/)

### Frontend
- **UI:** Vanilla HTML5, CSS3 (CSS Grid & Flexbox)
- **Logic:** Vanilla JavaScript (ES6+ API Fetch)

### Infrastructure & DevOps
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy & Load Balancer:** Nginx
- **Database Management:** PgAdmin4
- **CI/CD:** GitHub Actions (Automated Build & Push to GHCR)

## 📐 Architectural Best Practices

- **Stateless Scalability:** The backend can be scaled to multiple replicas using Docker Compose (`--scale backend=3`), with Nginx automatically round-robining incoming traffic.
- **Repository Pattern (CRUD Layer):** API routers are kept clean and free of business logic. All database interactions are encapsulated within a dedicated generic CRUD service layer.
- **Advanced Data Integrity:** Prevents overlapping room reservations at the database level using PostgreSQL GiST indexes and `EXCLUDE` constraints.
- **Soft Deletes:** Records are never permanently deleted. SQLAlchemy query interceptors automatically filter out soft-deleted records from standard queries.
- **Structured Observability:** Python's logging is completely overhauled to output **Structured JSON**. Each request generates an `X-Request-ID` injected into global context variables, ensuring end-to-end distributed trace tracking across all logs.
- **Centralized Rate Limiting:** API endpoints are protected by a Redis-backed rate limiter (e.g., 100 requests / hour) that safely operates across all scaled container instances.
- **Immutable Releases:** CI pipeline strictly separates build and configuration, tagging Docker images with unique Git commit SHAs.

## 📂 Project Structure

```text
coworker-rooms-app/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # API Routing controllers
│   │   ├── core/           # Configs, DB setup, SQL init scripts
│   │   ├── crud/           # Repository pattern data access layer
│   │   ├── middleware/     # Rate limiting and Request ID logging
│   │   ├── models/         # SQLAlchemy database models
│   │   └── schemas/        # Pydantic validation models
│   ├── scripts/            # Container startup scripts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.js              # Client-side API interactions
│   ├── index.html          # Vanilla UI
│   ├── style.css           # Styling
│   ├── default.conf        # Nginx configuration for static serving & API proxy
│   └── Dockerfile
├── deploy/
│   ├── docker-compose.dev.yml # Local development orchestration
│   ├── docker-compose.yml     # Production orchestration (uses GHCR images)
│   └── nginx.conf             # Nginx Load Balancer config
└── .github/workflows/ci.yml   # GitHub Actions CI/CD Pipeline
```

## 🏁 Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed
- Git

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/coworker-rooms-app.git
cd coworker-rooms-app/deploy
```

### 2. Configure Environment Variables
Create a `.env` file in the `deploy` directory (or wherever your compose file expects it) and populate it with your local development secrets:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=coworking
SECRET_KEY=your_jwt_secret_key
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
```

### 3. Spin up the cluster
Launch the application stack using Docker Compose. We recommend scaling the backend to see the load balancer and Redis rate limiter in action:
```bash
docker-compose -f docker-compose.dev.yml up -d --scale backend=3 --build
```

### 4. Access the Application
- **Web UI:** http://localhost:3000
- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **PgAdmin (Database Management):** http://localhost:5050
- **Redis Commander:** http://localhost:8081

### 5. View Structured Logs
To see the JSON structured logs with injected Request IDs flowing across your scaled instances:
```bash
docker-compose -f docker-compose.dev.yml logs -f backend
```

## 📄 License
This project is licensed under the MIT License.