import json, logging, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN, WEBAPP_URL
from db import DatabaseManager
logger = logging.getLogger(__name__)
notification_queue = asyncio.Queue()
db = DatabaseManager()

def validate_telegram_data(init_data: str):
    try:
        if not init_data:
            return None
        data = {}
        for part in (init_data or '').split('&'):
            if '=' in part:
                k,v = part.split('=',1); data[k]=v
        if 'user' in data:
            import urllib.parse
            return json.loads(urllib.parse.unquote(data['user']))
    except Exception as e:
        logger.error('validate error: %s', e)
    return None

class RestaurantBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        app = self.app
        app.add_handler(CommandHandler('start', self.start_cmd))
        app.add_handler(CommandHandler('help', self.help_cmd))
        app.add_handler(CommandHandler('register', self.register_group))
        app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, self.handle_group_message))
        if app.job_queue:
            app.job_queue.run_repeating(self.process_notifications, interval=3)

    async def process_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        processed = 0
        while processed < 5:
            try:
                item = notification_queue.get_nowait()
            except Exception:
                break
            try:
                await context.bot.send_message(chat_id=item['chat_id'], text=item.get('text',''), parse_mode='Markdown')
            except Exception as e:
                logger.error('notify fail: %s', e)
            processed += 1

    def send_notification(self, chat_id:int, text:str):
        try:
            notification_queue.put_nowait({'chat_id': chat_id, 'text': text})
        except Exception as e:
            logger.error('queue put fail: %s', e)

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if update.effective_chat.type == 'private':
            kb = InlineKeyboardMarkup([[InlineKeyboardButton('🚚 Elérhető rendelések', web_app=WebAppInfo(url=WEBAPP_URL))]])
            await update.message.reply_text(f'Üdv, {user.first_name}! Nyisd meg a futár felületet:', reply_markup=kb)
        else:
            await update.message.reply_text('Használd a /register parancsot a csoport regisztrálásához.')

    def parse_order_message(self, text: str):
        lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
        info = {}
        def after_colon(s): return s.split(':',1)[1].strip() if ':' in s else ''
        for ln in lines:
            low = ln.lower()
            if low.startswith('cím:') or low.startswith('cim:'):
                info['address'] = after_colon(ln)
            elif low.startswith('telefonszám:') or low.startswith('telefon:'):
                info['phone'] = after_colon(ln)
            elif low.startswith('megjegyzés:') or low.startswith('megjegyzes:'):
                info['details'] = after_colon(ln)
        if info.get('address'):
            info.setdefault('phone',''); info.setdefault('details','')
            return info
        return None

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ('group','supergroup'):
            return
        parsed = self.parse_order_message(update.message.text or '')
        if not parsed:
            return
        gid = update.effective_chat.id
        gname = update.effective_chat.title or 'Ismeretlen'
        item = {
            'restaurant_name': gname,
            'restaurant_address': parsed['address'],
            'phone_number': parsed.get('phone',''),
            'order_details': parsed.get('details',''),
            'group_id': gid,
            'group_name': gname,
            'message_id': update.message.message_id
        }
        oid = db.save_order(item)
        await update.message.reply_text(f'✅ Rendelés rögzítve. ID: #{oid}')
