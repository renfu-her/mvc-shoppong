import re
import unicodedata
from datetime import datetime
from decimal import Decimal

def generate_slug(text):
    """Generate URL-friendly slug from text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents and special characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text

def format_price(price, currency='$'):
    """Format price with currency symbol"""
    if isinstance(price, (int, float, Decimal)):
        return f"{currency}{price:.2f}"
    return f"{currency}0.00"

def format_date(date, format='%Y-%m-%d %H:%M'):
    """Format datetime object"""
    if isinstance(date, datetime):
        return date.strftime(format)
    return date

def validate_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits) <= 15

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename

def paginate_query(query, page, per_page=20):
    """Paginate SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

def calculate_discount_percentage(regular_price, sale_price):
    """Calculate discount percentage"""
    if not sale_price or not regular_price:
        return 0
    return round(((regular_price - sale_price) / regular_price) * 100)

def generate_order_number():
    """Generate unique order number (ORDER+YYMM+sequence resetting daily)."""
    today = datetime.utcnow().strftime('%y%m')
    prefix = f"ORDER{today}"

    from models.order import Order
    last_order = (Order.query
                  .filter(Order.order_number.like(f"{prefix}%"))
                  .order_by(Order.order_number.desc())
                  .first())

    if last_order and last_order.order_number.startswith(prefix):
        last_seq = int(last_order.order_number[-4:])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"{prefix}{next_seq:04d}"

def get_client_ip(request):
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def is_ajax_request(request):
    """Check if request is AJAX"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def json_response(data, status=200):
    """Create JSON response"""
    from flask import jsonify
    return jsonify(data), status

def error_response(message, status=400):
    """Create error response"""
    return json_response({'error': message}, status)

def success_response(message, data=None, status=200):
    """Create success response"""
    response = {'message': message}
    if data is not None:
        response['data'] = data
    return json_response(response, status)

# Import os for filename sanitization
import os
