"""
Receipts Views - View, Download, Verify Digital Receipts
"""
import qrcode
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string

from .models import Receipt


@login_required
def receipt_list(request):
    user = request.user
    if user.is_farmer:
        receipts = Receipt.objects.filter(farmer=user, is_valid=True).order_by('-issued_at')
    elif user.is_operator:
        receipts = Receipt.objects.filter(warehouse__operator=user).order_by('-issued_at')
    else:
        receipts = Receipt.objects.all().order_by('-issued_at')
    return render(request, 'receipts/list.html', {'receipts': receipts})


@login_required
def receipt_detail(request, pk):
    user = request.user
    if user.is_farmer:
        receipt = get_object_or_404(Receipt, pk=pk, farmer=user)
    elif user.is_operator:
        receipt = get_object_or_404(Receipt, pk=pk, warehouse__operator=user)
    else:
        receipt = get_object_or_404(Receipt, pk=pk)
    return render(request, 'receipts/detail.html', {'receipt': receipt})


@login_required
def receipt_print(request, pk):
    """Printable receipt view."""
    user = request.user
    if user.is_farmer:
        receipt = get_object_or_404(Receipt, pk=pk, farmer=user)
    else:
        receipt = get_object_or_404(Receipt, pk=pk)
    return render(request, 'receipts/print.html', {'receipt': receipt})


def verify_receipt(request):
    """Public receipt verification page."""
    result = None
    receipt_code = request.GET.get('code', '').strip()
    if receipt_code:
        try:
            receipt = Receipt.objects.get(receipt_code=receipt_code)
            result = {'found': True, 'receipt': receipt, 'valid': receipt.is_valid}
        except Receipt.DoesNotExist:
            result = {'found': False}
    return render(request, 'receipts/verify.html', {'result': result, 'code': receipt_code})


@login_required
def receipt_qr_code(request, pk):
    """Generate QR code for receipt."""
    receipt = get_object_or_404(Receipt, pk=pk)
    # Create QR code with receipt details
    qr_data = f"Receipt Code: {receipt.receipt_code}\nFarmer: {receipt.farmer.get_full_name()}\nWarehouse: {receipt.warehouse.name}\nQuantity: {receipt.quantity_bags} bags\nValid: {receipt.is_valid}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type='image/png')
