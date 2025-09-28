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

    pending = (Order.query
               .filter(Order.payment_status == 'pending')
               .order_by(Order.created_at.asc())
               .limit(limit)
               .all())

    results = []
    updated = 0
    processed = 0
    changed = False

    if not pending:
        return {'updated': 0, 'processed': 0, 'results': results}

    for order in pending:
        processed += 1
        info = {
            'order_id': order.id,
            'order_number': order.order_number,
            'previous_payment_status': order.payment_status,
            'previous_status': order.status,
            'new_payment_status': order.payment_status,
            'new_status': order.status,
            'action': 'skipped',
            'message': None,
            'payload': None,
        }

        if _should_mark_failed(order, now):
            order.payment_status = 'failed'
            order.status = 'failed'
            info['action'] = 'auto_failed'
            info['message'] = 'Past daily cutoff, marked as failed'
            db.session.add(order)
            updated += 1
            changed = True
            info['new_payment_status'] = order.payment_status
            info['new_status'] = order.status
            results.append(info)
            continue

        payload = _query_gateway(order, service)
        info['payload'] = payload
        if not payload:
            info['message'] = 'No response from gateway'
            results.append(info)
            continue

        rtn_code = payload.get('RtnCode')
        trade_status = payload.get('TradeStatus')
        trade_no = payload.get('TradeNo')
        merchant_trade_no = payload.get('MerchantTradeNo')

        if rtn_code in SUCCESS_CODES or trade_status == '1':
            info['action'] = 'marked_paid'
            info['message'] = payload.get('RtnMsg', 'Payment confirmed')
            order.payment_status = 'paid'
            order.status = 'processing'
            if trade_no:
                order.ecpay_trade_no = trade_no
            if merchant_trade_no:
                order.transaction_id = merchant_trade_no
            info['new_payment_status'] = order.payment_status
            info['new_status'] = order.status
            db.session.add(order)
            updated += 1
            changed = True
        else:
            info['action'] = 'pending'
            info['message'] = payload.get('RtnMsg', 'Still pending')
            if _should_mark_failed(order, now):
                order.payment_status = 'failed'
                order.status = 'failed'
                info['action'] = 'auto_failed'
                info['message'] = 'Status pending past cutoff, marked failed'
                info['new_payment_status'] = order.payment_status
                info['new_status'] = order.status
                db.session.add(order)
                updated += 1
                changed = True
            else:
                info['new_payment_status'] = order.payment_status
                info['new_status'] = order.status

        results.append(info)

    if changed:
        db.session.commit()
        current_app.logger.info('Synced %s pending orders via ECPay.', updated)

    return {
        'updated': updated,
        'processed': processed,
        'results': results,
    }
