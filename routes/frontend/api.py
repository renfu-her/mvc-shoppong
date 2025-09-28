
from flask import jsonify, request
from flask_login import current_user, login_required

from app import db
from models import Coupon, Product, WishList

from . import frontend_bp
from .helpers import get_or_create_cart, get_wishlist_count


@frontend_bp.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """Add item to cart via AJAX."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})

    product = Product.query.get_or_404(product_id)
    if not product.is_in_stock:
        return jsonify({'success': False, 'message': 'Product out of stock'})

    cart = get_or_create_cart()
    cart.add_item(product_id, quantity)

    return jsonify(
        {
            'success': True,
            'message': 'Item added to cart',
            'cart_count': cart.total_items,
        }
    )


@frontend_bp.route('/api/wishlist/toggle', methods=['POST'])
@login_required
def api_toggle_wishlist():
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    'success': False,
                    'message': 'Please log in to manage your wishlist.',
                    'requires_login': True,
                }
            ),
            401,
        )

    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    wishlist_item = WishList.query.filter_by(
        user_id=current_user.id, product_id=product_id
    ).first()

    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed', 'count': get_wishlist_count()})

    wishlist_item = WishList(
        user_id=current_user.id, product_id=product_id, quantity=quantity
    )
    db.session.add(wishlist_item)
    db.session.commit()

    return jsonify({'success': True, 'action': 'added', 'count': get_wishlist_count()})


@frontend_bp.route('/api/wishlist/count')
def api_wishlist_count():
    return jsonify({'count': get_wishlist_count()})


@frontend_bp.route('/api/cart/update', methods=['POST'])
def api_update_cart():
    """Update cart item quantity via AJAX."""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})

    cart = get_or_create_cart()
    cart.update_item_quantity(product_id, quantity)

    return jsonify(
        {
            'success': True,
            'message': 'Cart updated',
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
        }
    )


@frontend_bp.route('/api/cart/remove', methods=['POST'])
def api_remove_from_cart():
    """Remove item from cart via AJAX."""
    data = request.get_json() or {}
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID required'})

    cart = get_or_create_cart()
    cart.remove_item(product_id)

    return jsonify(
        {
            'success': True,
            'message': 'Item removed from cart',
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
        }
    )


@frontend_bp.route('/api/cart/count')
def api_cart_count():
    """Get cart item count via AJAX."""
    cart = get_or_create_cart()
    return jsonify({'count': cart.total_items})


@frontend_bp.route('/api/validate-coupon', methods=['POST'])
def api_validate_coupon():
    """Validate coupon code via AJAX."""
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()

    if not code:
        return jsonify({'success': False, 'message': 'Coupon code required'})

    cart = get_or_create_cart()
    product_ids = [item.product_id for item in cart.items]

    coupon, message = Coupon.validate_coupon_code(
        code=code,
        order_amount=float(cart.subtotal),
        product_ids=product_ids,
    )

    if coupon:
        discount = coupon.calculate_discount(float(cart.subtotal))
        return jsonify(
            {
                'success': True,
                'message': 'Coupon applied successfully',
                'discount': float(discount),
                'coupon_code': coupon.code,
            }
        )

    return jsonify({'success': False, 'message': message})
