# DCWMS Environment Configuration

## Setup Instructions

### 1. Create Your Local .env File

Copy the `.env.example` file to create your own `.env` file:

```bash
cp .env.example .env
```

### 2. Configure Django Settings

Update the following in your `.env`:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
```

### 3. Configure MPesa/Daraja Integration

To enable MPesa payment processing:

1. **Register at Daraja (Safaricom Developer Portal)**
   - Visit: https://developer.safaricom.co.ke/
   - Create an account and log in
   - Create a new app

2. **Get Your Credentials**
   - Consumer Key
   - Consumer Secret
   - Shortcode (your business till number)
   - Passkey (provided in the portal)

3. **Update .env File**

```env
MPESA_CONSUMER_KEY=your_consumer_key_from_daraja
MPESA_CONSUMER_SECRET=your_consumer_secret_from_daraja
MPESA_SHORTCODE=123456
MPESA_PASSKEY=your_mpesa_passkey
MPESA_BASE_URL=https://sandbox.safaricom.co.ke  # for testing
MPESA_CALLBACK_URL=http://yourdomain.com/payments/mpesa/callback/
```

### 4. Testing MPesa Locally

For local development, use:
```env
MPESA_BASE_URL=https://sandbox.safaricom.co.ke
MPESA_CALLBACK_URL=http://127.0.0.1:8000/payments/mpesa/callback/
```

### 5. Configure Email (Optional)

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # for development
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

### 6. Database Configuration (PostgreSQL for Production)

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dcwms_db
DB_USER=dcwms_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

### 7. Install Dependencies

```bash
pip install -r requirements.txt
```

### 8. Run Migrations

```bash
python manage.py migrate
```

### 9. Create Superuser

```bash
python manage.py createsuperuser
```

### 10. Start Development Server

```bash
python manage.py runserver
```

Access the application at: http://localhost:8000

## Features Implemented

### 1. ✅ Payment Integration
- MPesa payment gateway integration
- Automatic booking confirmation upon payment
- Digital receipt generation
- Payment history tracking

### 2. ✅ Booking Flow
- Farmers create bookings → Payment required
- Payment triggers automatic approval
- Inventory record created automatically
- Receipt generated instantly

### 3. ✅ Withdrawal System
- Simple withdrawal scheduling (no approval needed)
- Automatic inventory updates
- Capacity restoration
- Completion receipt generated

### 4. ✅ Receipt System
- Auto-generated digital receipts
- Printable receipts
- Receipt download functionality
- Complete booking/withdrawal details

### 5. ✅ Admin Dashboard
- Automatic updates without manual intervention
- Real-time booking status tracking
- Payment verification displayed
- No operator approval required for bookings

## Security Notes

⚠️ **Important for Production:**

1. Change `SECRET_KEY` to a strong random value
2. Set `DEBUG=False`
3. Update `ALLOWED_HOSTS` with your domain
4. Use environment variables for all sensitive data
5. Enable HTTPS
6. Use a production database (PostgreSQL)
7. Set up proper email configuration

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| DEBUG | Enable debug mode | True/False |
| SECRET_KEY | Django secret key | `django-insecure-...` |
| ALLOWED_HOSTS | Allowed hosts | `localhost,127.0.0.1` |
| MPESA_CONSUMER_KEY | Daraja consumer key | `from dashboard` |
| MPESA_CONSUMER_SECRET | Daraja consumer secret | `from dashboard` |
| MPESA_SHORTCODE | Business shortcode | `123456` |
| MPESA_PASSKEY | MPesa passkey | `from dashboard` |
| MPESA_BASE_URL | Daraja base URL | `https://sandbox.safaricom.co.ke` |
| MPESA_CALLBACK_URL | Callback URL | `http://yourdomain.com/callback/` |

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'requests'"**
- Solution: `pip install requests`

**Issue: MPesa callback not working**
- Ensure `MPESA_CALLBACK_URL` is publicly accessible
- Check firewall/port settings
- Verify callback URL is registered in Daraja

**Issue: Payments not auto-approving**
- Check if MPesa credentials are correct
- Verify callback endpoint is reachable
- Check application logs for errors

## API Documentation

### Payment Flow

1. **Create Booking** → Status: `pending_payment`
2. **Initiate Payment** → Sends STK push to phone
3. **Complete Payment** → Booking auto-confirmed (Status: `confirmed`)
4. **Generate Receipt** → Automatic
5. **View Receipt** → Available in payment status page

### Withdrawal Flow

1. **Schedule Withdrawal** → Status: `scheduled`
2. **Complete Withdrawal** → Inventory updated, capacity restored
3. **Generate Receipt** → Automatic
4. **Download Receipt** → Available after completion

## Support

For issues or questions:
1. Check the application logs
2. Review the Django debug toolbar (development only)
3. Check the database for data consistency
4. Verify .env configuration

---

**Last Updated:** April 24, 2026
**Version:** 1.0.0
