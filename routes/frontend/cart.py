
from decimal import Decimal

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app import db
from models import ShippingFee
from models.order import Order, OrderItem
from utils.ecpay import ECPayService, ECPAY_TEST_CONFIG
from utils.helpers import generate_order_number

from . import frontend_bp
from .helpers import get_or_create_cart


@frontend_bp.route('/cart')
def cart():
    """Shopping cart page."""
    cart_obj = get_or_create_cart()
    return render_template('frontend/cart.html', cart=cart_obj)


@frontend_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page - requires login."""
    cart_obj = get_or_create_cart()
    if not cart_obj or not cart_obj.items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('frontend.cart'))

    shipping_methods = ShippingFee.get_available_shipping_methods(
        order_amount=float(cart_obj.subtotal)
    )

    return render_template(
        'frontend/checkout.html',
        cart=cart_obj,
        shipping_methods=shipping_methods,
    )


@frontend_bp.route('/checkout/process', methods=['POST'])
@login_required
def process_checkout():
    """Process checkout and redirect to ECPay."""
    cart_obj = get_or_create_cart()
    cart_items = list(cart_obj.items) if cart_obj else []
    if not cart_obj or not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('frontend.cart'))

    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    shipping_method_id = request.form.get('shipping_method')
    notes = request.form.get('notes', '')

    if current_user.is_authenticated:
        dirty = False
        if current_user.first_name != first_name:
            current_user.first_name = first_name
            dirty = True
        if current_user.last_name != last_name:
            current_user.last_name = last_name
            dirty = True
        if getattr(current_user, 'phone', None) != phone:
            current_user.phone = phone
            dirty = True
        if getattr(current_user, 'address', None) != address:
            current_user.address = address
            dirty = True
        if dirty:
            db.session.add(current_user)

    if not all([first_name, last_name, email, phone, address, shipping_method_id]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('frontend.checkout'))

    try:
        shipping_method_id = int(shipping_method_id)
    except (TypeError, ValueError):
        flash('Invalid shipping method', 'error')
        return redirect(url_for('frontend.checkout'))

    shipping_method = ShippingFee.query.get(shipping_method_id)
    if not shipping_method:
        flash('Invalid shipping method', 'error')
        return redirect(url_for('frontend.checkout'))

    shipping_cost = shipping_method.calculate_shipping_cost(
        order_amount=float(cart_obj.subtotal)
    )
    if shipping_cost is None:
        flash('Invalid shipping method for this order', 'error')
        return redirect(url_for('frontend.checkout'))

    order_subtotal = Decimal(str(cart_obj.subtotal))
    shipping_cost_decimal = Decimal(str(shipping_cost))
    order_total = order_subtotal + shipping_cost_decimal

    order = Order(
        user_id=current_user.id,
        order_number=generate_order_number(),
        status='pending',
        customer_email=email,
        customer_phone=phone,
        billing_first_name=first_name,
        billing_last_name=last_name,
        billing_address_1=address,
        billing_city='Taipei',
        billing_state='Taiwan',
        billing_postcode='100',
        billing_country='TW',
        shipping_first_name=first_name,
        shipping_last_name=last_name,
        shipping_address_1=address,
        shipping_city='Taipei',
        shipping_state='Taiwan',
        shipping_postcode='100',
        shipping_country='TW',
        shipping_method=shipping_method.name,
        payment_method='ecpay',
        subtotal=order_subtotal,
        shipping_fee=shipping_cost_decimal,
        total_amount=order_total,
        customer_notes=notes,
        payment_status='pending',
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_items:
        product = item.product
        if not product:
            continue

        unit_price = Decimal(str(product.sale_price or product.regular_price))
        total_price = unit_price * item.quantity
        primary_image = product.get_primary_image()

        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                product_image=primary_image.image_path if primary_image else None,
                unit_price=unit_price,
                quantity=item.quantity,
                total_price=total_price,
            )
        )

    ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
    merchant_trade_no = ecpay_service.generate_merchant_trade_no(order.id)
    order.transaction_id = merchant_trade_no

    db.session.commit()

    item_names = [
        f"{item.product.name} x {item.quantity}" for item in cart_items if item.product
    ]
    order_data = {
        'merchant_trade_no': merchant_trade_no,
        'merchant_trade_date': ecpay_service.format_trade_date(),
        'total_amount': int(order.total_amount),
        'trade_desc': f"Order #{order.order_number}",
        'item_name': '#'.join(item_names),
        'return_url': url_for('frontend.ecpay_return', _external=True),
        'order_result_url': url_for('frontend.order_result', order_id=order.id, _external=True),
        'client_back_url': url_for('frontend.index', _external=True),
        'custom_field1': str(order.id),
        'custom_field2': f"{first_name} {last_name}",
        'custom_field3': email,
        'custom_field4': phone,
    }

    ecpay_params = ecpay_service.create_order(order_data)
    session['ecpay_params'] = ecpay_params
    session['order_id'] = order.id

    cart_obj.clear()

    return render_template(
        'frontend/ecpay_redirect.html',
        ecpay_params=ecpay_params,
        ecpay_url=ecpay_service.api_url,
    )


@frontend_bp.route('/ecpay/return', methods=['POST'])
def ecpay_return():
    """ECPay payment result notification (server-to-server)."""
    ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
    form_data = request.form.to_dict()

    if not ecpay_service.verify_check_mac_value(form_data.copy()):
        return '0|CheckMacValue verification failed'

    merchant_trade_no = form_data.get('MerchantTradeNo')
    rtn_code = form_data.get('RtnCode')
    trade_no = form_data.get('TradeNo')
    payment_type = form_data.get('PaymentType')
    custom_field1 = form_data.get('CustomField1')

    order = None
    if custom_field1 and custom_field1.isdigit():
        order = Order.query.get(int(custom_field1))
    if not order and merchant_trade_no:
        order = Order.query.filter_by(transaction_id=merchant_trade_no).first()

    if not order:
        return '0|OrderNotFound'

    if rtn_code == '1':
        order.payment_status = 'paid'
        order.status = 'processing'
        if trade_no:
            order.ecpay_trade_no = trade_no
        if merchant_trade_no:
            order.transaction_id = merchant_trade_no
    else:
        order.payment_status = 'failed'
        if order.status == 'processing':
            order.status = 'pending'

    if payment_type:
        order.payment_method = payment_type

    db.session.commit()
    return '1|OK'


@frontend_bp.route('/order/result/<int:order_id>', methods=['GET', 'POST'])
def order_result(order_id):
    """Order result page after payment or gateway callback."""
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        form_data = request.form.to_dict()
        ecpay_service = ECPayService(**ECPAY_TEST_CONFIG)
        if ecpay_service.verify_check_mac_value(form_data.copy()):
            merchant_trade_no = form_data.get('MerchantTradeNo')
            rtn_code = form_data.get('RtnCode')
            trade_no = form_data.get('TradeNo')
            payment_type = form_data.get('PaymentType')
            payment_date = form_data.get('PaymentDate')
            trade_amt = form_data.get('TradeAmt')
            rtn_msg = form_data.get('RtnMsg')

            if merchant_trade_no:
                order.transaction_id = merchant_trade_no
            if payment_type:
                order.payment_method = payment_type

            if rtn_code == '1':
                order.payment_status = 'paid'
                order.status = 'processing'
                if trade_no:
                    order.ecpay_trade_no = trade_no
            else:
                order.payment_status = 'failed'
                if order.status == 'processing':
                    order.status = 'pending'

            payload_store = session.get('order_result_payload', {})
            payload_store[str(order.id)] = {
                'merchant_trade_no': merchant_trade_no,
                'trade_no': trade_no,
                'payment_type': payment_type,
                'payment_date': payment_date,
                'trade_amt': trade_amt,
                'rtn_code': rtn_code,
                'rtn_msg': rtn_msg,
            }
            session['order_result_payload'] = payload_store
            session.modified = True

            db.session.commit()
        return redirect(url_for('frontend.order_result', order_id=order.id))

    payload_store = session.get('order_result_payload', {})
    result_payload = (
        payload_store.pop(str(order.id), None)
        if isinstance(payload_store, dict)
        else None
    )
    session['order_result_payload'] = (
        payload_store if isinstance(payload_store, dict) else {}
    )
    session.modified = True

    if not current_user.is_authenticated:
        return redirect(url_for('frontend.login', next=request.path))

    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('frontend.index'))

    return render_template(
        'frontend/order_result.html',
        order=order,
        result_payload=result_payload,
    )


@frontend_bp.route('/ecpay/test-info')
def ecpay_test_info():
    """ECPay test information page."""
    return render_template('frontend/ecpay_test_info.html')
