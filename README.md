# MVC Shopping - E-commerce Platform

A modern e-commerce platform built with Python Flask, featuring a complete MVC architecture, MySQL database, and responsive frontend design.

## 🚀 Recent Updates & Fixes

### ✅ Completed Features
- **User Authentication System**: Complete login/logout/register functionality for customers
- **Checkout Protection**: Login required for checkout process with proper redirects
- **Backend Route Change**: Admin panel moved from `/admin` to `/backend`
- **Cart Functionality**: Fixed add-to-cart with proper error handling
- **Database Schema**: Fixed cart table to support guest users (nullable user_id)
- **Template System**: Created missing templates (category.html, login.html, register.html)
- **Static Assets**: Added placeholder images and proper file structure
- **API Endpoints**: Working cart API with session management

### 🔧 Technical Fixes
- **Pillow Compatibility**: Updated to version >=9.0.0 for Windows compatibility
- **Circular Imports**: Resolved by creating separate database.py module
- **Decimal Type Issues**: Fixed SQLAlchemy Numeric type for price fields
- **Flask-Login Setup**: Added proper user_loader and authentication flow
- **Migration System**: Database migrations working with Alembic
- **Error Handling**: Comprehensive error handling in frontend JavaScript

## Features

### Frontend
- **Modern Design**: Based on Shopwise template with responsive layout
- **Product Catalog**: Browse products with filtering and search
- **Shopping Cart**: Add/remove items, quantity management with AJAX
- **Checkout Process**: Login-protected order flow
- **Product Details**: Detailed product pages with image galleries
- **Category Navigation**: Hierarchical category structure (3 levels max)
- **User Authentication**: Login/logout/register with session management

### Backend (Admin Panel)
- **Dashboard**: Overview of orders, products, and statistics
- **Product Management**: Create, edit, delete products with image upload
- **Category Management**: Manage product categories with hierarchy
- **Order Management**: View and update order status
- **Advertisement Management**: Manage banners and promotional content
- **Coupon System**: Create and manage discount coupons
- **Shipping Management**: Configure shipping methods and rates

### Technical Features
- **MVC Architecture**: Clean separation of concerns
- **MySQL Database**: Robust data storage with relationships
- **Image Processing**: Automatic WebP conversion and resizing
- **RESTful API**: JSON API for frontend-backend communication
- **Responsive Design**: Mobile-friendly interface
- **Security**: Admin and user authentication with data validation
- **Session Management**: Guest cart support with session-based storage

## Technology Stack

- **Backend**: Python 3.8+, Flask 2.3.3
- **Database**: MySQL 8.0+
- **ORM**: SQLAlchemy with Flask-Migrate
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Image Processing**: Pillow (PIL)
- **Authentication**: Flask-Login

## Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mvc-shopping
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**
   - Create MySQL database named `mvc-shopping`
   - Update database credentials in `config.py` if needed
   - Run the setup script:
   ```bash
   python setup_database.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Frontend: http://localhost:5000
   - User Login: http://localhost:5000/login
   - User Register: http://localhost:5000/register
   - Backend (Admin): http://localhost:5000/backend/login
   - Default admin credentials: admin / admin123
   - Test Cart: http://localhost:5000/static/test_cart.html

## Database Schema

### Core Tables
- **users**: User accounts and authentication
- **categories**: Product categories with hierarchy support
- **products**: Product information and pricing
- **product_images**: Product image management
- **carts**: Shopping cart management
- **cart_items**: Individual cart items
- **orders**: Order information and status
- **order_items**: Order line items
- **ads**: Advertisement and banner management
- **coupons**: Discount coupon system
- **shipping_fees**: Shipping method configuration

### Key Features
- **Hierarchical Categories**: Support for 3-level category structure
- **Image Management**: Automatic WebP conversion and thumbnail generation
- **Pricing System**: Regular price and sale price support
- **Inventory Management**: Stock tracking and management
- **Order Processing**: Complete order lifecycle management

## API Endpoints

### Frontend API
- `GET /api/products` - Get products with filtering
- `GET /api/products/<id>` - Get single product details
- `GET /api/categories` - Get category hierarchy
- `POST /api/cart/add` - Add item to cart (with session support)
- `POST /api/cart/update` - Update cart item quantity
- `POST /api/cart/remove` - Remove item from cart
- `GET /api/cart/count` - Get cart item count
- `POST /api/validate-coupon` - Validate coupon codes
- `POST /api/orders` - Create new order
- `GET /api/orders/<id>` - Get order details

### Admin API
- Product management endpoints
- Category management endpoints
- Order management endpoints
- Advertisement management endpoints
- Coupon management endpoints

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://root:@localhost/mvc-shopping
```

### Image Settings
- **Upload Directory**: `static/uploads/`
- **Supported Formats**: PNG, JPG, JPEG, GIF, WebP
- **Auto Conversion**: All images converted to WebP format
- **Sizes**: Product images (800x800), Thumbnails (300x300), Ads (1920x1080 desktop, 1080x1920 mobile)

## File Structure

```
mvc-shopping/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── setup_database.py     # Database setup script
├── models/               # Database models
│   ├── __init__.py
│   ├── user.py
│   ├── category.py
│   ├── product.py
│   ├── cart.py
│   ├── order.py
│   ├── ads.py
│   ├── coupon.py
│   └── shipping_fee.py
├── routes/               # URL routing
│   ├── __init__.py
│   ├── frontend.py
│   ├── admin.py
│   └── api.py
├── templates/            # HTML templates
│   ├── base.html
│   ├── frontend/
│   └── admin/
├── static/               # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── image_utils.py
│   └── helpers.py
└── migrations/           # Database migrations
    ├── env.py
    ├── script.py.mako
    └── alembic.ini
```

## Usage

### Frontend Usage
1. Browse products by category or search
2. View product details and images
3. Add products to shopping cart (works for guests and logged-in users)
4. Login required for checkout process
5. Complete order with shipping and payment information

### Backend (Admin) Usage
1. Login with admin credentials at `/backend/login`
2. Manage products, categories, and orders
3. Upload product images (automatically converted to WebP)
4. Create and manage coupons
5. Configure shipping methods
6. Monitor sales and inventory

### User Authentication
- **Guest Users**: Can browse and add to cart (session-based)
- **Logged-in Users**: Full access to checkout and order history
- **Admin Users**: Access to backend management panel

## Development

### Adding New Features
1. Create models in `models/` directory
2. Add routes in `routes/` directory
3. Create templates in `templates/` directory
4. Update database schema with migrations

### Database Migrations
```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

### Testing
- Test product creation and management
- Test order processing workflow
- Test image upload and processing
- Test coupon and shipping functionality
- Test cart functionality: http://localhost:5000/static/test_cart.html
- Test user authentication and checkout protection

### Known Issues & Solutions
- **Pillow Installation**: Use `Pillow>=9.0.0` for Windows compatibility
- **Database Migrations**: Run `flask db upgrade` after schema changes
- **Session Management**: Cart works for both guests and logged-in users
- **Image Processing**: All uploads automatically converted to WebP format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository.

## Changelog

### Version 1.1.0 (Current)
- ✅ **User Authentication System**: Complete login/logout functionality
- ✅ **Checkout Protection**: Login required for checkout with proper redirects
- ✅ **Backend Route Change**: Admin panel moved from `/admin` to `/backend`
- ✅ **Cart Functionality**: Fixed add-to-cart with session support
- ✅ **Database Schema**: Fixed cart table for guest users
- ✅ **Template System**: Added missing templates and error handling
- ✅ **Static Assets**: Added placeholder images and proper structure
- ✅ **API Endpoints**: Working cart API with comprehensive error handling
- ✅ **Migration System**: Database migrations working with Alembic
- ✅ **Technical Fixes**: Resolved Pillow, circular imports, and Decimal issues

### Version 1.0.0
- Initial release
- Complete MVC architecture
- Product management system
- Shopping cart and checkout
- Admin panel
- Image processing with WebP conversion
- Responsive design
- MySQL database integration
