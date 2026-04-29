"""
Management command to sync payment statuses from MPesa
"""
from django.core.management.base import BaseCommand
from payments.models import Payment
from payments.mpesa import MPesaService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync payment statuses from MPesa for pending/processing payments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--payment-id',
            type=str,
            help='Sync a specific payment by ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all processing payments',
        )

    def handle(self, *args, **options):
        mpesa_service = MPesaService()

        if options['payment_id']:
            # Sync specific payment
            try:
                payment = Payment.objects.get(payment_id=options['payment_id'])
                self.sync_payment(payment, mpesa_service)
            except Payment.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Payment {options['payment_id']} not found")
                )
        elif options['all']:
            # Sync all processing payments
            payments = Payment.objects.filter(
                status__in=['pending', 'processing']
            )
            count = 0
            for payment in payments:
                if self.sync_payment(payment, mpesa_service):
                    count += 1
            self.stdout.write(
                self.style.SUCCESS(f"Successfully synced {count} payments")
            )
        else:
            # Show processing payments
            payments = Payment.objects.filter(
                status__in=['pending', 'processing']
            ).order_by('-initiated_at')
            
            if not payments.exists():
                self.stdout.write("No pending or processing payments found.")
                return
            
            self.stdout.write(f"\nFound {payments.count()} processing payments:\n")
            for payment in payments:
                self.stdout.write(
                    f"  ID: {payment.payment_id} | "
                    f"Booking: {payment.booking.booking_ref_human} | "
                    f"Status: {payment.status} | "
                    f"Amount: KES {payment.amount_kes}"
                )
            
            self.stdout.write("\nUse --all flag to sync all payments, or --payment-id <id> to sync specific payment")

    def sync_payment(self, payment, mpesa_service):
        """Sync a single payment status"""
        if not payment.mpesa_transaction_id:
            logger.warning(f"No transaction ID for payment {payment.payment_id}")
            return False

        try:
            query_response = mpesa_service.query_payment_status(
                payment.mpesa_transaction_id
            )
            result_code = query_response.get('ResultCode')
            
            if result_code == 0:
                # Payment confirmed
                receipt_number = None
                if 'result' in query_response:
                    result_items = query_response.get('result', {})
                    if isinstance(result_items, dict):
                        receipt_number = (
                            result_items.get('MpesaReceiptNumber') or
                            result_items.get('mpesaReceiptNumber')
                        )
                
                payment.mark_completed(receipt_number=receipt_number)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Payment {payment.payment_id} marked as COMPLETED"
                    )
                )
                return True
            
            elif result_code == 1:
                # Still processing
                self.stdout.write(
                    f"⏳ Payment {payment.payment_id} still processing..."
                )
                return False
            
            else:
                # Failed
                payment.status = Payment.STATUS_FAILED
                payment.error_message = query_response.get('ResultDesc', 'Payment failed')
                payment.save()
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Payment {payment.payment_id} marked as FAILED: "
                        f"{payment.error_message}"
                    )
                )
                return False
        
        except Exception as e:
            logger.error(f"Error syncing payment {payment.payment_id}: {str(e)}")
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Error syncing payment {payment.payment_id}: {str(e)}"
                )
            )
            return False
