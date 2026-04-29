"""
MPesa Integration Service
"""
import base64
import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import Payment

# Set up logger for this module
logger = logging.getLogger(__name__)


class MPesaService:
    """MPesa payment integration service."""

    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.base_url = getattr(settings, 'MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')

    def get_access_token(self):
        """Get MPesa access token."""
        try:
            credentials = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials", headers=headers)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            raise Exception(f"Failed to get access token: {str(e)}")

    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push for payment."""
        try:
            access_token = self.get_access_token()

            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": getattr(settings, 'MPESA_CALLBACK_URL', ''),
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(f"{self.base_url}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise Exception(f"Failed to initiate STK push: {str(e)}")

    def query_payment_status(self, checkout_request_id):
        """Query MPesa to check payment status from response body."""
        try:
            access_token = self.get_access_token()
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers=headers,
                timeout=10
            )

            # IMPORTANT: M-Pesa returns HTTP 200 for ALL responses
            # The actual status is ALWAYS in the response body, NEVER in HTTP status code
            response_data = response.json() if response.text else {}
            
            # Add comprehensive logging for debugging
            logger.debug(f"M-Pesa Query Response: {json.dumps(response_data, indent=2)}")
            
            # The response MUST contain ResultCode - if not, something is wrong
            if 'ResultCode' not in response_data:
                # Try alternative response structures that might exist
                if 'result' in response_data and isinstance(response_data['result'], dict):
                    # Nested structure - ResultCode might be in 'result'
                    result_code = response_data['result'].get('ResultCode')
                    if result_code is not None:
                        response_data['ResultCode'] = result_code
                
                # If still no ResultCode, check for status field
                if 'ResultCode' not in response_data and 'status' in response_data:
                    status = response_data['status']
                    # Map status to ResultCode if needed
                    if status == 'success' or status == 0:
                        response_data['ResultCode'] = 0
                    elif status == 'pending' or status == 1:
                        response_data['ResultCode'] = 1
            
            # If we still don't have ResultCode and HTTP status is not 200, it's an error
            if 'ResultCode' not in response_data:
                if response.status_code != 200:
                    raise Exception(f"M-Pesa Error: HTTP {response.status_code} - {response.text or 'No response body'}")
                else:
                    # Even with 200 status, if no ResultCode, log for debugging
                    logger.warning(f"M-Pesa returned 200 but no ResultCode in body: {response_data}")
                    response_data['ResultCode'] = 2  # Default to error
            
            return response_data

        except requests.exceptions.Timeout:
            raise Exception("M-Pesa query timed out (10s)")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error querying M-Pesa: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error querying payment status: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from M-Pesa: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to query payment status: {str(e)}")

    def process_callback(self, callback_data):
        """Process MPesa callback."""
        try:
            # Extract callback data
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            result_desc = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')

            if result_code == 0:
                # Payment successful
                callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])

                # Extract payment details
                receipt_number = None
                transaction_id = None
                phone_number = None

                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        receipt_number = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        transaction_id = item.get('Value')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_number = str(item.get('Value'))

                # Find and update payment
                checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
                payment = Payment.objects.filter(mpesa_transaction_id=checkout_request_id).first()

                if payment:
                    payment.mark_completed(receipt_number, transaction_id)
                    if phone_number:
                        payment.mpesa_phone_number = phone_number
                    payment.callback_data = callback_data
                    payment.save()

                return True
            else:
                # Payment failed
                checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
                payment = Payment.objects.filter(mpesa_transaction_id=checkout_request_id).first()

                if payment:
                    payment.status = Payment.STATUS_FAILED
                    payment.error_message = result_desc
                    payment.callback_data = callback_data
                    payment.save()

                return False

        except Exception as e:
            # Log error
            return False