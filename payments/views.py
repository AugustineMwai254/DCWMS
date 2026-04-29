from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
import json
import logging
from .models import Payment
from .forms import MPesaPaymentForm
from .mpesa import MPesaService
from bookings.models import Booking

# Set up logger for this module
logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, booking_id):
    """Initiate payment for a booking."""
    booking = get_object_or_404(Booking, id=booking_id, farmer=request.user)

    # Check if booking is eligible for payment
    if booking.status != 'pending_payment':
        messages.error(request, "This booking is not eligible for payment.")
        return redirect('bookings:detail', pk=booking_id)

    # Check if payment already exists and is not failed/cancelled
    existing_payment = Payment.objects.filter(booking=booking).exclude(status__in=['failed', 'cancelled']).first()
    if existing_payment:
        return redirect('payments:status', payment_id=existing_payment.payment_id)

    if request.method == 'POST':
        form = MPesaPaymentForm(request.POST)
        if form.is_valid():
            payment = None
            try:
                # Clean up any failed or cancelled payments for this booking
                Payment.objects.filter(booking=booking, status__in=['failed', 'cancelled']).delete()

                # Create payment record
                payment = Payment.objects.create(
                    booking=booking,
                    farmer=request.user,
                    amount_kes=booking.total_fee_kes,
                    payment_method='mpesa',
                    status='pending'
                )

                # Initiate MPesa STK push
                mpesa_service = MPesaService()
                phone_number = form.cleaned_data['phone_number']

                response = mpesa_service.initiate_stk_push(
                    phone_number=phone_number,
                    amount=booking.total_fee_kes,
                    account_reference=f"DCWMS-{booking.booking_ref_human}",
                    transaction_desc=f"Payment for warehouse booking {booking.booking_ref_human}"
                )

                # Update payment with transaction details
                payment.mpesa_transaction_id = response.get('CheckoutRequestID')
                payment.mpesa_phone_number = phone_number
                payment.status = 'processing'
                payment.save()

                messages.success(request, "Payment request sent to your phone. Please check your MPesa and complete the payment.")
                return redirect('payments:status', payment_id=payment.payment_id)

            except Exception as e:
                if payment:
                    payment.status = 'failed'
                    payment.error_message = str(e)
                    payment.save()
                messages.error(request, f"Failed to initiate payment: {str(e)}")
    else:
        form = MPesaPaymentForm()

    context = {
        'booking': booking,
        'form': form,
        'title': 'Complete Payment'
    }
    return render(request, 'payments/initiate.html', context)


@login_required
def payment_status(request, payment_id):
    """Check payment status and redirect to receipt if completed."""
    payment = get_object_or_404(Payment, payment_id=payment_id, farmer=request.user)

    # If payment is completed, redirect to receipt page with success message
    if payment.status == Payment.STATUS_COMPLETED:
        messages.success(request, f"✓ Payment successful! Tracking Code: {payment.tracking_code}")
        # Get the receipt for this booking - check if it exists first
        try:
            receipt = payment.booking.receipt
            return redirect('receipts:detail', pk=receipt.pk)
        except:
            # If receipt doesn't exist, try to create it
            try:
                payment._create_inventory_record()
                receipt = payment.booking.receipt
                return redirect('receipts:detail', pk=receipt.pk)
            except Exception as e:
                messages.warning(request, f"Payment completed but receipt generation had an issue: {str(e)}")

    context = {
        'payment': payment,
        'title': 'Payment Status'
    }
    return render(request, 'payments/status.html', context)


@login_required
@require_http_methods(["GET"])
def manual_check_payment(request, payment_id):
    """Manual view to check and update a specific payment status."""
    payment = get_object_or_404(Payment, payment_id=payment_id, farmer=request.user)
    
    context = {
        'payment': payment,
        'title': 'Check Payment Status'
    }
    
    if request.method == 'GET' and 'confirm' in request.GET:
        # User confirmed checking payment
        mpesa_service = MPesaService()
        
        if not payment.mpesa_transaction_id:
            messages.error(request, "No transaction ID found for this payment.")
            return redirect('payments:status', payment_id=payment_id)
        
        try:
            query_response = mpesa_service.query_payment_status(payment.mpesa_transaction_id)
            
            logger.info(f"Manual payment status check response: {query_response}")
            
            # Extract ResultCode from response body - MUST handle missing/None values
            result_code = query_response.get('ResultCode')
            
            if result_code is None:
                logger.error(f"No ResultCode in manual check response: {query_response}")
                messages.error(request, "Unable to determine payment status. Please try again.")
                return redirect('payments:status', payment_id=payment_id)
            
            # Convert to int
            try:
                result_code = int(result_code)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert ResultCode: {result_code}")
                messages.error(request, "Invalid status code received. Please contact support.")
                return redirect('payments:status', payment_id=payment_id)
            
            result_desc = query_response.get('ResultDesc', 'No description provided')
            
            logger.info(f"Payment {payment.payment_ref} ResultCode: {result_code} - {result_desc}")
            
            # ==================== STATUS CODE HANDLING ====================
            # ResultCode 0 = Success
            if result_code == 0:
                logger.info(f"Manual check: Payment {payment.payment_ref} confirmed - ResultCode 0")
                
                # Extract receipt number
                receipt_number = None
                if 'MpesaReceiptNumber' in query_response:
                    receipt_number = query_response.get('MpesaReceiptNumber')
                elif 'mpesaReceiptNumber' in query_response:
                    receipt_number = query_response.get('mpesaReceiptNumber')
                
                payment.mark_completed(receipt_number=receipt_number)
                messages.success(request, "✓ Payment confirmed and receipt generated!")
                
                try:
                    receipt = payment.booking.receipt
                    return redirect('receipts:detail', pk=receipt.pk)
                except:
                    messages.warning(request, "Payment confirmed but receipt is not yet available.")
                    return redirect('payments:status', payment_id=payment_id)
            
            # ResultCode 1 = Still processing
            elif result_code == 1:
                logger.info(f"Manual check: Payment {payment.payment_ref} still processing - ResultCode 1")
                messages.warning(request, "Payment is still being processed. Please try again in a few moments.")
                return redirect('payments:status', payment_id=payment_id)
            
            # Any other code = Failed
            else:
                logger.error(f"Manual check: Payment {payment.payment_ref} failed - ResultCode {result_code}: {result_desc}")
                payment.status = Payment.STATUS_FAILED
                payment.error_message = f"ResultCode {result_code}: {result_desc}"
                payment.save()
                messages.error(request, f"Payment failed: {result_desc}")
                return redirect('payments:status', payment_id=payment_id)
        
        except Exception as e:
            logger.exception(f"Error in manual payment check for {payment.payment_ref}")
            messages.error(request, f"Error checking payment: {str(e)}")
            return redirect('payments:status', payment_id=payment_id)
    
    return render(request, 'payments/manual_check.html', context)


@login_required
@require_http_methods(["POST"])
def check_payment_status(request, payment_id):
    """AJAX endpoint to check and update payment status from MPesa."""
    try:
        payment = get_object_or_404(Payment, payment_id=payment_id, farmer=request.user)
        
        # Only check if still processing
        if payment.status != Payment.STATUS_PROCESSING:
            receipt_id = None
            try:
                if payment.status == Payment.STATUS_COMPLETED and hasattr(payment.booking, 'receipt'):
                    receipt_id = payment.booking.receipt.id
            except:
                pass
            
            return JsonResponse({
                'status': payment.status,
                'is_completed': payment.status == Payment.STATUS_COMPLETED,
                'receipt_id': receipt_id
            })
        
        # Try to query payment status from MPesa
        if payment.mpesa_transaction_id:
            mpesa_service = MPesaService()
            try:
                query_response = mpesa_service.query_payment_status(payment.mpesa_transaction_id)
                
                logger.info(f"Payment status check response for {payment.payment_ref}: {query_response}")
                
                # Extract ResultCode - it MUST be in the response
                result_code = query_response.get('ResultCode')
                
                # Handle various data types for ResultCode
                if result_code is None:
                    logger.error(f"No ResultCode in response: {query_response}")
                    return JsonResponse({
                        'status': 'processing',
                        'is_completed': False,
                        'message': 'Checking payment status...',
                        'debug': 'No ResultCode in response'
                    })
                
                # Convert to int if it's a string
                try:
                    result_code = int(result_code)
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert ResultCode to int: {result_code}")
                    result_code = int(result_code or 2)  # Default to error
                
                result_desc = query_response.get('ResultDesc', 'No description provided')
                
                logger.info(f"Payment {payment.payment_ref} ResultCode: {result_code}")
                
                # ==================== STATUS CODE HANDLING ====================
                # ResultCode 0 = Success (payment confirmed)
                if result_code == 0:
                    logger.info(f"Payment {payment.payment_ref} confirmed - ResultCode 0")
                    
                    # Extract receipt number from response
                    receipt_number = None
                    if 'MpesaReceiptNumber' in query_response:
                        receipt_number = query_response.get('MpesaReceiptNumber')
                    elif 'mpesaReceiptNumber' in query_response:
                        receipt_number = query_response.get('mpesaReceiptNumber')
                    
                    # Mark payment as completed
                    payment.mark_completed(receipt_number=receipt_number)
                    
                    receipt_id = None
                    try:
                        receipt_id = payment.booking.receipt.id
                    except:
                        pass
                    
                    return JsonResponse({
                        'status': 'completed',
                        'is_completed': True,
                        'message': 'Payment confirmed! Receipt has been generated.',
                        'receipt_id': receipt_id,
                        'redirect_url': f'/receipts/{receipt_id}/' if receipt_id else '/bookings/'
                    })
                
                # ResultCode 1 = Still processing (pending)
                elif result_code == 1:
                    logger.info(f"Payment {payment.payment_ref} still processing - ResultCode 1")
                    return JsonResponse({
                        'status': 'processing',
                        'is_completed': False,
                        'message': 'Payment is still being processed...'
                    })
                
                # Any other ResultCode = Payment failed
                else:
                    logger.error(f"Payment {payment.payment_ref} failed - ResultCode {result_code}: {result_desc}")
                    payment.status = Payment.STATUS_FAILED
                    payment.error_message = f"ResultCode {result_code}: {result_desc}"
                    payment.save()
                    
                    return JsonResponse({
                        'status': 'failed',
                        'is_completed': False,
                        'message': f"Payment failed: {result_desc}"
                    })
                    
            except Exception as e:
                logger.exception(f"Error querying payment status for {payment.payment_ref}")
                return JsonResponse({
                    'status': 'processing',
                    'is_completed': False,
                    'message': 'Checking payment status...',
                    'error': str(e)
                })
        
        logger.warning(f"Payment {payment.payment_ref} has no transaction ID")
        return JsonResponse({
            'status': payment.status,
            'is_completed': False,
            'message': 'No transaction ID found'
        })
        
    except Exception as e:
        logger.exception(f"Unexpected error in check_payment_status")
        return JsonResponse({
            'status': 'error',
            'is_completed': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
def mpesa_callback(request):
    """Handle MPesa callback."""
    try:
        callback_data = json.loads(request.body)
        mpesa_service = MPesaService()
        success = mpesa_service.process_callback(callback_data)

        if success:
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'failed'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def payment_history(request):
    """View payment history."""
    payments = Payment.objects.filter(farmer=request.user).order_by('-initiated_at')

    context = {
        'payments': payments,
        'title': 'Payment History'
    }
    return render(request, 'payments/history.html', context)