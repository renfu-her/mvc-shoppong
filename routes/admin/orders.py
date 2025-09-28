
from datetime import datetime

from flask import current_app, flash, redirect, render_template, request, url_for

from app import db
from models.order import Order
from utils.helpers import paginate_query
from tasks.order_status import sync_pending_orders

from . import admin_bp, admin_required


@admin_bp.route('/orders')
@admin_required
def orders():
    """Orders list."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Order.query
    if status:
        query = query.filter_by(status=status)

    orders_paginated = paginate_query(
        query.order_by(Order.created_at.desc()), page, 20
    )
    return render_template('admin/orders/list.html', orders=orders_paginated)


@admin_bp.route('/tools/pending-orders', methods=['GET', 'POST'])
@admin_required
def pending_orders_tool():
    """Admin tool to inspect and sync pending ECPay orders."""
    sync_info = None
    limit_value = 50

    if request.method == 'POST':
        limit = request.form.get('limit', type=int)
        limit_value = limit or 50
        try:
            sync_info = sync_pending_orders(limit=limit_value)
            updated = sync_info.get('updated', 0) if isinstance(sync_info, dict) else sync_info
            message_type = 'success' if updated else 'info'
            flash(f'Synced {updated} pending orders.', message_type)
        except Exception as exc:
            current_app.logger.exception('Error syncing pending orders: %s', exc)
            flash(f'Error syncing pending orders: {exc}', 'error')

    pending_orders = (
        Order.query.filter(Order.payment_status == 'pending')
        .order_by(Order.created_at.asc())
        .all()
    )
    now = datetime.utcnow()

    return render_template(
        'admin/tools/pending_orders.html',
        pending_orders=pending_orders,
        sync_info=sync_info,
        now=now,
        default_limit=limit_value,
    )


@admin_bp.route('/orders/<int:id>')
@admin_required
def order_detail(id):
    """Order detail."""
    order = Order.query.get_or_404(id)
    return render_template('admin/orders/detail.html', order=order)


@admin_bp.route('/orders/<int:id>/update-status', methods=['POST'])
@admin_required
def update_order_status(id):
    """Update order status."""
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')

    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', 'failed']
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash('Order status updated successfully', 'success')
    else:
        flash('Invalid status', 'error')

    return redirect(url_for('admin.order_detail', id=id))
