# ERP Web Accounting System

نظام محاسبي إلكتروني متكامل مبني بمعمارية 3 طبقات.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy Async + PostgreSQL
- **Gateway:** Express.js + TypeScript
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Infrastructure:** Docker Compose

## Quick Start

```bash
cd web
docker-compose up --build
```

- Frontend: http://localhost:5173
- Gateway: http://localhost:3001
- Backend API: http://localhost:8001/docs
- Database: localhost:5432

## Modules

- Authentication & User Management
- Sales & Purchases
- Inventory Management
- Accounting (Chart of Accounts, Journal Entries, Trial Balance)
- HR (Employees, Attendance, Leaves, Payroll)
- Payments & Banking
- Projects
- CRM (Customers, Suppliers, Leads)
- Reports & Dashboard
