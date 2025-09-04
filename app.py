import threading, logging
from flask import Flask
from config import DEBUG
from routes.orders import bp as orders_bp
from routes.courier import bp as courier_bp
from routes.admin import bp as admin_bp
from utils.telegram import RestaurantBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(orders_bp)
app.register_blueprint(courier_bp)
app.register_blueprint(admin_bp)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)

if __name__ == '__main__':
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    bot = RestaurantBot()
    bot.app.run_polling(allowed_updates=None)
