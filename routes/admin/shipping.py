
from flask import flash, redirect, render_template, request, url_for

from app import db
from models import ShippingFee

from . import admin_bp, admin_required


@admin_bp.route('/shipping')
@admin_required
def shipping_fees():
    """Shipping fees list."""
    fees = ShippingFee.query.order_by(ShippingFee.sort_order).all()
    return render_template('admin/shipping/list.html', shipping_fees=fees)


@admin_bp.route('/shipping/create', methods=['GET', 'POST'])
@admin_required
def create_shipping_fee():
    """Create new shipping fee."""
    if request.method == 'POST':
        try:
            shipping_fee = ShippingFee(
                name=request.form['name'],
                description=request.form.get('description', ''),
                method_type=request.form['method_type'],
                cost=float(request.form.get('cost', 0)),
                free_shipping_threshold=float(request.form['free_shipping_threshold'])
                if request.form.get('free_shipping_threshold')
                else None,
                is_active=bool(request.form.get('is_active')),
                sort_order=int(request.form.get('sort_order', 0)),
            )

            db.session.add(shipping_fee)
            db.session.commit()
            flash('Shipping fee created successfully', 'success')
            return redirect(url_for('admin.shipping_fees'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating shipping fee: {exc}', 'error')

    return render_template('admin/shipping/create.html')
