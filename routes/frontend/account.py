
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from models.order import Order

from . import frontend_bp


@frontend_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with order history."""
    user = current_user

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        user.first_name = first_name or None
        user.last_name = last_name or None
        user.phone = phone or None
        user.address = address or None

        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('frontend.profile'))

    orders = (
        Order.query.filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    order_stats = {
        'total': len(orders),
        'pending': sum(1 for order in orders if order.status == 'pending'),
        'processing': sum(1 for order in orders if order.status == 'processing'),
        'completed': sum(1 for order in orders if order.status in {'shipped', 'delivered'}),
        'cancelled': sum(1 for order in orders if order.status in {'cancelled', 'refunded'}),
    }

    return render_template(
        'frontend/profile.html',
        user=user,
        orders=orders,
        order_stats=order_stats,
    )
