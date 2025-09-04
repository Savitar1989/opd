import sqlite3, logging
from typing import List, Dict, Optional
from config import DB_NAME
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self) -> None:
        self.init_db()

    def init_db(self) -> None:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_name TEXT NOT NULL,
            restaurant_address TEXT NOT NULL,
            phone_number TEXT,
            order_details TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            group_name TEXT,
            message_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            delivery_partner_id INTEGER,
            delivery_partner_name TEXT,
            delivery_partner_username TEXT,
            estimated_time INTEGER,
            accepted_at TIMESTAMP,
            picked_up_at TIMESTAMP,
            delivered_at TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )""")
        conn.commit()
        conn.close()
        logger.info('DB initialized')

    def save_order(self, item: Dict) -> int:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""INSERT INTO orders
            (restaurant_name, restaurant_address, phone_number, order_details, group_id, group_name, message_id)
            VALUES (?,?,?,?,?,?,?)""",
            (item.get('restaurant_name',''),
             item.get('restaurant_address',''),
             item.get('phone_number',''),
             item.get('order_details',''),
             item.get('group_id'),
             item.get('group_name'),
             item.get('message_id')))
        oid = cur.lastrowid
        conn.commit()
        conn.close()
        return oid

    def get_open_orders(self) -> List[Dict]:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""SELECT id, restaurant_name, restaurant_address, phone_number, order_details,
            group_id, group_name, created_at, status, delivery_partner_id, estimated_time
            FROM orders
            WHERE status IN ('pending','accepted','picked_up')
            ORDER BY created_at DESC""")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_order_status(self, order_id: int, status: str,
                            partner_id: int | None = None,
                            partner_name: str | None = None,
                            partner_username: str | None = None,
                            estimated_time: int | None = None) -> None:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""UPDATE orders
            SET status = ?,
                delivery_partner_id = COALESCE(?, delivery_partner_id),
                delivery_partner_name = COALESCE(?, delivery_partner_name),
                delivery_partner_username = COALESCE(?, delivery_partner_username),
                estimated_time = COALESCE(?, estimated_time),
                accepted_at = CASE WHEN ?='accepted' THEN CURRENT_TIMESTAMP ELSE accepted_at END,
                picked_up_at = CASE WHEN ?='picked_up' THEN CURRENT_TIMESTAMP ELSE picked_up_at END,
                delivered_at = CASE WHEN ?='delivered' THEN CURRENT_TIMESTAMP ELSE delivered_at END
            WHERE id = ?""",
            (status, partner_id, partner_name, partner_username, estimated_time,
             status, status, status, order_id))
        conn.commit()
        conn.close()

    def get_partner_addresses(self, partner_id: int, status: str):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""SELECT id, restaurant_address, group_name FROM orders
            WHERE delivery_partner_id = ? AND status = ? ORDER BY created_at""", (partner_id, status))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_partner_orders(self, partner_id: int, status: str):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""SELECT id, restaurant_name, restaurant_address, phone_number, order_details,
            group_id, group_name, created_at, status, estimated_time
            FROM orders
            WHERE status=? AND delivery_partner_id=?
            ORDER BY created_at DESC""", (status, partner_id))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_orders_by_status(self, status: str):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if status == 'pending':
            cur.execute("""SELECT id, restaurant_name, restaurant_address, phone_number, order_details,
                group_id, group_name, created_at, status FROM orders WHERE status='pending' ORDER BY created_at DESC""")
        else:
            cur.execute("""SELECT id, restaurant_name, restaurant_address, phone_number, order_details,
                group_id, group_name, created_at, status, estimated_time FROM orders WHERE status=? ORDER BY created_at DESC""", (status,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
