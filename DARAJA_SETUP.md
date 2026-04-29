# MPesa/Daraja Integration Guide

## Getting Started with Daraja API

### Step 1: Register on Daraja Portal

1. Visit: **https://developer.safaricom.co.ke/**
2. Click "Sign Up"
3. Create account with:
   - Email
   - Full Name
   - Organization (if applicable)
   - Password

### Step 2: Create Your First App

1. Login to dashboard
2. Navigate to "My Apps" or "Applications"
3. Click "Create New App"
4. Fill in:
   - **App Name:** `DCWMS Development`
   - **Description:** Digital Cereal Warehouse Management System
   - **Type:** Select appropriate category
5. Click "Create"

### Step 3: Get Your Credentials

After creating the app, you'll see:

```
Consumer Key:     xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Consumer Secret:  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Important:** Copy these credentials immediately and save them securely.

### Step 4: Get Your Business Shortcode

You'll need:
- **Shortcode:** Your business till number (provided by Safaricom)
- **Passkey:** Security key for signing requests (also provided)

### Step 5: Update .env File

Open `dcwms_django/.env` and update:

```env
# MPesa Configuration
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_SHORTCODE=your_shortcode_here
MPESA_PASSKEY=your_passkey_here
MPESA_BASE_URL=https://sandbox.safaricom.co.ke
MPESA_CALLBACK_URL=http://127.0.0.1:8000/payments/mpesa/callback/
```

### Step 6: Testing the Integration

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Access the application:**
   - Go to: http://localhost:8000
   - Login as a farmer

3. **Create a test booking:**
   - Go to Warehouses → Find a warehouse → Create booking
   - Fill in booking details
   - Click "Create Booking"

4. **Process payment:**
   - You'll be redirected to payment page
   - Enter your test phone number starting with 254
   - Click "Pay with MPesa"
   - You should receive an STK push on your phone

5. **Complete payment:**
   - Enter your MPesa PIN on your phone
   - Payment will be verified
   - Booking will auto-confirm
   - Receipt will be generated

### Step 7: Verify Callback

To ensure callbacks are working:

1. Check application logs for callback receipt
2. Verify booking status changed to "confirmed"
3. Check if inventory record was created
4. Verify receipt was generated

## Sandbox vs Production

### Sandbox (Development)
```env
MPESA_BASE_URL=https://sandbox.safaricom.co.ke
MPESA_CALLBACK_URL=http://127.0.0.1:8000/payments/mpesa/callback/
```
- Test payments
- Test phone numbers start with 254712345678
- No real money involved

### Production
```env
MPESA_BASE_URL=https://api.safaricom.co.ke
MPESA_CALLBACK_URL=https://yourdomain.com/payments/mpesa/callback/
```
- Real payments
- Real phone numbers
- Real money involved
- Set DEBUG=False

## Troubleshooting

### Issue: "Invalid Consumer Key"
**Solution:** 
- Verify you copied the key correctly
- Check for extra spaces
- Ensure keys match your app

### Issue: "Network Connection Error"
**Solution:**
- Check internet connection
- Verify base URL is correct for environment
- Check firewall settings

### Issue: "Callback not received"
**Solution:**
- Ensure callback URL is publicly accessible
- Check firewall allows incoming requests
- Verify URL matches in settings
- Check application logs

### Issue: "Invalid Shortcode"
**Solution:**
- Verify shortcode format (should be numeric)
- Confirm it matches your registered business code
- Check with Safaricom support

## Test Phone Numbers (Sandbox Only)

For testing in sandbox environment:
```
254712345678  - Valid MPesa number
254712345679  - Another test number
```

Note: These are sandbox test numbers and won't work in production.

## API Response Examples

### Successful STK Push
```json
{
    "ResponseCode": "0",
    "ResponseDescription": "Success. Request accepted for processing",
    "CheckoutRequestID": "ws_CO_12345678"
}
```

### Successful Callback
```json
{
    "Body": {
        "stkCallback": {
            "MerchantRequestID": "123456",
            "CheckoutRequestID": "ws_CO_12345678",
            "ResultCode": 0,
            "ResultDesc": "The service request has been processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    {
                        "Name": "Amount",
                        "Value": 1000
                    },
                    {
                        "Name": "MpesaReceiptNumber",
                        "Value": "LHXYZ1234567"
                    },
                    {
                        "Name": "TransactionDate",
                        "Value": "20240424131500"
                    },
                    {
                        "Name": "PhoneNumber",
                        "Value": 254712345678
                    }
                ]
            }
        }
    }
}
```

## Security Checklist

- [ ] Consumer Key and Secret stored in `.env`
- [ ] `.env` file added to `.gitignore`
- [ ] Callback URL is HTTPS in production
- [ ] Passkey stored securely
- [ ] DEBUG=False in production
- [ ] SECRET_KEY changed to secure value
- [ ] Database password changed
- [ ] API errors don't expose sensitive info

## Support Resources

- **Daraja Documentation:** https://developer.safaricom.co.ke/docs
- **API Reference:** https://developer.safaricom.co.ke/api/index
- **Community Forum:** https://developer.safaricom.co.ke/community

## Next Steps After Setup

1. ✅ Get Daraja credentials
2. ✅ Update .env file
3. ✅ Test with sandbox environment
4. ✅ Verify callbacks work
5. ✅ Test complete booking flow
6. ✅ Move to production (when ready)

---

**For Production Deployment:**
1. Update all credentials for production
2. Change DEBUG to False
3. Set up HTTPS
4. Update ALLOWED_HOSTS
5. Configure email backend
6. Setup PostgreSQL database
7. Enable SSL/TLS for all communications

---

**Status:** Ready for Daraja integration
**Last Updated:** April 24, 2026
