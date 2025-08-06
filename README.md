# 📊 Cap Table Management System

A comprehensive full-stack enterprise application for managing corporate capitalization tables and share issuances. This project demonstrates advanced software engineering practices, clean architecture principles, and AI-assisted development workflows.

---

## 🚀 Executive Summary

The **Cap Table Management System** is a production-ready web application that digitizes and streamlines equity management for corporations. Built with modern Python technologies and following clean architecture principles, it provides secure role-based access for administrators and shareholders to manage equity distributions, generate legal certificates, and maintain comprehensive audit trails.

### 🔑 Key Business Value

- **Automated Equity Management**: Streamlines share issuance workflows  
- **Compliance Ready**: Generates legally compliant share certificates  
- **Audit Trail**: Complete tracking of all equity transactions  
- **Role-Based Security**: Granular access control for different user types  
- **Scalable Architecture**: Built to handle enterprise-level requirements  

---

## 🎯 Business Context & Domain

### What is a Cap Table?

A **capitalization table** (cap table) details the equity ownership structure of a company. It tracks:

- **Shareholders**: Individuals or entities holding shares  
- **Share Classes**: Common, preferred, etc.  
- **Ownership Percentages**: Distribution of company ownership  
- **Issuance History**: When/how shares were distributed  
- **Valuations**: Share prices and company valuation over time  

### 🧩 Problem Statement

Traditional cap table management using spreadsheets leads to:

- Human errors  
- Version control issues  
- Compliance risks  
- Limited shareholder access  
- Audit challenges  

### ✅ Solution Approach

This system:

- Centralizes data  
- Automates workflows  
- Ensures compliance  
- Provides transparency  
- Maintains secure role-based access  

---

## 🏗️ Technical Architecture

### Clean Architecture Layers

🌐 Presentation Layer (FastAPI, Middleware, Exception Handlers)
│
💼 Business Logic Layer (Services, Validation, PDF Generation)
│
💾 Data Access Layer (Repositories, SQLAlchemy, DB Connection)

markdown
Copier
Modifier

### Core Design Principles

- ✅ **Single Responsibility**  
- ✅ **Open/Closed**  
- ✅ **Liskov Substitution**  
- ✅ **Interface Segregation**  
- ✅ **Dependency Inversion**

### Architecture Benefits

- 🔄 Framework Independent  
- 🧪 Easily Testable  
- 🗄️ Database Agnostic  
- 🔧 Highly Maintainable  

---

## 🛠️ Technology Stack

### 🧩 Backend

| Component         | Technology             | Purpose                                  |
|------------------|------------------------|------------------------------------------|
| Framework         | FastAPI 0.104+         | High-performance async API framework     |
| Database          | PostgreSQL 15+         | ACID-compliant relational DB             |
| ORM               | SQLAlchemy 2.0+        | Async ORM with type safety               |
| Validation        | Pydantic V2            | Schema validation & serialization        |
| Auth              | JWT + OAuth2           | Secure token-based authentication        |
| Password Hashing  | Passlib + bcrypt       | Secure password storage                  |
| PDF Generation    | ReportLab              | Professional certificate generation      |
| Testing           | Pytest + pytest-asyncio| Unit & integration testing               |
| Server            | Uvicorn                | ASGI server for FastAPI                  |

### 🤖 AI Development Tools

- Claude Sonnet 4 AI – primary coding assistant  
- Claude 3.5 Sonnet – architecture support  
- Git – version control  
- pip – dependency management  

---

## 📁 Project Structure

```bash
cap-table-management/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .gitignore
├── app/
│ ├── auth/ # JWT Auth
│ ├── models/ # SQLAlchemy models
│ ├── repositories/ # Database operations
│ ├── services/ # Business logic
│ ├── api/ # API endpoints
│ ├── schemas/ # Pydantic schemas
│ ├── config.py # Configuration
│ ├── database.py # Database setup
│ └── main.py # App entrypoint
├── requirements.txt
└── tests/
```
## ✅ Feature Implementation Status 

### 🔐 Authentication & Authorization
- ✅ JWT-based login  
- ✅ Role-based access control  
- ✅ Password hashing  
- ✅ Token refresh  
- ✅ Secure session management  

### 👑 Admin Capabilities
- ✅ Shareholder CRUD  
- ✅ Share issuance workflows  
- ✅ PDF certificate generation  
- ✅ Dashboard analytics  
- ✅ Audit trail access  

### 👤 Shareholder Features
- ✅ Dashboard with personal holdings  
- ✅ Issuance history  
- ✅ Certificate downloads  
- ✅ Secure data access  

### 🎯 Advanced Features
- ✅ Audit logging  
- ✅ Business rule validation  
- ✅ Console email simulation  
- ✅ Health monitoring  
- ✅ Centralized error handling  

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+  
- PostgreSQL 14+  
- Git  

### 2. Setup Project

```bash
git clone https://github.com/Perrin-Nj/cap-table-management.git
cd cap-table-management

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure Database

```bash
createdb cap_table_db
cp .env.example .env
nano .env  # or open it in your editor
```

Edit the `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/cap_table_db
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
LOG_LEVEL=INFO
```

### 4. Run App

```bash
uvicorn app.main:app --reload
```

### 5. Test App

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "database": "connected"}
```

Open in your browser:
http://localhost:8000/docs

---

## 🔐 Default User Credentials

### 👑 Admin  
**Email:** admin@captable.com  
**Password:** admin123

### 👤 Shareholder  
**Email:** shareholder@example.com  
**Password:** shareholder123

---

## 📡 API Overview

### 🔐 Authentication

```http
POST /api/token/
Content-Type: application/x-www-form-urlencoded

username=admin@captable.com&password=admin123
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 👑 Admin Endpoints

- `GET /api/shareholders/` — List all shareholders  
- `POST /api/shareholders/` — Create a new shareholder  
- `GET /api/shareholders/{shareholder_id}` — Get shareholder details  
- `GET /api/shareholders/user/{user_id}` — Get shareholder by user ID  
- `POST /api/issuances/` — Issue new shares  
- `GET /api/issuances/` — View all share issuances (admin view)  
- `GET /api/issuances/{issuance_id}` — Get specific issuance details  

---

## 👤 Shareholder Endpoints

- `GET /api/issuances/` — View personal issuance history  
- `GET /api/issuances/{issuance_id}` — View specific personal issuance details  
- `GET /api/issuances/{issuance_id}/certificate` — Download personal share certificate  
- `GET /api/issuances/{issuance_id}/preview` — Preview personal share certificate  
- `GET /api/shareholders/{shareholder_id}` — View own shareholder profile  
- `GET /api/shareholders/user/{user_id}` — View own shareholder profile by user ID  


### 🛠️ System

- `GET /health` — Health check

**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
**ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤖 AI-Assisted Development Workflow

This project leverages AI tooling to accelerate and improve software quality:

- **Cursor AI** – For AI pair programming and code generation  
- **GitHub Copilot** – For intelligent autocompletion  
- **Claude 3.5** – For architectural design assistance  
- **OpenAI ChatGPT** – For documentation and code reviews

---

## 💡 License & Contributions

This project is open-source and available for contributions, learning, and forking.  
Feel free to open issues or submit pull requests to improve the project!