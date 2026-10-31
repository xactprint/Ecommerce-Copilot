## For Testing : 

user : admin | password : admin123456


# Ecommerce Copilot

**Turn e-commerce data into clear insights and actionable decisions.**

Ecommerce Copilot is a full-stack e-commerce management and analytics application designed to help online sellers monitor their products, orders, inventory, and business performance from a single dashboard.

The project combines a modern **React + TypeScript frontend** with a **Django REST API**, **PostgreSQL on Neon**, and a production deployment on **Vercel**.

> **Status:** MVP — deployed and operational

**Live application:**  
https://ecommerce-copilot-flax.vercel.app

---

## Overview

Managing an online store generates a large amount of data: products, orders, inventory levels, sales activity, and customer transactions.

Ecommerce Copilot aims to transform this raw data into a simple and actionable business view.

The application provides:

- A centralized dashboard
- Product management
- Order management
- Inventory visibility
- Authentication and user management
- Django administration
- REST API access
- PostgreSQL persistence
- Production-ready deployment
- A foundation for future AI-powered e-commerce insights

The long-term vision is to evolve Ecommerce Copilot from a traditional e-commerce management interface into an **AI-powered business copilot** capable of helping merchants understand what is happening in their store and decide what to do next.

---

## Key Features

### Dashboard

The dashboard provides a high-level overview of the store's activity and performance.

It is designed to answer questions such as:

- How is the store performing?
- What is happening with current orders?
- Which products require attention?
- What are the most important inventory signals?

---

### Product Management

Products can be managed through the application and Django administration interface.

Product information includes data such as:

- Product name
- SKU
- Description
- Category
- Price
- Stock quantity
- Product status

---

### Order Management

The application provides an order management layer for tracking customer orders.

The backend exposes dedicated REST endpoints for orders and order-related data.

---

### Inventory Monitoring

Inventory information is integrated into the product and dashboard experience.

This provides the foundation for future features such as:

- Low-stock alerts
- Out-of-stock detection
- Inventory trends
- Stock forecasting
- Reorder recommendations

---

### Authentication

The application uses Django REST Framework authentication.

Users can securely authenticate and access protected application resources.

The backend API uses token authentication and protected endpoints by default.

---

### Django Administration

A full Django Admin interface is available for administrative operations.

The production Django Admin is available at:

`/admin/`

This provides an additional management interface for administrators and developers.

---

## Technology Stack

### Frontend

- **React 19**
- **TypeScript**
- **Vite 8**
- Modern component-based architecture

### Backend

- **Django 6.1**
- **Django REST Framework 3.18**
- Python
- Token authentication
- Django ORM

### Database

- **PostgreSQL**
- **Neon PostgreSQL** in production

Neon provides the production PostgreSQL database used by the application.

### Deployment

- **Vercel**
- GitHub
- GitHub Actions
- Neon PostgreSQL

---

## Architecture

The application follows a full-stack architecture:

```text
                    ┌───────────────────────┐
                    │       User            │
                    │   Web Browser         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │       Vercel          │
                    │                       │
                    │  React + Vite         │
                    │  Django REST API      │
                    └───────────┬───────────┘
                                │
                         REST / JSON API
                                │
                                ▼
                    ┌───────────────────────┐
                    │        Django         │
                    │     REST Framework    │
                    │                       │
                    │ Dashboard             │
                    │ Products              │
                    │ Orders                │
                    │ Authentication        │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │     Neon PostgreSQL   │
                    │                       │
                    │ Production Database   │
                    └───────────────────────┘
```

The production application uses a pooled Neon connection for runtime database access, while database administration and migrations are handled separately through controlled CI workflows.

---

## Project Structure

```text
Ecommerce-Copilot/
│
├── backend/
│   ├── manage.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   └── api/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── permissions.py
│       ├── urls.py
│       ├── admin.py
│       ├── tests.py
│       ├── migrations/
│       └── management/
│           └── commands/
│               └── seed_demo.py
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── ...
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
│
├── .github/
│   └── workflows/
│       ├── django-migration-plan.yml
│       ├── django-migrate.yml
│       └── django-create-superuser.yml
│
├── .gitignore
└── README.md
```

---

## API

The Django REST API currently exposes endpoints for:

```text
POST   /api/token/
POST   /api/logout/

GET    /api/dashboard/

GET    /api/products/
GET    /api/orders/
```

Additional API functionality can be added as the application evolves.

Protected API resources require authentication.

---

## Authentication

Authentication is handled through Django REST Framework token authentication.

The API is configured with protected endpoints by default:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

This ensures that application data is not exposed through unauthenticated API requests.

---

## Database

Production data is stored in **PostgreSQL on Neon**.

The production database is:

```text
ecommerce-copilot
```

The application uses PostgreSQL in production and does not fall back to SQLite when production configuration is enabled.

The project deliberately keeps the local SQLite database separate from the production database.

### Important

The local database:

```text
backend/db.sqlite3
```

is for local development only.

It must **never** be used as the source of production data.

---

## Database Migrations

Database migrations are handled through GitHub Actions rather than through the deployed Vercel application.

Two workflows are available:

### Migration Plan

```text
Django Migration Plan
```

This workflow inspects pending migrations without applying them.

### Apply Migrations

```text
Django Apply Migrations
```

This workflow:

1. Connects to the Neon production database.
2. Validates the database name.
3. Validates the PostgreSQL database user.
4. Displays the migration plan.
5. Applies pending Django migrations.
6. Verifies the migration state.

The production schema has been successfully initialized and the Django migrations are currently applied.

---

## Production Administrator

A dedicated GitHub Actions workflow is available for creating the production Django administrator:

```text
Django Create Neon Superuser
```

The workflow is manually triggered and uses GitHub repository secrets for the administrator credentials.

The workflow:

1. Connects to Neon.
2. Validates the target PostgreSQL database.
3. Checks whether the username already exists.
4. Checks whether the email already exists.
5. Creates the Django superuser.
6. Never prints the administrator password.

Administrator credentials are never hard-coded in the repository.

---

## Environment Variables

### Backend

Typical backend environment variables include:

```text
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=<allowed-hosts>
DJANGO_CSRF_TRUSTED_ORIGINS=<trusted-origins>

DATABASE_URL=<pooled-neon-database-url>
DATABASE_URL_UNPOOLED=<direct-neon-database-url>
```

### Frontend

The frontend uses:

```text
VITE_API_URL=/api
```

Environment files containing secrets must never be committed to Git.

---

## Local Development

### Backend

Create and activate a Python virtual environment, then install the backend dependencies:

```bash
cd backend

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Configure the required environment variables before starting Django.

Run the development server:

```bash
python manage.py runserver
```

### Frontend

Install the frontend dependencies:

```bash
cd frontend

npm install
```

Start the Vite development server:

```bash
npm run dev
```

---

## Demo Data

The project includes a Django management command for generating demonstration data:

```text
backend/api/management/commands/seed_demo.py
```

This is intended for development and testing environments.

Demo data can be used to simulate:

- Products
- Inventory levels
- Orders
- Sales activity

This makes it possible to demonstrate the dashboard without using real commercial data.

> Production demo data should only be generated deliberately and against the intended database.

---

## Deployment

The application is deployed on Vercel with Neon PostgreSQL as the production database.

### Production

```text
Frontend + API:
https://ecommerce-copilot-flax.vercel.app

Django Admin:
/admin/

API:
/api/
```

The production environment uses:

```text
React + Vite
        │
        ▼
     Vercel
        │
        ├── Frontend
        │
        └── Django API
                │
                ▼
          Neon PostgreSQL
```

---

## CI/CD

GitHub Actions is used for controlled production database operations.

Current workflows include:

```text
.github/workflows/
│
├── django-migration-plan.yml
├── django-migrate.yml
└── django-create-superuser.yml
```

These workflows are intentionally **manual (`workflow_dispatch`)** for sensitive database operations.

This prevents an ordinary Git push from automatically modifying the production database.

---

## Security Principles

The project follows several important security principles:

- Production secrets are stored in Vercel and GitHub Secrets.
- Secrets are never hard-coded into the source code.
- Administrator passwords are never printed in CI logs.
- Production API endpoints require authentication.
- PostgreSQL is mandatory in production.
- The local SQLite database is not deployed.
- Database migrations are executed through controlled workflows.
- The Neon direct database URL is not used as the normal runtime connection.
- Sensitive environment variables must never use `VITE_*` names.

---

## Current MVP Scope

The current MVP focuses on the core e-commerce management foundation:

```text
Authentication
       │
       ▼
Dashboard
       │
       ├── Products
       │
       ├── Inventory
       │
       └── Orders
```

The project is intentionally being developed incrementally.

The goal is to establish a reliable data and application foundation before adding more advanced AI functionality.

---

## Roadmap

### Phase 1 — Core Platform

- [x] React frontend
- [x] Django backend
- [x] REST API
- [x] PostgreSQL / Neon
- [x] Authentication
- [x] Dashboard
- [x] Product management
- [x] Order management
- [x] Django Admin
- [x] Production deployment
- [x] Production database migrations
- [x] Production administrator
- [x] CI workflows

### Phase 2 — E-commerce Intelligence

- [ ] Sales analytics
- [ ] Product performance analysis
- [ ] Inventory alerts
- [ ] Low-stock detection
- [ ] Best-selling product analysis
- [ ] Revenue trends
- [ ] Customer/order insights

### Phase 3 — AI Copilot

- [ ] AI-generated business insights
- [ ] Natural-language questions about store data
- [ ] Product recommendations
- [ ] Inventory recommendations
- [ ] Sales anomaly detection
- [ ] Automated business summaries
- [ ] Conversational e-commerce assistant

### Phase 4 — Integrations

Potential future integrations include:

- Shopify
- WooCommerce
- YouCan
- CSV / Excel imports
- E-commerce marketplaces
- Social commerce platforms

---

## Product Vision

The ultimate goal of Ecommerce Copilot is not simply to display e-commerce data.

It is to help merchants **understand their business and take action**.

Instead of asking:

> "What happened?"

the future Ecommerce Copilot should help answer:

> "What happened, why did it happen, and what should I do next?"

This is the foundation for transforming the application into an **AI-powered e-commerce business intelligence platform**.

---

## Screenshots

Screenshots and product demonstrations can be added here as the UI evolves.

Recommended sections:

- Dashboard
- Products
- Orders
- Inventory
- AI Insights
- Django Admin

---

## Development Philosophy

The project follows a pragmatic MVP approach:

1. Build the core functionality.
2. Keep the architecture simple.
3. Validate the production infrastructure early.
4. Use real PostgreSQL infrastructure.
5. Protect production data.
6. Add AI capabilities progressively.
7. Prioritize useful business outcomes over unnecessary complexity.

---

## License

This project is currently maintained as a private/proprietary project.

License information will be added when the distribution model is finalized.

---

## Author

**Mourad Bennamane**

Full Stack Developer · Web Designer · Trainer

E-commerce · Software Engineering · AI · Digital Transformation

---

**Ecommerce Copilot**

*Turn your data into decisions.*
