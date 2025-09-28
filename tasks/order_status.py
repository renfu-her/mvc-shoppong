from datetime import datetime
from flask import current_app

from app import db
from models.order import Order
from utils.ecpay import ECPayService, ECPAY_TEST_CONFIG

SUCCESS_CODES = {'1'}


def _end_of_day(dt: datetime) -> datetime:
    if dt is None:
        return datetime.utcnow()
    return dt.replace(hour=23, minute=59, second=59, microsecond=0)


def _should_mark_failed(order: Order, now: datetime) -> bool:
    return now >= _end_of_day(order.created_at)


def _query_gateway(order: Order, service: ECPayService):
    merchant_trade_no = order.transaction_id or order.order_number
    if not merchant_trade_no:
        return None
    try:
        return service.query_trade_info(merchant_trade_no)
    except Exception as exc:
        current_app.logger.warning('ECPay query failed for order %s: %s', order.id, exc)
        return None


def sync_pending_orders(limit: int = 50):
    service = ECPayService(**ECPAY_TEST_CONFIG)
    now = datetime.utcnow()

    pending = Order.query.filter(Order.payment_status == 'pending').order_by(Order.created_at.asc()).limit(limit).all()
    if not pending:
        current_app.logger.debug('No pending orders to sync')
        return 0

    updates = 0

    for order in pending:
        if _should_mark_failed(order, now):
            order.payment_status = 'failed'
            order.status = 'failed'
            db.session.add(order)
            updates += 1
            continue

        payload = _query_gateway(order, service)
        if not payload:
            continue

        rtn_code = payload.get('RtnCode')
        if rtn_code in SUCCESS_CODES:
            order.payment_status = 'paid'
            order.status = 'processing'
            order.ecpay_trade_no = payload.get('TradeNo') or order.ecpay_trade_no
            order.transaction_id = payload.get('MerchantTradeNo') or order.transaction_id
            db.session.add(order)
            updates += 1
        elif _should_mark_failed(order, now):
            order.payment_status = 'failed'
            order.status = 'failed'
            db.session.add(order)
            updates += 1

    if updates:
        db.session.commit()
        current_app.logger.info('Synced %s pending orders via ECPay.', updates)

    return updates
