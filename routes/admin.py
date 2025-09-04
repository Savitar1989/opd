from flask import Blueprint, request, render_template_string
from config import ADMIN_USER_IDS
from utils.telegram import validate_telegram_data
from db import DatabaseManager
bp = Blueprint('admin', __name__)
db = DatabaseManager()
ADMIN_HTML = r"""
<!doctype html>
<html lang="hu">
<head><meta charset="utf-8"><title>Admin</title></head>
<body>
  <h1>Admin statisztika</h1>
  <h2>Heti futár bontás</h2>
  <table border="1">
    <tr><th>Hét</th><th>Futár</th><th>Darab</th><th>Átlag idő (perc)</th></tr>
    {% for r in weekly_courier %}
    <tr>
      <td>{{ r.week }}</td>
      <td>{{ r.courier_name or r.delivery_partner_id }}</td>
      <td>{{ r.cnt }}</td>
      <td>{{ r.avg_min }}</td>
    </tr>
    {% endfor %}
  </table>

  <h2>Étterem bontás</h2>
  <table border="1">
    <tr><th>Hét</th><th>Csoport</th><th>Darab</th><th>Átlag idő</th></tr>
    {% for r in weekly_restaurant %}
    <tr>
      <td>{{ r.week }}</td>
      <td>{{ r.group_name }}</td>
      <td>{{ r.cnt }}</td>
      <td>{{ r.avg_min }}</td>
    </tr>
    {% endfor %}
  </table>

  <h2>Részletes kézbesítések</h2>
  <table border="1">
    <tr><th>Dátum</th><th>Futár</th><th>Csoport</th><th>Cím</th><th>Idő (perc)</th></tr>
    {% for r in deliveries %}
    <tr>
      <td>{{ r.delivered_at }}</td>
      <td>{{ r.courier_name or r.delivery_partner_id }}</td>
      <td>{{ r.group_name }}</td>
      <td>{{ r.restaurant_address }}</td>
      <td>{{ r.min }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""\n\n@bp.route('/admin')
def admin_page():
    init_data = request.args.get('init_data','')
    user = validate_telegram_data(init_data)
    if not user or user.get('id') not in ADMIN_USER_IDS:
        return '🚫 Hozzáférés megtagadva', 403
    conn = __import__('sqlite3').connect(__import__('config').DB_NAME)
    conn.row_factory = __import__('sqlite3').Row
    cur = conn.cursor()
    cur.execute("""SELECT delivered_at, delivery_partner_id, COALESCE(delivery_partner_name,'') AS courier_name,
                   group_name, restaurant_address,
                   ROUND((julianday(delivered_at)-julianday(accepted_at))*24*60,1) AS min
                   FROM orders
                   WHERE delivered_at IS NOT NULL AND accepted_at IS NOT NULL
                   ORDER BY delivered_at DESC
                   LIMIT 500""")
    deliveries = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template_string(ADMIN_HTML, weekly_courier=[], weekly_restaurant=[], deliveries=deliveries)

@bp.route('/api/is_admin', methods=['POST'])
def api_is_admin():
    data = request.json or {}
    user = validate_telegram_data(data.get('initData',''))
    if not user:
        return {'ok': False, 'admin': False}, 401
    return {'ok': True, 'admin': user.get('id') in ADMIN_USER_IDS}
