import hashlib
import urllib.parse
import time
from datetime import datetime
import json

class ECPayService:
    """綠界電子金流服務"""
    
    def __init__(self, merchant_id, hash_key, hash_iv, is_test=True):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.is_test = is_test
        
        # API URLs
        if is_test:
            self.api_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
        else:
            self.api_url = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"
    
    def generate_check_mac_value(self, params):
        """產生檢查碼"""
        # 移除 CheckMacValue 參數
        if 'CheckMacValue' in params:
            del params['CheckMacValue']
        
        # 參數排序
        sorted_params = sorted(params.items())
        
        # 組合參數字串
        query_string = '&'.join([f"{key}={value}" for key, value in sorted_params])
        
        # 加上 HashKey 和 HashIV
        query_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"
        
        # URL encode
        query_string = urllib.parse.quote_plus(query_string).lower()
        
        # 產生 SHA256 雜湊
        check_mac_value = hashlib.sha256(query_string.encode('utf-8')).hexdigest().upper()
        
        return check_mac_value
    
    def create_order(self, order_data):
        """建立訂單"""
        # 基本參數
        params = {
            'MerchantID': self.merchant_id,
            'MerchantTradeNo': order_data['merchant_trade_no'],
            'MerchantTradeDate': order_data['merchant_trade_date'],
            'PaymentType': 'aio',
            'TotalAmount': order_data['total_amount'],
            'TradeDesc': order_data['trade_desc'],
            'ItemName': order_data['item_name'],
            'ReturnURL': order_data['return_url'],
            'ChoosePayment': 'Credit',  # Credit card only
            'OrderResultURL': order_data.get('order_result_url', ''),
            'ClientBackURL': order_data.get('client_back_url', ''),
            'NeedExtraPaidInfo': 'Y',
            'IgnorePayment': '',  # 不忽略任何付款方式
            'PlatformID': '',  # 平台商代號
            'InvoiceMark': 'N',  # 不開立發票
            'CustomField1': order_data.get('custom_field1', ''),
            'CustomField2': order_data.get('custom_field2', ''),
            'CustomField3': order_data.get('custom_field3', ''),
            'CustomField4': order_data.get('custom_field4', ''),
        }
        
        # 產生檢查碼
        params['CheckMacValue'] = self.generate_check_mac_value(params)
        
        return params
    
    def verify_check_mac_value(self, params):
        """驗證檢查碼"""
        received_check_mac = params.get('CheckMacValue', '')
        calculated_check_mac = self.generate_check_mac_value(params.copy())
        
        return received_check_mac == calculated_check_mac
    
    def format_trade_date(self, date_obj=None):
        """格式化交易日期"""
        if date_obj is None:
            date_obj = datetime.now()
        return date_obj.strftime('%Y/%m/%d %H:%M:%S')
    
    def generate_merchant_trade_no(self, order_id):
        """產生特店訂單編號"""
        timestamp = int(time.time())
        return f"EC{order_id:06d}{timestamp}"

# 測試環境設定 (根據綠界官方測試資料)
ECPAY_TEST_CONFIG = {
    'merchant_id': '3002607',  # 測試環境特店編號
    'hash_key': 'pwFHCqoQZGmho4w6',  # 測試環境 HashKey
    'hash_iv': 'EkRm7iFT261dpevs',   # 測試環境 HashIV
    'is_test': True
}

# 正式環境設定 (需要申請)
ECPAY_PROD_CONFIG = {
    'merchant_id': '',  # 正式環境特店編號
    'hash_key': '',     # 正式環境 HashKey
    'hash_iv': '',      # 正式環境 HashIV
    'is_test': False
}

# 測試信用卡資料 (根據綠界官方測試資料)
ECPAY_TEST_CARDS = {
    'domestic': {
        'card_number': '4311-9511-1111-1111',
        'security_code': '任意三碼',
        'expiry_date': '12/2025',  # 需大於當前日期
        'description': '國內信用卡測試卡號'
    },
    'domestic_2': {
        'card_number': '4311-9522-2222-2222',
        'security_code': '任意三碼',
        'expiry_date': '12/2025',
        'description': '國內信用卡測試卡號2'
    },
    'overseas': {
        'card_number': '4000-2011-1111-1111',
        'security_code': '任意三碼',
        'expiry_date': '12/2025',
        'description': '海外信用卡測試卡號'
    },
    'amex_domestic': {
        'card_number': '3403-532780-80900',
        'security_code': '任意四碼',
        'expiry_date': '12/2025',
        'description': '美國運通國內測試卡號'
    },
    'amex_overseas': {
        'card_number': '3712-222222-22222',
        'security_code': '任意四碼',
        'expiry_date': '12/2025',
        'description': '美國運通海外測試卡號'
    },
    'installment': {
        'card_number': '4938-1777-7777-7777',
        'security_code': '任意三碼',
        'expiry_date': '12/2025',
        'description': '圓夢彈性分期測試卡號'
    }
}

# 3D驗證測試資料
ECPAY_3D_VERIFICATION = {
    'sms_code': '1234',  # 測試環境固定簡訊驗證碼
    'description': '測試環境3D驗證簡訊固定為1234'
}
