# MVC Shopping 專案工作流程說明

## 目錄
1. [專案概述](#專案概述)
2. [資料庫表格產生方式](#資料庫表格產生方式)
3. [MVC 架構串接方式](#mvc-架構串接方式)
4. [ECharts 圖表運作方式](#echarts-圖表運作方式)
5. [專案架構圖](#專案架構圖)
6. [開發工作流程](#開發工作流程)
7. [部署流程](#部署流程)

## 專案概述

MVC Shopping 是一個基於 Python Flask 的現代電商平台，採用完整的 MVC 架構模式，整合 MySQL 資料庫、ECharts 資料視覺化、以及綠界 ECPay 金流服務。

### 技術棧
- **後端**: Python 3.8+, Flask 2.3.3
- **資料庫**: MySQL 8.0+, SQLAlchemy ORM
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **圖表**: ECharts 5.4.3
- **金流**: 綠界 ECPay
- **認證**: Flask-Login
- **圖片處理**: Pillow (PIL)

## 資料庫表格產生方式

### 1. 資料庫設定與初始化

#### 設定檔 (`config.py`)
```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/mvc-shopping'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上傳設定
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大檔案大小
    
    # 圖片設定
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    THUMBNAIL_SIZE = (300, 300)
    PRODUCT_IMAGE_SIZE = (800, 800)
    AD_IMAGE_SIZE = {
        'desktop': (1920, 1080),  # 16:9
        'mobile': (1080, 1920)    # 9:16
    }
```

#### 資料庫初始化 (`database.py`)
```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

### 2. 模型定義 (Models)

所有資料庫表格都在 `models/` 目錄下定義，使用 SQLAlchemy ORM：

#### 產品模型範例 (`models/product.py`)
```python
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    short_description = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    
    # 定價
    regular_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=True)
    
    # 庫存
    stock_quantity = db.Column(db.Integer, default=0)
    manage_stock = db.Column(db.Boolean, default=True)
    stock_status = db.Column(db.String(20), default='instock')
    
    # 產品詳情
    weight = db.Column(db.Numeric(8, 2), nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    material = db.Column(db.String(100), nullable=True)
    
    # 狀態和可見性
    status = db.Column(db.String(20), default='draft')
    featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # 關聯關係
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def current_price(self):
        """取得目前價格 (特價或原價)"""
        return self.sale_price if self.sale_price else self.regular_price
    
    @staticmethod
    def get_featured_products(limit=8):
        """取得精選產品"""
        return Product.query.filter_by(
            featured=True, 
            is_active=True, 
            status='published'
        ).limit(limit).all()
```

### 3. 資料庫建立流程

#### 步驟 1: 執行設定腳本
```bash
python setup_database.py
```

#### 步驟 2: 建立表格
```python
def create_database():
    app = create_app()
    with app.app_context():
        print("Creating database tables...")
        db.create_all()  # 根據模型定義建立所有表格
        print("Database tables created successfully!")
        
        # 建立範例資料
        create_sample_data()
        
        print("Database setup completed successfully!")
```

#### 步驟 3: 資料庫遷移 (使用 Alembic)
```bash
# 建立新的遷移
flask db migrate -m "Description of changes"

# 套用遷移
flask db upgrade
```

### 4. 主要資料表結構

| 表格名稱 | 用途 | 主要欄位 |
|---------|------|----------|
| **users** | 使用者帳號與認證 | id, username, email, password_hash, is_admin |
| **categories** | 產品分類 (支援階層結構) | id, name, slug, parent_id, is_parent |
| **products** | 產品資訊與定價 | id, name, slug, regular_price, sale_price, stock_quantity |
| **product_images** | 產品圖片管理 | id, product_id, image_path, is_primary |
| **carts** | 購物車管理 | id, user_id, session_id, created_at |
| **cart_items** | 購物車項目 | id, cart_id, product_id, quantity |
| **orders** | 訂單資訊與狀態 | id, order_number, user_id, status, total_amount |
| **order_items** | 訂單明細項目 | id, order_id, product_id, quantity, unit_price |
| **ads** | 廣告橫幅管理 | id, title, position, desktop_image, mobile_image |
| **coupons** | 折扣券系統 | id, code, discount_type, discount_value |
| **shipping_fees** | 運費方式設定 | id, name, method_type, cost |

## MVC 架構串接方式

### 1. 應用程式初始化 (`app.py`)

```python
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化擴展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'frontend.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # 使用者載入器
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # 匯入模型以註冊到 SQLAlchemy
    from models import User, Category, Product, ProductImage, Cart, CartItem, Ads, Coupon, ShippingFee, WishList
    from models.order import Order, OrderItem
    
    # 建立上傳目錄
    os.makedirs('static/uploads/products', exist_ok=True)
    os.makedirs('static/uploads/ads', exist_ok=True)
    
    # 註冊藍圖 (Blueprint)
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp, url_prefix='/backend')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
```

### 2. 控制器層 (Controller)

#### 前端控制器 (`routes/frontend/`)
```python
# routes/frontend/catalog.py
@frontend_bp.route('/')
def index():
    """首頁控制器"""
    # 1. 從模型取得資料
    featured_products = Product.get_featured_products(8)
    new_arrivals = Product.get_new_arrivals(8)
    best_sellers = Product.get_best_sellers(8)
    on_sale_products = Product.get_on_sale_products(8)
    
    # 2. 取得橫幅廣告
    banners = Ads.get_homepage_banners()
    
    # 3. 取得分類資料
    categories = Category.get_three_level_categories()
    
    # 4. 處理業務邏輯
    wishlist_product_ids = get_user_wishlist_product_ids()
    
    # 5. 準備特價商品資料
    deal_candidates = on_sale_products[:3]
    deal_products = prepare_deal_products(deal_candidates)
    
    # 6. 傳遞資料給視圖
    return render_template('frontend/index.html',
                         featured_products=featured_products,
                         new_arrivals=new_arrivals,
                         best_sellers=best_sellers,
                         on_sale_products=on_sale_products,
                         banners=banners,
                         categories=categories,
                         wishlist_product_ids=wishlist_product_ids,
                         deal_products=deal_products)
```

#### 管理後台控制器 (`routes/admin/`)
```python
# routes/admin/dashboard.py
@admin_bp.route('/')
@admin_required
def dashboard():
    """管理後台儀表板"""
    # 統計資料查詢
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_categories = Category.query.count()
    total_users = User.query.count()
    
    # 最近訂單
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # 低庫存商品
    low_stock_products = Product.query.filter(
        Product.stock_quantity <= 5,
        Product.manage_stock == True
    ).limit(10).all()
    
    # 圖表資料準備
    order_chart_data = prepare_order_chart_data()
    product_chart_data = prepare_product_chart_data()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_categories=total_categories,
                         total_users=total_users,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products,
                         order_chart_data=order_chart_data,
                         product_chart_data=product_chart_data)
```

### 3. 模型層 (Model)

#### 業務邏輯封裝
```python
# models/product.py
class Product(db.Model):
    # ... 資料庫欄位定義 ...
    
    @property
    def current_price(self):
        """取得目前價格 (特價或原價)"""
        return self.sale_price if self.sale_price else self.regular_price
    
    @property
    def discount_percentage(self):
        """計算折扣百分比"""
        if self.sale_price and self.regular_price:
            return round(((self.regular_price - self.sale_price) / self.regular_price) * 100)
        return 0
    
    @property
    def is_on_sale(self):
        """檢查是否特價"""
        return self.sale_price is not None and self.sale_price < self.regular_price
    
    @property
    def is_in_stock(self):
        """檢查是否有庫存"""
        if not self.manage_stock:
            return self.stock_status == 'instock'
        return self.stock_quantity > 0
    
    def get_primary_image(self):
        """取得主要產品圖片"""
        primary_image = ProductImage.query.filter_by(
            product_id=self.id, 
            is_primary=True
        ).first()
        if not primary_image:
            primary_image = ProductImage.query.filter_by(product_id=self.id).first()
        return primary_image
    
    @staticmethod
    def get_featured_products(limit=8):
        """取得精選產品"""
        return Product.query.filter_by(
            featured=True, 
            is_active=True, 
            status='published'
        ).limit(limit).all()
    
    @staticmethod
    def get_new_arrivals(limit=8):
        """取得新到貨產品"""
        return Product.query.filter_by(
            is_active=True, 
            status='published'
        ).order_by(Product.created_at.desc()).limit(limit).all()
```

### 4. 視圖層 (View)

#### Jinja2 模板系統
```html
<!-- templates/frontend/index.html -->
{% extends "base.html" %}

{% block title %}Home - MVC Shopping{% endblock %}

{% block content %}
<!-- 橫幅廣告區域 -->
<section class="hero-section{% if not banners %} hero-section-static{% endif %}">
    {% if banners %}
    <div id="heroCarousel" class="carousel slide hero-carousel" data-bs-ride="carousel">
        <div class="carousel-inner">
            {% for banner in banners %}
            <div class="carousel-item {% if loop.first %}active{% endif %}">
                {% if banner.link_url %}<a href="{{ banner.link_url }}">{% endif %}
                <picture>
                    {% if banner.mobile_image %}
                    <source media="(max-width: 767.98px)" 
                            srcset="{{ url_for('static', filename=banner.mobile_image) }}">
                    {% endif %}
                    <img src="{{ url_for('static', filename=banner.desktop_image) }}" 
                         class="d-block w-100 hero-banner-image" 
                         alt="{{ banner.title }}">
                </picture>
                {% if banner.link_url %}</a>{% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</section>

<!-- 精選產品區域 -->
<section class="featured-products py-5 bg-light">
    <div class="container">
        <div class="section-header text-center mb-5">
            <h2>Exclusive Products</h2>
        </div>
        <div class="row">
            {% for product in featured_products %}
            <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
                <div class="product-card">
                    <div class="product-image">
                        {% set primary_image = product.get_primary_image() %}
                        {% if primary_image %}
                        <img src="{{ url_for('static', filename=primary_image.image_path) }}" 
                             alt="{{ product.name }}" class="img-fluid">
                        {% endif %}
                        {% if product.is_on_sale %}
                        <div class="product-badge sale-badge">{{ product.discount_percentage }}% Off</div>
                        {% endif %}
                    </div>
                    <div class="product-info">
                        <h6 class="product-name">
                            <a href="{{ url_for('frontend.product_detail', slug=product.slug) }}">
                                {{ product.name }}
                            </a>
                        </h6>
                        <div class="product-price">
                            <span class="current-price">${{ "%.2f"|format(product.current_price) }}</span>
                            {% if product.sale_price %}
                            <span class="old-price">${{ "%.2f"|format(product.regular_price) }}</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>
{% endblock %}
```

### 5. MVC 資料流向

```
1. 使用者請求 → URL 路由匹配
2. 控制器接收請求 → 呼叫對應的控制器方法
3. 控制器呼叫模型方法 → 查詢資料庫
4. 模型返回資料物件 → 控制器接收資料
5. 控制器處理業務邏輯 → 準備模板資料
6. 渲染 Jinja2 模板 → 產生 HTML 頁面
7. 返回完整頁面給使用者瀏覽器
```

## ECharts 圖表運作方式

### 1. 後端資料準備

#### 控制器準備圖表資料
```python
# routes/admin/dashboard.py
def dashboard():
    analysis_days = 14
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=analysis_days - 1)
    
    # 訂單趨勢資料查詢
    order_rows = db.session.query(
        func.date(Order.created_at).label('order_date'),
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.total_amount), 0).label('order_total'),
    ).filter(Order.created_at >= start_date).group_by(
        func.date(Order.created_at)
    ).order_by(func.date(Order.created_at)).all()
    
    # 轉換為圖表格式
    order_map = {
        row.order_date: {
            'orders': row.order_count or 0,
            'revenue': float(row.order_total or 0),
        }
        for row in order_rows
    }
    
    order_chart_data = []
    for offset in range(analysis_days):
        day = start_date + timedelta(days=offset)
        stats = order_map.get(day, {'orders': 0, 'revenue': 0.0})
        order_chart_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'orders': int(stats['orders']),
            'revenue': float(stats['revenue']),
        })
    
    # 產品銷售資料查詢
    product_rows = db.session.query(
        Product.name.label('product_name'),
        func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
        func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue'),
    ).join(OrderItem, OrderItem.product_id == Product.id).join(
        Order, Order.id == OrderItem.order_id
    ).filter(Order.created_at >= start_date).filter(
        Order.status.notin_(['cancelled', 'refunded', 'failed'])
    ).group_by(Product.id, Product.name).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    product_chart_data = [
        {
            'name': row.product_name,
            'units': int(row.units_sold or 0),
            'revenue': float(row.revenue or 0),
        }
        for row in product_rows
    ]
    
    return render_template('admin/dashboard.html',
                         order_chart_data=order_chart_data,
                         product_chart_data=product_chart_data)
```

### 2. 前端 ECharts 初始化

#### HTML 模板載入 ECharts
```html
<!-- templates/admin/dashboard.html -->
<div class="row commerce-insights mb-4">
    <div class="col-lg-7 mb-4">
        <div class="card h-100">
            <div class="card-header">
                <h6 class="mb-0">Order Momentum</h6>
            </div>
            <div class="card-body">
                <div id="order-trend-chart" style="height: 320px;"></div>
            </div>
        </div>
    </div>
    <div class="col-lg-5 mb-4">
        <div class="card h-100">
            <div class="card-header">
                <h6 class="mb-0">Top Products by Units</h6>
            </div>
            <div class="card-body">
                <div id="product-performance-chart" style="height: 320px;"></div>
            </div>
        </div>
    </div>
</div>

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script>
(function() {
    const readyHandler = function() {
        const orderData = {{ order_chart_data|tojson }};
        const productData = {{ product_chart_data|tojson }};
        
        if (typeof echarts === 'undefined') {
            return;
        }
        
        const chartsToResize = [];
        
        // 訂單趨勢圖
        const orderEl = document.getElementById('order-trend-chart');
        if (orderEl && orderData.length) {
            const orderChart = echarts.init(orderEl);
            chartsToResize.push(orderChart);
            
            const orderDates = orderData.map(item => item.date);
            const orderCounts = orderData.map(item => item.orders);
            const orderRevenue = orderData.map(item => Number(item.revenue || 0));
            
            orderChart.setOption({
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: function(params) {
                        const [ordersPoint, revenuePoint] = params;
                        const revenueValue = revenuePoint ? revenuePoint.data : 0;
                        return `${ordersPoint.axisValue}<br/>Orders: ${ordersPoint.data}<br/>Revenue: $${Number(revenueValue).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    }
                },
                legend: { data: ['Orders', 'Revenue'] },
                grid: { left: '4%', right: '4%', bottom: '6%', top: '12%', containLabel: true },
                xAxis: { type: 'category', data: orderDates, boundaryGap: true },
                yAxis: [
                    { type: 'value', name: 'Orders', minInterval: 1 },
                    { type: 'value', name: 'Revenue', position: 'right', axisLabel: { formatter: value => '$' + Number(value).toLocaleString() } }
                ],
                series: [
                    { name: 'Orders', type: 'bar', data: orderCounts, barMaxWidth: 26, itemStyle: { color: '#0d6efd' } },
                    { name: 'Revenue', type: 'line', yAxisIndex: 1, smooth: true, symbolSize: 8, data: orderRevenue, itemStyle: { color: '#20c997' } }
                ]
            });
        }
        
        // 產品銷售圖
        const productEl = document.getElementById('product-performance-chart');
        if (productEl && productData.length) {
            const productChart = echarts.init(productEl);
            chartsToResize.push(productChart);
            
            const productNames = productData.map(item => item.name);
            const productUnits = productData.map(item => item.units);
            const productRevenue = productData.map(item => Number(item.revenue || 0));
            
            productChart.setOption({
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'shadow' },
                    formatter: function(params) {
                        const unitsPoint = params.find(p => p.seriesName === 'Units Sold');
                        const revenuePoint = params.find(p => p.seriesName === 'Revenue');
                        const units = unitsPoint ? unitsPoint.data : 0;
                        const revenue = revenuePoint ? revenuePoint.data : 0;
                        return `${params[0].axisValue}<br/>Units Sold: ${units}<br/>Revenue: $${Number(revenue).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    }
                },
                legend: { data: ['Units Sold', 'Revenue'] },
                grid: { left: '22%', right: '12%', bottom: '6%', top: '12%', containLabel: true },
                xAxis: [
                    { type: 'value', name: 'Units', minInterval: 1 },
                    { type: 'value', name: 'Revenue', position: 'top', axisLabel: { formatter: value => '$' + Number(value).toLocaleString() } }
                ],
                yAxis: { type: 'category', data: productNames, inverse: true, axisTick: { alignWithLabel: true } },
                series: [
                    { name: 'Units Sold', type: 'bar', xAxisIndex: 0, data: productUnits, barMaxWidth: 18, itemStyle: { color: '#6610f2' } },
                    { name: 'Revenue', type: 'line', xAxisIndex: 1, data: productRevenue, smooth: true, symbolSize: 8, itemStyle: { color: '#fd7e14' } }
                ]
            });
        }
        
        // 響應式調整
        if (chartsToResize.length) {
            window.addEventListener('resize', () => chartsToResize.forEach(chart => chart.resize()));
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', readyHandler);
    } else {
        readyHandler();
    }
})();
</script>
{% endblock %}
```

### 3. ECharts 運作流程

```
1. 後端控制器查詢資料庫統計資料
   ↓
2. 將資料轉換為 JSON 格式
   ↓
3. 透過 Jinja2 模板傳遞給前端
   ↓
4. 前端 JavaScript 接收 JSON 資料
   ↓
5. 初始化 ECharts 實例
   ↓
6. 設定圖表配置選項 (軸、系列、樣式)
   ↓
7. 綁定資料到圖表
   ↓
8. 渲染互動式圖表
   ↓
9. 響應式調整 (視窗大小改變時)
```

### 4. 圖表功能特色

- **雙軸圖表**: 訂單數量 (柱狀圖) + 營收 (折線圖)
- **互動式提示**: 滑鼠懸停顯示詳細資料
- **響應式設計**: 自動調整圖表大小
- **即時資料**: 從資料庫即時查詢最新統計
- **多種圖表類型**: 柱狀圖、折線圖、橫向條形圖
- **自適應顏色**: 使用 Bootstrap 主題色彩
- **格式化顯示**: 金額格式化、數字千分位分隔

## 專案架構圖

```
mvc-shopping/
├── app.py                 # 應用程式入口點
├── config.py              # 設定檔
├── database.py            # 資料庫初始化
├── setup_database.py      # 資料庫設定腳本
├── requirements.txt       # Python 依賴套件
├── run_sync.bat          # Windows 執行腳本
│
├── models/                # 資料模型 (Model)
│   ├── __init__.py
│   ├── user.py           # 使用者模型
│   ├── category.py       # 分類模型
│   ├── product.py        # 產品模型
│   ├── cart.py           # 購物車模型
│   ├── order.py          # 訂單模型
│   ├── ads.py            # 廣告模型
│   ├── coupon.py         # 優惠券模型
│   ├── shipping_fee.py   # 運費模型
│   └── wishlist.py       # 願望清單模型
│
├── routes/                # 路由控制器 (Controller)
│   ├── __init__.py
│   ├── api.py            # API 路由
│   ├── frontend/         # 前端路由
│   │   ├── __init__.py
│   │   ├── auth.py       # 認證路由
│   │   ├── catalog.py    # 商品目錄路由
│   │   ├── cart.py       # 購物車路由
│   │   ├── wishlist.py   # 願望清單路由
│   │   ├── account.py    # 帳戶路由
│   │   └── api.py        # 前端 API
│   └── admin/            # 後台路由
│       ├── __init__.py
│       ├── auth.py       # 後台認證
│       ├── dashboard.py  # 儀表板
│       ├── products.py   # 產品管理
│       ├── categories.py # 分類管理
│       ├── orders.py     # 訂單管理
│       ├── ads.py        # 廣告管理
│       ├── coupons.py    # 優惠券管理
│       └── shipping.py   # 運費管理
│
├── templates/             # 視圖模板 (View)
│   ├── base.html         # 基礎模板
│   ├── frontend/         # 前端模板
│   │   ├── index.html    # 首頁
│   │   ├── shop.html     # 商店頁面
│   │   ├── product_detail.html # 產品詳情
│   │   ├── cart.html     # 購物車
│   │   ├── checkout.html # 結帳頁面
│   │   ├── login.html    # 登入頁面
│   │   ├── register.html # 註冊頁面
│   │   ├── profile.html  # 個人資料
│   │   ├── wishlist.html # 願望清單
│   │   └── order_result.html # 訂單結果
│   └── admin/            # 後台模板
│       ├── base.html     # 後台基礎模板
│       ├── dashboard.html # 儀表板
│       ├── login.html    # 後台登入
│       ├── products/     # 產品管理模板
│       ├── categories/   # 分類管理模板
│       ├── orders/       # 訂單管理模板
│       ├── ads/          # 廣告管理模板
│       ├── coupons/      # 優惠券管理模板
│       └── shipping/     # 運費管理模板
│
├── static/                # 靜態資源
│   ├── css/              # 樣式表
│   │   ├── style.css     # 前端樣式
│   │   └── admin.css     # 後台樣式
│   ├── js/               # JavaScript
│   │   ├── main.js       # 前端腳本
│   │   └── admin.js      # 後台腳本
│   ├── images/           # 圖片資源
│   │   ├── logo.png
│   │   ├── hero-product.png
│   │   └── placeholder.jpg
│   └── uploads/          # 上傳檔案
│       ├── products/     # 產品圖片
│       └── ads/          # 廣告圖片
│
├── utils/                 # 工具函數
│   ├── __init__.py
│   ├── ecpay.py          # 綠界金流整合
│   ├── helpers.py        # 輔助函數
│   └── image_utils.py    # 圖片處理工具
│
├── tasks/                 # 背景任務
│   ├── __init__.py
│   └── order_status.py   # 訂單狀態同步
│
└── migrations/            # 資料庫遷移
    ├── alembic.ini
    ├── env.py
    ├── script.py.mako
    └── versions/         # 遷移版本
```

## 開發工作流程

### 1. 環境設定

#### 安裝依賴
```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境 (Windows)
venv\Scripts\activate

# 安裝依賴套件
pip install -r requirements.txt
```

#### 資料庫設定
```bash
# 建立 MySQL 資料庫
mysql -u root -p
CREATE DATABASE `mvc-shopping`;

# 執行資料庫設定
python setup_database.py
```

### 2. 開發流程

#### 新增功能
1. **建立模型** (`models/`)
   ```python
   class NewModel(db.Model):
       __tablename__ = 'new_table'
       # 定義欄位和關聯
   ```

2. **建立遷移**
   ```bash
   flask db migrate -m "Add new model"
   flask db upgrade
   ```

3. **建立控制器** (`routes/`)
   ```python
   @blueprint.route('/new-feature')
   def new_feature():
       # 控制器邏輯
       return render_template('template.html')
   ```

4. **建立模板** (`templates/`)
   ```html
   {% extends "base.html" %}
   {% block content %}
   <!-- 頁面內容 -->
   {% endblock %}
   ```

#### 測試流程
```bash
# 啟動開發伺服器
python app.py

# 測試前端
http://localhost:5000

# 測試後台
http://localhost:5000/backend/login
# 預設帳號: admin / admin123
```

### 3. 程式碼結構

#### 模型設計原則
- 使用 SQLAlchemy ORM
- 定義清晰的關聯關係
- 封裝業務邏輯方法
- 使用屬性 (property) 計算衍生值

#### 控制器設計原則
- 單一職責原則
- 清晰的資料流向
- 適當的錯誤處理
- 使用裝飾器進行權限控制

#### 模板設計原則
- 繼承基礎模板
- 使用 Jinja2 語法
- 響應式設計
- 適當的 JavaScript 整合

## 部署流程

### 1. 生產環境設定

#### 環境變數設定
```bash
# .env 檔案
SECRET_KEY=your-production-secret-key
DATABASE_URL=mysql+pymysql://user:password@host:port/database
FLASK_ENV=production
```

#### 資料庫設定
```bash
# 建立生產資料庫
mysql -u root -p
CREATE DATABASE `mvc-shopping-prod`;

# 執行遷移
flask db upgrade
```

### 2. 部署檢查清單

- [ ] 設定生產環境變數
- [ ] 更新資料庫連線設定
- [ ] 設定檔案上傳目錄權限
- [ ] 配置 Web 伺服器 (Nginx/Apache)
- [ ] 設定 SSL 憑證
- [ ] 配置防火牆規則
- [ ] 設定備份策略
- [ ] 監控系統設定

### 3. 效能優化

#### 資料庫優化
- 建立適當的索引
- 使用查詢優化
- 設定連線池

#### 前端優化
- 壓縮靜態資源
- 使用 CDN
- 啟用快取

#### 圖片優化
- 自動 WebP 轉換
- 縮圖生成
- 延遲載入

---

## 總結

MVC Shopping 專案展示了完整的 Python Flask MVC 架構實作，從資料庫設計到前端展示，包含了現代電商網站的所有核心功能。透過清晰的架構分離、完整的業務邏輯封裝、以及豐富的資料視覺化功能，為開發者提供了一個可擴展、可維護的電商平台基礎。

### 主要特色
- **完整的 MVC 架構**: 清晰的關注點分離
- **豐富的資料模型**: 支援複雜的電商業務邏輯
- **響應式前端設計**: 支援各種裝置
- **強大的管理後台**: 完整的商品和訂單管理
- **資料視覺化**: ECharts 圖表展示
- **金流整合**: 綠界 ECPay 支付整合
- **圖片處理**: 自動格式轉換和縮圖
- **RESTful API**: 支援前後端分離開發

這個專案不僅是一個功能完整的電商平台，更是一個學習 Python Web 開發和 MVC 架構設計的優秀範例。
