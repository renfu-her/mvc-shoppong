
from flask import flash, redirect, render_template, request, url_for

from app import db
from models import Coupon

from . import admin_bp, admin_required


@admin_bp.route('/coupons')
@admin_required
def coupons():
    """Coupons list."""
    coupons_data = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template('admin/coupons/list.html', coupons=coupons_data)


@admin_bp.route('/coupons/create', methods=['GET', 'POST'])
@admin_required
def create_coupon():
    """Create new coupon."""
    if request.method == 'POST':
        try:
            coupon = Coupon(
                code=request.form['code'],
                name=request.form['name'],
                description=request.form.get('description', ''),
                discount_type=request.form['discount_type'],
                discount_value=float(request.form['discount_value']),
                minimum_amount=float(request.form.get('minimum_amount', 0)),
                maximum_discount=float(request.form['maximum_discount'])
                if request.form.get('maximum_discount')
                else None,
                usage_limit=int(request.form['usage_limit'])
                if request.form.get('usage_limit')
                else None,
                usage_limit_per_user=int(request.form.get('usage_limit_per_user', 1)),
                is_active=bool(request.form.get('is_active')),
            )

            db.session.add(coupon)
            db.session.commit()
            flash('Coupon created successfully', 'success')
            return redirect(url_for('admin.coupons'))

        except Exception as exc:
            db.session.rollback()
            flash(f'Error creating coupon: {exc}', 'error')

    return render_template('admin/coupons/create.html')
