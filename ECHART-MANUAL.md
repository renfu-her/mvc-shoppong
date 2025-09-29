# ECharts 實作手冊
# MVC Shopping Platform - ECharts Implementation Manual

## 目錄
1. [概述](#概述)
2. [目前實作的圖表](#目前實作的圖表)
3. [ECharts 架構](#echarts-架構)
4. [資料流程](#資料流程)
5. [圖表組件詳解](#圖表組件詳解)
6. [擴展新圖表](#擴展新圖表)
7. [最佳實作](#最佳實作)
8. [故障排除](#故障排除)

## 概述

MVC Shopping 專案使用 **ECharts 5.4.3** 作為主要的資料視覺化解決方案，目前主要應用在管理後台的儀表板頁面，提供電商營運的重要指標視覺化展示。

### 技術規格
- **ECharts 版本**: 5.4.3
- **載入方式**: CDN (jsdelivr)
- **整合方式**: 直接在 HTML 模板中嵌入 JavaScript
- **響應式支援**: 完整支援
- **主題**: 使用透明背景配合 Bootstrap 主題色

## 目前實作的圖表

### 1. 訂單趨勢圖 (Order Momentum Chart)
**位置**: 管理後台首頁左側
**圖表類型**: 混合圖表 (柱狀圖 + 折線圖)
**資料來源**: `Order` 表格
**時間範圍**: 動態可調整 (7天、14天、30天、90天或自訂區間)
**新增功能**: 
- ✅ 日期區間選擇器
- ✅ 預設時間範圍按鈕
- ✅ ECharts 內建縮放功能 (dataZoom)
- ✅ AJAX 動態更新

#### 資料結構
```json
[
  {
    "date": "2024-01-15",
    "orders": 5,
    "revenue": 1250.00
  }
]
```

#### 圖表特色
- **雙軸設計**: 左軸顯示訂單數量，右軸顯示營收金額
- **柱狀圖**: 每日訂單數量 (藍色 #0d6efd)
- **折線圖**: 每日營收金額 (綠色 #20c997)
- **互動提示**: 顯示日期、訂單數、營收金額
- **響應式**: 自動調整圖表尺寸

### 2. 產品銷售排行圖 (Top Products Performance Chart)
**位置**: 管理後台首頁右側
**圖表類型**: 混合圖表 (橫向柱狀圖 + 折線圖)
**資料來源**: `OrderItem` + `Product` 表格
**顯示範圍**: 前 10 名熱銷商品
**新增功能**:
- ✅ 支援動態日期區間調整
- ✅ AJAX 動態更新資料

#### 資料結構
```json
[
  {
    "name": "iPhone 15 Pro",
    "units": 25,
    "revenue": 24750.00
  }
]
```

#### 圖表特色
- **橫向佈局**: 產品名稱顯示在 Y 軸
- **雙軸設計**: 下軸顯示銷售數量，上軸顯示營收
- **柱狀圖**: 銷售數量 (紫色 #6610f2)
- **折線圖**: 營收金額 (橘色 #fd7e14)
- **排序**: 按銷售數量降序排列
- **限制**: 僅顯示前 10 名產品

## ECharts 架構

### 文件結構
```
templates/admin/dashboard.html
├── HTML 容器
│   ├── #order-trend-chart (320px 高度)
│   └── #product-performance-chart (320px 高度)
├── CDN 載入
│   └── echarts@5.4.3/dist/echarts.min.js
└── JavaScript 初始化
    ├── 資料處理
    ├── 圖表配置
    └── 響應式處理
```

### 程式碼架構
```javascript
(function() {
    const readyHandler = function() {
        // 1. 接收後端傳來的 JSON 資料
        const orderData = {{ order_chart_data|tojson }};
        const productData = {{ product_chart_data|tojson }};
        
        // 2. 檢查 ECharts 是否載入
        if (typeof echarts === 'undefined') return;
        
        // 3. 初始化圖表實例
        const chartsToResize = [];
        
        // 4. 訂單趨勢圖設定
        if (orderEl && orderData.length) {
            const orderChart = echarts.init(orderEl);
            // 配置選項...
        }
        
        // 5. 產品銷售圖設定
        if (productEl && productData.length) {
            const productChart = echarts.init(productEl);
            // 配置選項...
        }
        
        // 6. 響應式調整
        window.addEventListener('resize', () => 
            chartsToResize.forEach(chart => chart.resize())
        );
    };
    
    // 7. DOM 載入完成後執行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', readyHandler);
    } else {
        readyHandler();
    }
})();
```

## 日期區間選擇功能

### 1. UI 控件說明

#### 預設時間範圍按鈕
- **7 Days**: 最近 7 天
- **14 Days**: 最近 14 天 (預設選中)
- **30 Days**: 最近 30 天  
- **90 Days**: 最近 90 天

#### 自訂日期選擇器
- **開始日期**: 分析期間起始日期
- **結束日期**: 分析期間結束日期 (不可超過今天)
- **Update 按鈕**: 套用自訂日期範圍

#### 載入指示器
- 資料更新時顯示旋轉載入圖示
- 提供視覺反饋改善使用者體驗

### 2. 功能特色

#### 動態更新
- **無需重新整理頁面**: 使用 AJAX 技術
- **即時資料**: 從資料庫即時查詢指定時間範圍
- **平滑動畫**: 圖表數據切換帶有過渡效果

#### 數據縮放
- **ECharts dataZoom**: 內建滑桿縮放功能
- **日期軸縮放**: 可以放大檢視特定時間段
- **拖拽操作**: 支援滑鼠拖拽調整顯示範圍

#### 輸入驗證
- **日期格式檢查**: 確保輸入格式正確
- **邏輯驗證**: 開始日期不可晚於結束日期
- **未來日期限制**: 結束日期不可超過今天

### 3. API 端點

#### GET `/backend/chart-data`
**參數**:
- `days` (optional): 指定最近天數 (1-365)
- `start_date` (optional): 開始日期 (YYYY-MM-DD)
- `end_date` (optional): 結束日期 (YYYY-MM-DD)

**回應格式**:
```json
{
    "success": true,
    "order_chart_data": [...],
    "product_chart_data": [...],
    "analysis_range_label": "Jan 15 - Jan 29, 2024",
    "start_date": "2024-01-15",
    "end_date": "2024-01-29"
}
```

**錯誤回應**:
```json
{
    "success": false,
    "error": "Invalid date format"
}
```

## 資料流程

### 1. 後端資料準備流程

```python
# routes/admin/dashboard.py

def dashboard():
    # Step 1: 設定分析時間範圍
    analysis_days = 14
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=analysis_days - 1)
    
    # Step 2: 查詢訂單統計資料
    order_rows = db.session.query(
        func.date(Order.created_at).label('order_date'),
        func.count(Order.id).label('order_count'),
        func.coalesce(func.sum(Order.total_amount), 0).label('order_total'),
    ).filter(Order.created_at >= start_date
    ).group_by(func.date(Order.created_at)
    ).order_by(func.date(Order.created_at)).all()
    
    # Step 3: 轉換為圖表資料格式
    order_map = {
        row.order_date: {
            'orders': row.order_count or 0,
            'revenue': float(row.order_total or 0),
        }
        for row in order_rows
    }
    
    # Step 4: 填補缺失日期 (確保連續 14 天資料)
    order_chart_data = []
    for offset in range(analysis_days):
        day = start_date + timedelta(days=offset)
        stats = order_map.get(day, {'orders': 0, 'revenue': 0.0})
        order_chart_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'orders': int(stats['orders']),
            'revenue': float(stats['revenue']),
        })
    
    # Step 5: 查詢產品銷售統計
    product_rows = db.session.query(
        Product.name.label('product_name'),
        func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
        func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue'),
    ).join(OrderItem, OrderItem.product_id == Product.id
    ).join(Order, Order.id == OrderItem.order_id
    ).filter(Order.created_at >= start_date
    ).filter(Order.status.notin_(['cancelled', 'refunded', 'failed'])
    ).group_by(Product.id, Product.name
    ).order_by(func.sum(OrderItem.quantity).desc()
    ).limit(10).all()
    
    # Step 6: 轉換產品資料格式
    product_chart_data = [
        {
            'name': row.product_name,
            'units': int(row.units_sold or 0),
            'revenue': float(row.revenue or 0),
        }
        for row in product_rows
    ]
    
    # Step 7: 傳遞給模板
    return render_template('admin/dashboard.html',
                         order_chart_data=order_chart_data,
                         product_chart_data=product_chart_data)
```

### 2. 前端資料處理流程

```javascript
// 1. 接收後端 JSON 資料
const orderData = {{ order_chart_data|tojson }};
const productData = {{ product_chart_data|tojson }};

// 2. 轉換為 ECharts 所需格式
// 訂單趨勢圖
const orderDates = orderData.map(item => item.date);
const orderCounts = orderData.map(item => item.orders);
const orderRevenue = orderData.map(item => Number(item.revenue || 0));

// 產品銷售圖
const productNames = productData.map(item => item.name);
const productUnits = productData.map(item => item.units);
const productRevenue = productData.map(item => Number(item.revenue || 0));

// 3. 設定圖表配置並渲染
```

## 圖表組件詳解

### 1. 訂單趨勢圖配置

```javascript
orderChart.setOption({
    // 基本設定
    backgroundColor: 'transparent',
    
    // 提示框配置
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
            const [ordersPoint, revenuePoint] = params;
            const revenueValue = revenuePoint ? revenuePoint.data : 0;
            return `${ordersPoint.axisValue}<br/>
                    Orders: ${ordersPoint.data}<br/>
                    Revenue: $${Number(revenueValue).toLocaleString(undefined, { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                    })}`;
        }
    },
    
    // 圖例
    legend: { data: ['Orders', 'Revenue'] },
    
    // 網格設定
    grid: { 
        left: '4%', 
        right: '4%', 
        bottom: '6%', 
        top: '12%', 
        containLabel: true 
    },
    
    // X 軸 (時間)
    xAxis: { 
        type: 'category', 
        data: orderDates, 
        boundaryGap: true 
    },
    
    // Y 軸 (雙軸)
    yAxis: [
        { 
            type: 'value', 
            name: 'Orders', 
            minInterval: 1 
        },
        { 
            type: 'value', 
            name: 'Revenue', 
            position: 'right', 
            axisLabel: { 
                formatter: value => '$' + Number(value).toLocaleString() 
            } 
        }
    ],
    
    // 系列配置
    series: [
        { 
            name: 'Orders', 
            type: 'bar', 
            data: orderCounts, 
            barMaxWidth: 26, 
            itemStyle: { color: '#0d6efd' } 
        },
        { 
            name: 'Revenue', 
            type: 'line', 
            yAxisIndex: 1, 
            smooth: true, 
            symbolSize: 8, 
            data: orderRevenue, 
            itemStyle: { color: '#20c997' } 
        }
    ]
});
```

### 2. 產品銷售圖配置

```javascript
productChart.setOption({
    // 基本設定
    backgroundColor: 'transparent',
    
    // 提示框配置
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
            const unitsPoint = params.find(p => p.seriesName === 'Units Sold');
            const revenuePoint = params.find(p => p.seriesName === 'Revenue');
            const units = unitsPoint ? unitsPoint.data : 0;
            const revenue = revenuePoint ? revenuePoint.data : 0;
            return `${params[0].axisValue}<br/>
                    Units Sold: ${units}<br/>
                    Revenue: $${Number(revenue).toLocaleString(undefined, { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                    })}`;
        }
    },
    
    // 圖例
    legend: { data: ['Units Sold', 'Revenue'] },
    
    // 網格設定
    grid: { 
        left: '22%', 
        right: '12%', 
        bottom: '6%', 
        top: '12%', 
        containLabel: true 
    },
    
    // X 軸 (雙軸)
    xAxis: [
        { 
            type: 'value', 
            name: 'Units', 
            minInterval: 1 
        },
        { 
            type: 'value', 
            name: 'Revenue', 
            position: 'top', 
            axisLabel: { 
                formatter: value => '$' + Number(value).toLocaleString() 
            } 
        }
    ],
    
    // Y 軸 (產品名稱)
    yAxis: { 
        type: 'category', 
        data: productNames, 
        inverse: true, 
        axisTick: { alignWithLabel: true } 
    },
    
    // 系列配置
    series: [
        { 
            name: 'Units Sold', 
            type: 'bar', 
            xAxisIndex: 0, 
            data: productUnits, 
            barMaxWidth: 18, 
            itemStyle: { color: '#6610f2' } 
        },
        { 
            name: 'Revenue', 
            type: 'line', 
            xAxisIndex: 1, 
            data: productRevenue, 
            smooth: true, 
            symbolSize: 8, 
            itemStyle: { color: '#fd7e14' } 
        }
    ]
});
```

## 擴展新圖表

### 1. 後端資料準備

```python
# routes/admin/dashboard.py

def dashboard():
    # 現有程式碼...
    
    # 新增: 分類銷售統計
    category_rows = db.session.query(
        Category.name.label('category_name'),
        func.count(Product.id).label('product_count'),
        func.coalesce(func.sum(OrderItem.quantity), 0).label('total_sales')
    ).join(Product, Product.category_id == Category.id
    ).join(OrderItem, OrderItem.product_id == Product.id
    ).join(Order, Order.id == OrderItem.order_id
    ).filter(Order.created_at >= start_date
    ).group_by(Category.id, Category.name
    ).order_by(func.sum(OrderItem.quantity).desc()
    ).all()
    
    category_chart_data = [
        {
            'name': row.category_name,
            'products': int(row.product_count or 0),
            'sales': int(row.total_sales or 0)
        }
        for row in category_rows
    ]
    
    return render_template('admin/dashboard.html',
                         # 現有參數...
                         category_chart_data=category_chart_data)
```

### 2. 前端 HTML 容器

```html
<!-- templates/admin/dashboard.html -->
<div class="col-lg-6 mb-4">
    <div class="card h-100">
        <div class="card-header">
            <h6 class="mb-0">Category Performance</h6>
        </div>
        <div class="card-body">
            <div id="category-chart" style="height: 300px;"></div>
        </div>
    </div>
</div>
```

### 3. JavaScript 圖表初始化

```javascript
// 在現有 script 區塊中新增
const categoryData = {{ category_chart_data|tojson }};

const categoryEl = document.getElementById('category-chart');
if (categoryEl && categoryData.length) {
    const categoryChart = echarts.init(categoryEl);
    chartsToResize.push(categoryChart);
    
    categoryChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            type: 'scroll',
            orient: 'vertical',
            right: 10,
            top: 20,
            bottom: 20,
        },
        series: [
            {
                name: 'Category Sales',
                type: 'pie',
                radius: ['50%', '70%'],
                avoidLabelOverlap: false,
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '30',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: categoryData.map(item => ({
                    value: item.sales,
                    name: item.name
                }))
            }
        ]
    });
}
```

## 最佳實作

### 1. 效能優化

#### 資料查詢優化
```python
# 使用索引優化查詢
# 確保 Order.created_at 有索引
# 確保外鍵關聯有適當索引

# 限制查詢資料量
.limit(100)  # 避免查詢過多資料

# 使用快取 (可選)
from flask_caching import Cache
@cache.cached(timeout=300)  # 快取 5 分鐘
def get_chart_data():
    # 查詢邏輯
    pass
```

#### 前端優化
```javascript
// 1. 延遲載入 ECharts
function loadEChartsAsync() {
    return new Promise((resolve, reject) => {
        if (typeof echarts !== 'undefined') {
            resolve(echarts);
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js';
        script.onload = () => resolve(window.echarts);
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// 2. 圖表大小優化
chart.setOption(option, true);  // 使用 notMerge 選項
chart.resize();  // 手動觸發重新計算

// 3. 記憶體管理
window.addEventListener('beforeunload', () => {
    chartsToResize.forEach(chart => chart.dispose());
});
```

### 2. 響應式設計

```javascript
// 斷點配置
const breakpoints = {
    xs: 0,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200
};

function getResponsiveOption(width) {
    if (width < breakpoints.md) {
        // 手機版配置
        return {
            grid: { left: '10%', right: '10%' },
            legend: { orient: 'horizontal', bottom: 0 }
        };
    } else {
        // 桌面版配置
        return {
            grid: { left: '4%', right: '4%' },
            legend: { orient: 'horizontal', top: 0 }
        };
    }
}

// 應用響應式配置
window.addEventListener('resize', () => {
    const width = window.innerWidth;
    chartsToResize.forEach(chart => {
        chart.setOption(getResponsiveOption(width));
        chart.resize();
    });
});
```

### 3. 錯誤處理

```javascript
function initChart(elementId, data, options) {
    try {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Chart element ${elementId} not found`);
            return null;
        }
        
        if (!data || data.length === 0) {
            element.innerHTML = '<div class="text-center text-muted p-4">No data available</div>';
            return null;
        }
        
        const chart = echarts.init(element);
        chart.setOption(options);
        
        // 錯誤監聽
        chart.on('error', function(err) {
            console.error('Chart error:', err);
            element.innerHTML = '<div class="text-center text-danger p-4">Chart loading failed</div>';
        });
        
        return chart;
        
    } catch (error) {
        console.error('Failed to initialize chart:', error);
        return null;
    }
}
```

### 4. 主題一致性

```javascript
// 定義統一的顏色主題
const CHART_COLORS = {
    primary: '#0d6efd',
    success: '#20c997',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#0dcaf0',
    secondary: '#6c757d',
    purple: '#6610f2',
    orange: '#fd7e14'
};

// 建立主題配置
function createTheme() {
    return {
        color: Object.values(CHART_COLORS),
        backgroundColor: 'transparent',
        textStyle: {
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            fontSize: 12
        },
        title: {
            textStyle: {
                color: '#495057',
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        legend: {
            textStyle: {
                color: '#6c757d'
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            borderWidth: 0,
            textStyle: {
                color: '#fff'
            }
        }
    };
}

// 應用主題
echarts.registerTheme('bootstrap', createTheme());
const chart = echarts.init(element, 'bootstrap');
```

## 故障排除

### 1. 常見問題

#### 問題: 圖表無法顯示
```javascript
// 檢查清單:
console.log('ECharts loaded:', typeof echarts !== 'undefined');
console.log('Element exists:', document.getElementById('chart-id') !== null);
console.log('Data available:', data && data.length > 0);
console.log('Chart initialized:', chart !== null);

// 解決方案:
// 1. 確認 ECharts CDN 載入成功
// 2. 檢查容器元素存在且有設定高度
// 3. 驗證資料格式正確
// 4. 檢查 JavaScript 錯誤
```

#### 問題: 圖表大小異常
```javascript
// 常見原因:
// 1. 容器元素沒有明確的高度
// 2. 初始化時容器隱藏 (display: none)
// 3. 響應式調整未正確觸發

// 解決方案:
// 1. 設定容器 CSS 高度
#chart-container {
    height: 400px;
    width: 100%;
}

// 2. 延遲初始化或強制重新計算
setTimeout(() => {
    chart.resize();
}, 100);

// 3. 監聽容器大小變化
const resizeObserver = new ResizeObserver(() => {
    chart.resize();
});
resizeObserver.observe(chartElement);
```

#### 問題: 資料更新異常
```javascript
// 錯誤做法:
chart.setOption(newData);  // 可能導致配置丟失

// 正確做法:
chart.setOption(newData, false, true);  // 合併配置並動畫更新

// 或完全重新設定:
chart.clear();
chart.setOption(fullOptions);
```

### 2. 除錯工具

```javascript
// 開發模式除錯工具
function debugChart(chart, data) {
    if (process.env.NODE_ENV === 'development') {
        window.chartDebug = {
            chart: chart,
            data: data,
            option: chart.getOption(),
            resize: () => chart.resize(),
            refresh: (newData) => chart.setOption(newData)
        };
        console.log('Chart debug tools available at window.chartDebug');
    }
}

// 效能監控
function monitorChartPerformance(chart) {
    const startTime = performance.now();
    
    chart.on('finished', () => {
        const endTime = performance.now();
        console.log(`Chart render time: ${endTime - startTime}ms`);
    });
}
```

### 3. 瀏覽器相容性

```javascript
// 檢查瀏覽器支援
function checkBrowserSupport() {
    const features = {
        canvas: !!document.createElement('canvas').getContext,
        svg: !!(document.createElementNS && document.createElementNS('http://www.w3.org/2000/svg', 'svg').createSVGRect),
        webgl: !!window.WebGLRenderingContext
    };
    
    if (!features.canvas && !features.svg) {
        console.warn('Browser does not support canvas or SVG');
        return false;
    }
    
    return true;
}

// 降級處理
if (!checkBrowserSupport()) {
    // 顯示靜態圖片或表格替代
    document.getElementById('chart-container').innerHTML = 
        '<div class="alert alert-warning">Your browser does not support interactive charts. Please upgrade your browser.</div>';
}
```

---

## 總結

MVC Shopping 專案的 ECharts 實作展現了現代 Web 應用中資料視覺化的最佳實踐。透過完整的 MVC 架構整合、響應式設計、以及豐富的互動功能，為管理者提供了直觀且實用的資料分析工具。

### 主要優勢
- **完整整合**: 與 Flask MVC 架構無縫整合
- **即時資料**: 直接從資料庫查詢最新統計
- **響應式設計**: 支援各種裝置和螢幕尺寸
- **高度客製化**: 符合 Bootstrap 主題風格
- **效能優化**: 合理的資料查詢和前端渲染策略
- **易於擴展**: 清晰的架構便於新增更多圖表

### 擴展方向
1. **更多圖表類型**: 圓餅圖、散點圖、熱力圖等
2. **時間範圍選擇**: 動態調整分析時間範圍
3. **即時更新**: WebSocket 或 AJAX 輪詢自動更新
4. **資料匯出**: 圖表轉為圖片或 PDF
5. **進階分析**: 趨勢預測、同比分析等
6. **使用者自訂**: 允許使用者選擇顯示的指標

這份手冊為開發者提供了完整的 ECharts 實作指南，從基礎概念到進階應用，確保能夠有效維護和擴展現有的資料視覺化功能。
