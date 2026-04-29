# Quick Reference Guide

## Files to Know

| File | Purpose | Location |
|------|---------|----------|
| `.env` | Your configuration | `dcwms_django/.env` |
| `ENV_SETUP.md` | Setup instructions | `dcwms_django/ENV_SETUP.md` |
| `DARAJA_SETUP.md` | Daraja API guide | `dcwms_django/DARAJA_SETUP.md` |
| `ISSUES_RESOLVED.md` | Issues fixed | `dcwms_django/ISSUES_RESOLVED.md` |
| `IMPLEMENTATION_SUMMARY.md` | Technical details | `dcwms_django/IMPLEMENTATION_SUMMARY.md` |

## Quick Commands

### Start Server
```bash
cd dcwms_django
python manage.py runserver
```

### Run Checks
```bash
python manage.py check
```

### Create Admin User
```bash
python manage.py createsuperuser
```

### Apply Migrations
```bash
python manage.py migrate
```

## Key Endpoints

- **Application Home:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin
- **Bookings:** http://localhost:8000/bookings/
- **Payments:** http://localhost:8000/payments/
- **Receipts:** http://localhost:8000/receipts/

## Configuration

### Sandbox (Testing)
```env
MPESA_BASE_URL=https://sandbox.safaricom.co.ke
MPESA_CALLBACK_URL=http://127.0.0.1:8000/payments/mpesa/callback/
```

### Production
```env
MPESA_BASE_URL=https://api.safaricom.co.ke
MPESA_CALLBACK_URL=https://yourdomain.com/payments/mpesa/callback/
DEBUG=False
```

## What Happens When You...

### Create a Booking
1. Farmer creates booking
2. System sets status: `pending_payment`
3. Redirects to payment page
4. Awaits payment

### Complete Payment
1. Farmer enters MPesa number
2. System sends STK push
3. Farmer pays via MPesa
4. Callback received
5. Booking auto-confirmed
6. Inventory created
7. Receipt generated
8. User sees receipt options

### Schedule Withdrawal
1. Farmer schedules withdrawal
2. Status: `scheduled`
3. No operator approval needed

### Complete Withdrawal
1. Farmer/Operator completes withdrawal
2. Inventory updated
3. Capacity restored
4. Receipt generated
5. Status: `completed`

## Troubleshooting Quick Fixes

**Issue: "ModuleNotFoundError: requests"**
```bash
pip install requests
```

**Issue: Settings not loading**
```bash
pip install python-dotenv
```

**Issue: Database error**
```bash
python manage.py migrate
```

**Issue: Static files not found**
```bash
python manage.py collectstatic
```

## Important Notes

- ✅ All errors have been fixed
- ✅ System auto-approves bookings upon payment
- ✅ Receipts generate automatically
- ✅ Configuration ready in `.env`
- ⏳ Awaiting Daraja API credentials

## Getting Daraja Credentials

1. Go to: https://developer.safaricom.co.ke/
2. Sign up / Login
3. Create new app
4. Copy credentials:
   - Consumer Key
   - Consumer Secret
   - Shortcode
   - Passkey
5. Update `.env` file

## File Structure
```
dcwms_django/
├── .env                    ← Your configuration
├── .env.example           ← Template
├── ENV_SETUP.md           ← Setup guide
├── DARAJA_SETUP.md        ← API guide
├── ISSUES_RESOLVED.md     ← What's fixed
├── IMPLEMENTATION_SUMMARY.md
├── payments/
│   ├── views.py          ← Fixed UnboundLocalError
│   ├── models.py
│   └── urls.py
├── templates/
│   ├── payments/
│   │   ├── initiate.html ← Fixed booking details
│   │   └── status.html   ← Added receipt links
│   └── ...
└── withdrawals/
    └── views.py         ← Added receipt generation
```

## Next Action Items

- [ ] Get Daraja credentials
- [ ] Update .env file
- [ ] Test payment flow
- [ ] Deploy to production

---

**Status:** Ready for MPesa integration  
**Server:** Running at http://localhost:8000
