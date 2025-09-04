from flask import Blueprint, jsonify, request
from db import DatabaseManager
from utils.telegram import validate_telegram_data
db = DatabaseManager()
bp = Blueprint('courier', __name__)

@bp.route('/api/orders_by_status')
def api_orders_by_status():
    status = (request.args.get('status') or '').strip()
    if not status:
        return jsonify([])
    rows = db.get_orders_by_status(status)
    return jsonify(rows)

@bp.route('/api/my_orders', methods=['POST'])
def api_my_orders():
    data = request.json or {}
    user = validate_telegram_data(data.get('initData',''))
    if not user:
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    status = (data.get('status') or '').strip()
    if status not in ('accepted','picked_up','delivered'):
        return jsonify({'ok': True, 'orders': []})
    rows = db.get_partner_orders(user['id'], status)
    return jsonify({'ok': True, 'orders': rows})
