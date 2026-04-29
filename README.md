# DCWMS - Digital Cereal Warehouse Management System

## Overview
A full-featured Django web application that allows smallholder farmers in Kenya to find certified warehouses, book storage space, receive digital receipts, and manage grain withdrawals — while giving warehouse operators tools to manage inventory and logistics.

---

## System Modules
1. **User Management** – Farmer / Operator / Admin roles with RBAC
2. **Warehouse Management** – Create and manage certified warehouse profiles
3. **Warehouse Finder** – Search by county, sub-county, capacity, storage type
4. **Booking System** – Real-time capacity validation and booking workflow
5. **Digital Receipt System** – Auto-generated secure e-WRS receipts
6. **Inventory Management** – Auto-tracked grain inventory with movement logs
7. **Withdrawal Scheduling** – Farmers schedule, operators approve & complete
8. **Operator Dashboard** – Manage bookings, inventory, and warehouse stats
9. **Reporting Module** – Utilization, cereal breakdown, booking analytics

---

## Quick Start (Local Development)

### 1. Clone and set up environment
```bash
git clone <repo_url>
cd dcwms
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=dcwms_db
DB_USER=dcwms_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 3. Set up PostgreSQL database
```sql
CREATE DATABASE dcwms_db;
CREATE USER dcwms_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dcwms_db TO dcwms_user;
```

> **Alternative for development**: Switch to SQLite in settings.py by uncommenting the SQLite DATABASES block.

### 4. Run migrations and create superuser
```bash
python manage.py makemigrations accounts warehouses bookings receipts inventory withdrawals reports
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run development server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## User Roles & Workflows

### Farmer Workflow
1. Register at `/accounts/register/farmer/`
2. Search warehouses at `/warehouses/`
3. Click **Book Storage** on any warehouse
4. Fill booking form (cereal type, bags, dates)
5. Wait for operator approval
6. Once approved → digital receipt auto-generated
7. View receipt at `/receipts/`
8. Schedule withdrawal from `/inventory/`

### Operator Workflow
1. Register at `/accounts/register/operator/`
2. Create warehouse profile at `/warehouses/create/`
3. Review pending bookings at `/bookings/?status=pending`
4. Approve → inventory auto-created, capacity auto-reduced
5. Approve/complete withdrawal requests at `/withdrawals/`
6. Monitor utilization at `/reports/`

### Admin
- Access Django admin at `/admin/`
- View all system data

---

## Project Structure
```
dcwms/
├── dcwms/              # Project settings, URLs
├── accounts/           # Users, auth, roles, dashboard
├── warehouses/         # Warehouse profiles, finder
├── bookings/           # Booking requests, approval
├── receipts/           # Digital receipt generation
├── inventory/          # Grain inventory tracking
├── withdrawals/        # Withdrawal scheduling
├── reports/            # Analytics and reporting
├── templates/          # All HTML templates
├── static/             # CSS, JS, images
├── requirements.txt
└── manage.py
```

---

## Deployment (Render / Railway / Heroku)

### Environment variables needed in production:
```
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DATABASE_URL=postgres://...
```

### Static files (add to settings.py for production):
```python
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add after SecurityMiddleware
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Deploy steps:
```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn dcwms.wsgi:application --bind 0.0.0.0:$PORT
```

### Procfile (for Heroku/Railway):
```
web: gunicorn dcwms.wsgi:application
release: python manage.py migrate
```

---

## Receipt Verification
Anyone can verify a receipt publicly at:
`/receipts/verify/?code=RC-XXXXXXXX`

No login required — this allows banks, cooperatives, and traders to confirm grain ownership.

---

## Security Features
- Django CSRF protection on all forms
- Password hashing (Django default PBKDF2)
- Role-based access control (farmers can't access operator views)
- Session-based authentication
- SHA-256 receipt security hash
- Input validation on all forms (client + server-side)

---

## Data Integrity
- Warehouse capacity automatically reduced on booking approval
- Capacity automatically restored on withdrawal completion
- Inventory records created automatically on booking approval
- Movement logs track all inbound/outbound grain
- All operations wrapped in `transaction.atomic()` to prevent partial updates

---

## Author
Augustine Moses Musangi Mwai  
ADM: J77-1568-2022  
Machakos University – BSc Information Technology  
Supervisor: Madam Veronica Mutua  
February 2026
