import requests
import os
import json
import base64
import re
import aiohttp
from datetime import datetime, time
from zoneinfo import ZoneInfo
from cryptography.fernet import Fernet
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

MAIN_API = os.getenv('Main_API')
CAR_API = os.getenv('Car_API')
OIL = os.getenv('Oil')
ADMIN_ID = int(os.getenv('Admin_ID'))
GIT = os.getenv('GIT_Token')
BOT_TOKEN = os.getenv('BOT_TOKEN')
KEY = os.getenv('Key')
VERSION = '2.0.2'

class Arz:
    def __init__(self):
        self.tehran = ZoneInfo("Asia/Tehran")
        self.fernet = Fernet(KEY)
        self.set = self.load_hours()

        self.keyboard = [
            ['💱 خلاصه قیمت ها 🪙'],
            ['🪙 قیمت سکه 🪙', '💰 قیمت طلا 💰'],
            ['💱 قیمت ارز ها 💱'],
            ['🚗 خودرو های وارداتی 🚗', '🚗 خودرو های داخلی 🚗'],
            ['🧮 تبدیل ارز به ریال 🧮']
        ]

        self.admin_keyborad = [
            ['💱 خلاصه قیمت ها 🪙'],
            ['🪙 قیمت سکه 🪙', '💰 قیمت طلا 💰'],
            ['💱 قیمت ارز ها 💱'],
            ['🚗 خودرو های وارداتی 🚗', '🚗 خودرو های داخلی 🚗'],
            ['🧮 تبدیل ارز به ریال 🧮'],
            ['⚙️ پنل مدیریت ⚙️']
        ]

        self.carkeyboard = [
            ['هیوندای', 'کیا', 'تویوتا'],
            ['بنز', 'بی ام و', 'فولکس واگن'],
            ['مزدا', 'ولوو', 'آئودی'],
            ['نیسان', 'هوندا', 'میتسوبیشی'],
            ['MG', 'BYD', 'GAC'],
            ['چانگان', 'ونوسیا', 'اشکودا'],
            ['🔙 بازگشت']
        ]

        self.dakhelikeyboard = [
            ['سایپا', 'ایران خودرو'],
            ['مدیران خودرو', 'کرمان موتور'],
            ['سایر', 'بهمن موتور'], 
            ['🔙 بازگشت']
        ]

    def load_state(self) -> list:
        url = 'https://raw.githubusercontent.com/Sinaksh0/warp-config/refs/heads/main/users.json'
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return []

            body = response.text.strip()

            try:
                decrypt = self.fernet.decrypt(body).decode()
                data = json.loads(decrypt)
            except ValueError:
                try:
                    decoded = base64.b64decode(body)
                    decrypt = self.fernet.decrypt(decoded).decode('utf-8')
                    data = json.loads(decrypt)
                except Exception:
                    return []

            return data["users"]
        except requests.RequestException:
            return []

    def load_price(self) -> dict:
        url = 'https://raw.githubusercontent.com/Sinaksh0/warp-config/refs/heads/main/prices.json'

        response = requests.get(url, timeout=15)
        return response.json()

    def load_hours(self) -> list:
        url = 'https://raw.githubusercontent.com/Sinaksh0/warp-config/refs/heads/main/hours.json'

        response = requests.get(url, timeout=15).text
        result = json.loads(response)
        return result
    
    def upload_price(self, prices):
        url = 'https://api.github.com/repos/Sinaksh0/warp-config/contents/prices.json'

        headers = {
            'Authorization': f'Bearer {GIT}',
            'Accept': 'application/vnd.github+json'
        }

        data = json.dumps(prices, ensure_ascii=False).encode()
        encoded = base64.b64encode(data).decode('utf-8')

        response = requests.get(url, headers=headers, timeout=20)

        body = {
            'message': 'Auto updating prices',
            'content': encoded,
            'branch': 'main'
        }

        if response.status_code == 200:
            body['sha'] = response.json().get('sha')

        requests.put(url, headers=headers, json=body, timeout=20)
        return
    
    def upload_github(self, data):
        if not GIT:
            raise RuntimeError("GITHUB_TOKEN is not set")

        url = 'https://api.github.com/repos/Sinaksh0/warp-config/contents/users.json'
        headers = {
            "Authorization": f"Bearer {GIT}",
            "Accept": "application/vnd.github+json"
        }

        payload = json.dumps({
            "count": len(data),
            "users": data
            }, 
            ensure_ascii=False).encode('utf-8')
        encrypt = self.fernet.encrypt(payload)
        encoded = base64.b64encode(encrypt).decode("utf-8")

        resp = requests.get(url, headers=headers, timeout=20)

        body = {
            "message": "Auto updating users",
            "content": encoded,
            "branch": "main"
        }

        if resp.status_code == 200:
            body["sha"] = resp.json().get("sha")

        requests.put(url, headers=headers, json=body, timeout=20)
        return

    def upload_hours(self, hours):
        url = 'https://api.github.com/repos/Sinaksh0/warp-config/contents/hours.json'

        headers = {
            'Authorization': f'Bearer {GIT}',
            'Accept': 'application/vnd.github+json'
        }

        data = json.dumps(hours, ensure_ascii=False).encode()
        encoded = base64.b64encode(data).decode('utf-8')

        response = requests.get(url, headers=headers, timeout=20)

        body = {
            'message': 'Auto updating hours',
            'content': encoded,
            'branch': 'main'
        }

        if response.status_code == 200:
            body['sha'] = response.json().get('sha')

        requests.put(url, headers=headers, json=body, timeout=20)
        return
    
    def check_user(self, name: str, chat_id: int):
        users = self.load_state()
        flag = True
        for id in users:
            if chat_id == id['ID']:
                flag = False
                break
        
        if flag:
            users.append({
                "Name": name,
                "ID": chat_id
            })
            self.upload_github(users)
        return
    
    async def get_arz(self, url):
        response = requests.get(url, timeout=10).json()
        return response

    async def get_car(self, url):
        response = requests.get(url, timeout=10).json()
        return response['cars']

    async def check_update(self, context: ContextTypes.DEFAULT_TYPE):
        users = self.load_state()
        if not users:
            return

        new_users = []
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['ID'],
                    text=f'✨ نسخه‌ی جدید v{VERSION} منتشر شد.\n\n'
                        '🔄 برای دریافت آخرین تغییرات، دستور زیر را بفرستید:\n'
                        '/update'
                )
                new_users.append(user)

            except Exception:
                pass

        if new_users != users:
            self.upload_github(new_users)

        return

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        user = update.effective_user
        chat_id = chat.id

        if chat.type == 'private' and user.id == ADMIN_ID:
            keyboard = self.admin_keyborad
        else:
            keyboard = self.keyboard

        if chat.type in ['group', 'supergroup']:
            name = chat.title
        else:
            name = user.full_name

        self.check_user(name, chat_id)

        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f60d']
            )
        
        html = f"""
            <p>سلام <strong>{name}</strong> 👋 به قیمت‌نما خوش اومدی؛ بازار رو با چند لمس دنبال کن.</p>
            
            <h3>✨ از اینجا شروع کن</h3>
            <ul>
                <li>💱 نرخ ارزها و قیمت طلا</li>
                <li>🪙 قیمت سکه‌ها و حباب بازار</li>
                <li>🚗 قیمت روز خودروهای داخلی و وارداتی</li>
                <li>🧮 تبدیل سریع ارز و طلا</li>
            </ul>

            <tg-button-row>
                <tg-button type="url" style="success" url="https://t.me/SI_KSH">پشتیبانی ربات ↗</tg-button>
            </tg-button-row>
        """

        await self.send_rich_message(chat_id, html)
        await update.message.reply_text("👇 یکی از گزینه‌های منو رو انتخاب کن تا شروع کنیم.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        
        return

    async def update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        user = update.effective_user
        chat_id = chat.id

        if chat.type == 'private' and user.id == ADMIN_ID:
            keyboard = self.admin_keyborad
        else:
            keyboard = self.keyboard

        if chat.type in ['group', 'supergroup']:
            name = chat.title
        else:
            name = user.full_name

        self.check_user(name, chat_id)

        await self.reaction(update, context)

        html = f"""
        <h1>نسخه v{VERSION} ✨</h1>

        <h3>✨ تغییرات این نسخه</h3>
        <ul>
            <li>📊 نمایش جدولی قیمت‌ها برای مقایسه‌ی راحت‌تر</li>
            <li>🗓️ دیدن ساعت‌های گزارش فعال با /myschedule</li>
        </ul>
        
        <ul>
            <li><input type="checkbox" checked><strong>تغییرات جدید با موفقیت انجام شد</strong></li>
        </ul>
        """

        await self.send_rich_message(chat_id, html)
        await update.message.reply_text('<b>✅ تغییرات نسخه‌ی جدید رو در پیام بالا ببین.</b>', 
            parse_mode='HTML', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)
        chat_id = update.effective_chat.id

        html = """
        <h3>📋 راهنمای سریع ربات</h3>
        <table bordered striped compact>
        <tr><th>🎯 کاربرد</th><th>⌨️ دستور</th></tr>
        <tr><td>🚀 شروع و نمایش منو</td><td>/start</td></tr>
        <tr><td>✨ تغییرات نسخه</td><td>/update</td></tr>
        <tr><td>⏰ تنظیم گزارش خودکار</td><td>/set</td></tr>
        <tr><td>🗓️ دیدن ساعت‌های فعال</td><td>/myschedule</td></tr>
        <tr><td>⏸️ توقف گزارش زمان‌بندی‌شده</td><td>/unset</td></tr>
        <tr><td>📨 پیام به مدیر</td><td>/send</td></tr>
        </table>
        """

        await self.send_rich_message(chat_id, html)

    async def set_hours(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)
        
        if len(context.args) == 0:
            await update.message.reply_text('⏰ ساعت‌های دریافت گزارش رو وارد کن. نمونه:\n/set 8:15 10:35 18 22')
            return

        hour = []
        minute = []
        for arg in context.args:
            try:
                if ":" in arg:
                    h, m = map(int, arg.split(":"))
                    hour.append(h)
                    minute.append(m)
                else:
                    h = int(arg)
                    hour.append(h)
                    minute.append(0)
            except ValueError:
                await update.message.reply_text('⚠️ ساعت و دقیقه باید عدد باشن؛ مثلاً 8:15.')
                return
        
        for h in hour:
            if not 0 <= h <=23:
                await update.message.reply_text("⚠️ ساعت رو بین 0 تا 23 وارد کن.")
                return

        for min in minute:
            if not 0 <= min < 60:
                await update.message.reply_text("⚠️ دقیقه رو بین 0 تا 59 وارد کن.")
                return
            
        job_name = f'chat_id_{update.effective_chat.id}'

        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        times = list(zip(hour, minute))
        for h, m in times:
            context.job_queue.run_daily(self.send_daily, time=time(h, m, tzinfo=self.tehran), chat_id=update.effective_chat.id, name=job_name)

        if update.effective_chat.type in ['group', 'supergroup']:
            name = update.effective_chat.title
        else:
            name = update.effective_user.full_name

        set_hour = self.load_hours()
        for set in set_hour:
            if set['ID'] == update.effective_chat.id:
                set['Hours'] = times
                break
        else:
            set_hour.append({
                'Name': name,
                'Hours': times,
                'ID': update.effective_chat.id,
                'job_name': job_name
            })

        self.upload_hours(set_hour)
        await update.message.reply_text(f'✅ گزارش خودکار با این ساعت‌ها تنظیم شد: {times}')
        return

    async def myschedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)
        user_hour = self.load_hours()

        flag = True
        for user in user_hour:
            if user['ID'] == update.effective_chat.id:
                text = '🗓️ <b>ساعت‌های گزارش خودکار شما:</b>\n\n'
                for hour, minute in user['Hours']:
                    text += f'🕒 {hour:02d}:{minute:02d}\n'
                flag = False
                break
            
        if flag:
            text = 'ℹ️ هنوز گزارشی زمان‌بندی نشده.\nبرای انتخاب ساعت‌ها، دستور /set رو بفرست.'

        await update.message.reply_text(text=text, parse_mode='HTML')
        
    async def unset_hours(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)

        job_name = f'chat_id_{update.effective_chat.id}'

        if not context.job_queue.get_jobs_by_name(job_name):
            await update.message.reply_text('ℹ️ گزارشی برای این گفتگو زمان‌بندی نشده که متوقفش کنیم.')
            return
        
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        set_hour = self.load_hours()

        for user in set_hour:
            if user['job_name'] == job_name:
                set_hour.remove(user)
                break

        self.upload_hours(set_hour)
        await update.message.reply_text('⏸️ ارسال خودکار گزارش برای این گفتگو متوقف شد.')
        return

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private' and update.effective_user.id != ADMIN_ID:
            return

        await self.reaction(update, context)
        
        self.inline_keyboard = [
            [InlineKeyboardButton('📊 تعداد کاربران 📊', callback_data='users')],
            [InlineKeyboardButton('📨 پیام همگانی 📨', callback_data='messages')]
        ]

        reply_markup = InlineKeyboardMarkup(self.inline_keyboard)
        await update.message.reply_text('⚙️ پنل مدیریت باز شد؛ یکی از گزینه‌ها رو انتخاب کن.',
                reply_markup=reply_markup)

    async def handle_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton('🔙 بازگشت', callback_data='back')]
        ]

        choose = query.data
        if choose == 'users':
            data = self.load_state()
            count = len(data)
            message = f'👥 کاربران ثبت‌شده: {count}\n'
            message += '📋 فهرست کاربران\n\n'
            for i, user in enumerate(data, start=1):
                message += (
                    f'{i}. {user['Name']} - {user['ID']}\n\n'
                )
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

        elif choose == 'messages':
            await query.edit_message_text('📨 برای ارسال پیام، دستور /manager رو با گیرنده و متن بفرست.\nنمونه: /manager all سلام', reply_markup=InlineKeyboardMarkup(keyboard))

        elif choose == 'back':
            await query.edit_message_text('⚙️ پنل مدیریت آماده است.',
                reply_markup=InlineKeyboardMarkup(self.inline_keyboard))

    async def send_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)

        text = update.message.text.strip() if update.message.text else ''
        if not text.startswith('/manager'):
            await update.message.reply_text('⚠️ قالب دستور درست نیست. یکی از این نمونه‌ها رو بفرست:\n/manager all سلام\n/manager 123456789 سلام')
            return

        rest = text[len('/manager'):].strip()
        if not rest:
            await update.message.reply_text('👤 گیرنده‌ی پیام رو مشخص کن. نمونه:\n/manager all سلام\n/manager 123456789 سلام')
            return

        target = rest.split()[0]
        msg = ' '.join(rest.split()[1:]).strip()

        if not msg:
            await update.message.reply_text('✍️ متن پیام رو هم بنویس. نمونه:\n/manager all سلام\n/manager 123456789 سلام')
            return

        if target.lower() == 'all':
            users = self.load_state()
            sent = 0
            failed = 0
            for user in users:
                chat_id = user.get('ID')
                if chat_id is None:
                    continue
                try:
                    await context.bot.send_message(chat_id=chat_id, text=msg)
                    sent += 1
                except Exception:
                    failed += 1
            await update.message.reply_text(f'📨 ارسال همگانی انجام شد؛ {sent} پیام موفق بود.' + (f' ⚠️ {failed} پیام ارسال نشد.' if failed else ' ✅'))
            return

        if target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
            try:
                chat_id = int(target)
                await context.bot.send_message(chat_id=chat_id, text=msg)
                await update.message.reply_text(f'✅ پیام با موفقیت به آیدی {chat_id} رسید.')
            except Exception as exc:
                await update.message.reply_text(f'❌ ارسال پیام به آیدی {target} ناموفق بود.\nجزئیات: {exc}')
            return

        await update.message.reply_text('⚠️ گیرنده رو با «all» یا یک آیدی عددی مشخص کن.\nنمونه: /manager all سلام')

    async def send_to_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reaction(update, context)
        
        text = update.message.text
        if '/send' not in text:
            await update.message.reply_text('⚠️ برای پیام به مدیر، متن رو با /send شروع کن.\nنمونه: /send سلام، یک پیام دارم.')
            return 

        if text == '/send':
            await update.message.reply_text('✍️ متن پیامت رو بعد از /send بنویس.\nنمونه: /send سلام، یک پیام دارم.')
            return
        
        msg = text.replace('/send', '')
        await context.bot.send_message(chat_id=ADMIN_ID, text=f'📨 پیام از {update.effective_user.full_name} ({update.effective_user.id}):\n\n{msg}')
        await update.message.reply_text('✅ پیامت برای مدیر فرستاده شد.')

    async def send_daily(self, context: ContextTypes.DEFAULT_TYPE):
        self.data = self.load_price()
        data = await self.get_arz(MAIN_API)
        oil = await self.get_arz(OIL)

        flag = False
        today = datetime.now(self.tehran).strftime('%m/%d/%Y')
        tether_data = self.data['tether'] if self.data['date'] == today else []
        usd_data = self.data['usd'] if self.data['date'] == today else []
        eur_data = self.data['eur'] if self.data['date'] == today else []
        emami_data = self.data['emami'] if self.data['date'] == today else []
        azadi_data = self.data['azadi'] if self.data['date'] == today else []
        tala_data = self.data['gold'] if self.data['date'] == today else []

        if self.data.get('date') != today:
            self.data['date'] = today


        tether = data['crypto_prices']['items'][0]
        dollar = data['currency_prices']['items'][0]
        eurro = data['currency_prices']['items'][1]
        seke_emami = data['gold_prices']['items'][2]
        seke = data['gold_prices']['items'][3]
        tala_18 = data['gold_prices']['items'][1]
        oil = oil['items'][0]

        if int(tether['price_toman']) not in tether_data:
            tether_data.append(int(tether['price_toman']))
            self.data['tether'] = tether_data
            flag = True

        if int(dollar['sell_price']['value']) not in usd_data:
            usd_data.append(int(dollar['sell_price']['value']))
            self.data['usd'] = usd_data
            flag = True

        if int(eurro['sell_price']['value']) not in eur_data:
            eur_data.append(int(eurro['sell_price']['value']))
            self.data['eur'] = eur_data
            flag = True

        if int(seke_emami['price']) not in emami_data:
            emami_data.append(int(seke_emami['price']))
            self.data['emami'] = emami_data
            flag = True

        if int(seke['price']) not in azadi_data:
            azadi_data.append(int(seke['price']))
            self.data['azadi'] = azadi_data
            flag = True

        if int(tala_18['price']) not in tala_data:
            tala_data.append(int(tala_18['price']))
            self.data['gold'] = tala_data
            flag = True

        tether_max = max(tether_data)
        tether_min = min(tether_data)
        usd_max = max(usd_data)
        usd_min = min(usd_data)
        eur_max = max(eur_data)
        eur_min = min(eur_data)
        emami_max = max(emami_data)
        emami_min = min(emami_data)
        azadi_max = max(azadi_data)
        azadi_min = min(azadi_data)
        tala_max = max(tala_data)
        tala_min = min(tala_data)

        html = f"""
        <h3>💱 گزارش خلاصه بازار 🪙</h3>
        <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

        <table bordered striped compact>
            <tr><th>عنوان</th><th>💵 نرخ فروش</th><th>⬆️ بیشینه</th><th>⬇️ کمینه</th><th>🫧 حباب</th></tr>
            <tr><td>\U0001f4b8 تتر</td><td>{int(tether['price_toman']):,}</td><td>{tether_max:,}</td><td>{tether_min:,}</td><td>---</td></tr>
            <tr><td>\U0001f4b5 دلار</td><td>{int(dollar['sell_price']['value']):,}</td><td>{usd_max:,}</td><td>{usd_min:,}</td><td>---</td></tr>
            <tr><td>💷 یورو</td><td>{int(eurro['sell_price']['value']):,}</td><td>{eur_max:,}</td><td>{eur_min:,}</td><td>---</td></tr>
            <tr><td>🪙 سکه امامی</td><td>{int(seke_emami['price']):,}</td><td>{emami_max:,}</td><td>{emami_min:,}</td><td>{int(seke_emami['bubble']['amount']):,}</td></tr>
            <tr><td>🪙 سکه بهار آزادی</td><td>{int(seke['price']):,}</td><td>{azadi_max:,}</td><td>{azadi_min:,}</td><td>{int(seke['bubble']['amount']):,}</td></tr>
            <tr><td>💰 طلای 18 عیار</td><td>{int(tala_18['price']):,}</td><td>{tala_max:,}</td><td>{tala_min:,}</td><td>{int(tala_18['bubble']['amount']):,}</td></tr>
            <tr><td>🛢️ {oil['name']}</td><td>{oil['price']} دلار</td><td>---</td><td>---</td><td>---</td></tr>
        </table>
        <tg-button-row>
            <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
        </tg-button-row>
        """

        if flag:
            self.upload_price(self.data)

        if context.job is not None:
            await self.send_rich_message(context.job.chat_id, html)
            return
        
        return html

    async def send_rich_message(self, chat_id: int, html_content: str):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendRichMessage"
        payload = {
            "chat_id": chat_id,
            "rich_message": {
                "html": html_content.strip(),
                "is_rtl": True
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                return await response.json()

    async def reaction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
            message_id=update.message.message_id,
            reaction=['\U0001f44d']
        )
        return
    
    async def take_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        self.data = self.load_price()

        if text is None:
            return
        
        try:
            if text == '💱 قیمت ارز ها 💱':
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال دریافت قیمت‌ها...')
                data = await self.get_arz(MAIN_API)
                data = data['currency_prices']['items']
                dollar = data[0]
                eurro = data[1]
                eur_rate = eurro["usd_rate"]["value"]
                canada = data[6]
                can_rate = canada["usd_rate"]["value"]
                derham = data[2]
                der_rate = derham["usd_rate"]["value"]
                lir = data[3]
                lir_rate = lir["usd_rate"]["value"]
                pond = data[4]
                pond_rate = pond["usd_rate"]["value"]
                dinar = data[9]
                dinar_rate = dinar["usd_rate"]["value"]
                oman = data[15]
                oman_rate = oman["usd_rate"]["value"]
                arab = data[19]
                arab_rate = arab["usd_rate"]["value"]

                await sent.edit_text('📨 در حال آماده‌سازی گزارش...')

                html = f"""
                <h3>💱 نرخ روز ارزها</h3>
                <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

                <table bordered striped compact>
                    <tr><th>نماد</th><th>💱 ارز</th><th>\U0001f4b0 نرخ فروش</th><th>💵 نسبت به دلار</tr>
                    <tr><td>🇺🇸</td><td>دلار آمریکا</td><td>{int(dollar['sell_price']['value']):,}</td><td>---</td></tr>
                    <tr><td>🇪🇺</td><td>یورو اروپا</td><td>{int(eurro['sell_price']['value']):,}</td><td>{eur_rate}</td></tr>
                    <tr><td>🇨🇦</td><td>دلار کانادا</td><td>{int(canada['sell_price']['value']):,}</td><td>{can_rate}</td></tr>
                    <tr><td>🇦🇪</td><td>درهم امارات</td><td>{int(derham['sell_price']['value']):,}</td><td>{der_rate}</td></tr>
                    <tr><td>🇹🇷</td><td>لیر ترکیه</td><td>{int(lir['sell_price']['value']):,}</td><td>{lir_rate}</td></tr>
                    <tr><td>🇬🇧</td><td>پوند انگلیس</td><td>{int(pond['sell_price']['value']):,}</td><td>{pond_rate}</td></tr>
                    <tr><td>🇮🇶</td><td>صد دینار عراق</td><td>{int(dinar['sell_price']['value']):,}</td><td>{dinar_rate}</td></tr>
                    <tr><td>🇴🇲</td><td>ریال عمان</td><td>{int(oman['sell_price']['value']):,}</td><td>{oman_rate}</td></tr>
                    <tr><td>🇸🇦</td><td>ریال عربستان</td><td>{int(arab['sell_price']['value']):,}</td><td>{arab_rate}</td></tr>
                </table>
                <tg-button-row>
                    <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
                </tg-button-row>
                """
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, html)
                return
            
            elif text == '🪙 قیمت سکه 🪙':
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال دریافت قیمت سکه‌ها...')
                data = await self.get_arz(MAIN_API)
                data = data['gold_prices']['items']

                today = datetime.now(self.tehran).strftime('%m/%d/%Y')
                emami_data = self.data['emami'] if self.data['date'] == today else []
                azadi_data = self.data['azadi'] if self.data['date'] == today else []
                nim_data = self.data['nim'] if self.data['date'] == today else []
                rob_data = self.data['rob'] if self.data['date'] == today else []

                if self.data.get('date') != today:
                    self.data['date'] = today

                message = "🪙 گزارش قیمت سکه\n\n"
                emami = data[2]
                azadi = data[3]
                nim = data[4]
                rob = data[5]

                if int(emami['price']) not in emami_data:
                    emami_data.append(int(emami['price']))
                    self.data['emami'] = emami_data
                    flag = True

                if int(azadi['price']) not in azadi_data:
                    azadi_data.append(int(azadi['price']))
                    self.data['azadi'] = azadi_data
                    flag = True

                if int(nim['price']) not in nim_data:
                    nim_data.append(int(nim['price']))
                    self.data['nim'] = nim_data
                    flag = True

                if int(rob['price']) not in rob_data:
                    rob_data.append(int(rob['price']))
                    self.data['rob'] = rob_data
                    flag = True

                max_emami = max(emami_data)
                min_emami = min(emami_data)
                max_azadi = max(azadi_data)
                min_azadi = min(azadi_data)
                max_nim = max(nim_data)
                min_nim = min(nim_data)
                max_rob = max(rob_data)
                min_rob = min(rob_data)

                await sent.edit_text('📨 در حال آماده‌سازی گزارش...')

                html = f"""
                <h3>🪙 بازار سکه</h3>
                <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

                <table bordered striped compact>
                    <tr><th>نوع سکه</th><th>💵 قیمت فعلی</th><th>⬆️ بیشینه</th><th>⬇️ کمینه</th><th>🫧 حباب</th></tr>
                    <tr><td>🪙 سکه امامی</td><td>{int(emami['price']):,}</td><td>{max_emami:,}</td><td>{min_emami:,}</td><td>{int(emami['bubble']['amount']):,}</td></tr>
                    <tr><td>🪙 سکه بهار آزادی</td><td>{int(azadi['price']):,}</td><td>{max_azadi:,}</td><td>{min_azadi:,}</td><td>{int(azadi['bubble']['amount']):,}</td></tr>
                    <tr><td>🪙 نیم سکه</td><td>{int(nim['price']):,}</td><td>{max_nim:,}</td><td>{min_nim:,}</td><td>{int(nim['bubble']['amount']):,}</td></tr>
                    <tr><td>🪙 ربع سکه</td><td>{int(rob['price']):,}</td><td>{max_rob:,}</td><td>{min_rob:,}</td><td>{int(rob['bubble']['amount']):,}</td></tr>
                </table>
                <tg-button-row>
                    <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
                </tg-button-row>
                """
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, html)

                if flag:
                    self.upload_price(self.data)
                return
            
            elif text == '💰 قیمت طلا 💰':
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال دریافت قیمت طلا...')
                data = await self.get_arz(MAIN_API)
                tala_18 = data['gold_prices']['items'][1]

                flag = False
                today = datetime.now(self.tehran).strftime('%m/%d/%Y')
                tala_data = self.data['gold'] if self.data['date'] == today else []

                if self.data['date'] != today:
                    self.data['date'] = today

                if int(tala_18['price']) not in tala_data:
                    tala_data.append(int(tala_18['price']))
                    self.data['gold'] = tala_data
                    flag = True

                max_price = max(tala_data)
                min_price = min(tala_data)

                await sent.edit_text('📨 در حال آماده‌سازی گزارش...')

                html = f"""
                <h3>💰 بازار طلای ۱۸ عیار</h3>
                <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

                <table bordered compact>
                    <tr><th>شاخص</th><th>💵 مقدار</th><th>⬆️ بیشینه</th><th>⬇️ کمینه</th><th>🫧 حباب</th></tr>
                    <tr><td>💰 طلای 18 عیار</td><td>{int(tala_18['price']):,}</td><td>{max_price:,}</td><td>{min_price:,}</td><td>{int(tala_18['bubble']['amount']):,}</td></tr>
                </table>
                <tg-button-row>
                    <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
                </tg-button-row>
                """
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, html)

                if flag:
                    self.upload_price(self.data)
                return
            
            elif text == '💱 خلاصه قیمت ها 🪙':
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال آماده‌سازی خلاصه‌ی بازار...')
                result = await self.send_daily(context)

                await sent.edit_text('📨 در حال آماده‌سازی گزارش...')
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, result)
                return
            
            elif text == '🚗 خودرو های داخلی 🚗':
                await self.reaction(update, context)
                await update.message.reply_text(
                    "🚗 فهرست خودروهای داخلی\nیکی از گزینه‌ها را انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(self.dakhelikeyboard, resize_keyboard=True)
                )
                return

            elif text == '🚗 خودرو های وارداتی 🚗':
                await self.reaction(update, context)
                await update.message.reply_text(
                    "🚙 فهرست خودروهای وارداتی\nیکی از گزینه‌ها را انتخاب کن:",
                    reply_markup=ReplyKeyboardMarkup(self.carkeyboard, resize_keyboard=True)
                )
                return

            elif text in '🔙 بازگشت':
                await self.reaction(update, context)
                if update.effective_chat.type == 'private' and update.effective_user.id == ADMIN_ID:
                    keyboard = self.admin_keyborad
                else:
                    keyboard = self.keyboard
                await update.message.reply_text(
                    "🏠 به منوی اصلی برگشتی.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            elif text in ['ایران خودرو', 'سایپا', 'مدیران خودرو', 'کرمان موتور', 'بهمن موتور', 'سایر']:
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال دریافت قیمت خودروها...')

                cars = {
                    'ایران خودرو': 'irankhodro',
                    'سایپا': 'saipa',
                    'مدیران خودرو': 'modiran',
                    'کرمان موتور': 'kerman',
                    'بهمن موتور': 'bahman',
                    'سایر': 'sayer'
                }

                url = cars.get(text)
                data = await self.get_car(f'{CAR_API}/dakheli/{url}')
                if not data:
                    await sent.edit_text('❌ اطلاعات خودروها فعلاً در دسترس نیست. کمی بعد دوباره تلاش کن.')
                    return
                await sent.edit_text('📨 در حال آماده‌سازی فهرست خودروها...')

                message = ""
                for item in data:
                    message += f"<tr><td>{item['name']}</td><td>{item['factory_price_txt']}</td><td>{item['bazar_price_txt']}</td><td>{item['change_price']:,}</td><td>{item['disagreement_price']}</td></tr>"

                html = f"""
                <h3>🚗 قیمت روز خودروهای {text}</h3>
                <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

                <table bordered striped compact>
                    <tr><th>🚘 خودرو</th><th>🏭 کارخانه</th><th>🏷️ بازار</th><th>📈 تغییر ۲۴ساعته</th><th>↔️ اختلاف</th></tr>
                    {message}
                </table>
                <tg-button-row>
                    <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
                </tg-button-row>
                """
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, html)
                return

            elif text in ['هیوندای', 'کیا', 'تویوتا', 'بنز', 'بی ام و', 'فولکس واگن', 'مزدا', 'ولوو', 'آئودی', 'نیسان', 'هوندا', 'میتسوبیشی', 'MG', 'BYD', 'GAC', 'چانگان', 'ونوسیا', 'اشکودا']:
                await self.reaction(update, context)
                sent = await update.message.reply_text('⏳ در حال دریافت قیمت خودروها...')

                cars = {
                    'هیوندای': 'hyundai',
                    'کیا': 'kia',
                    'تویوتا': 'toyota',
                    'بنز': 'benz',
                    'بی ام و': 'bmw',
                    'فولکس واگن': 'volkswagen',
                    'مزدا': 'mazda',
                    'ولوو': 'volvo',
                    'آئودی': 'audi',
                    'نیسان': 'nissan',
                    'هوندا': 'honda',
                    'میتسوبیشی': 'mitsubishi',
                    'MG': 'mg',
                    'BYD': 'byd',
                    'GAC': 'gac',
                    'چانگان': 'changan',
                    'ونوسیا': 'venucia',
                    'اشکودا': 'skoda'
                }

                url = cars.get(text)
                data = await self.get_car(f'{CAR_API}/varedati/{url}')
                if not data:
                    await sent.edit_text('❌ اطلاعات خودروها فعلاً در دسترس نیست. کمی بعد دوباره تلاش کن.')
                    return
                await sent.edit_text('📨 در حال آماده‌سازی فهرست خودروها...')

                message = ""
                for item in data:
                    message += f"<tr><td>{item['name']}</td><td>{item['factory_price_txt']}</td><td>{item['bazar_price_txt']}</td><td>{item['change_price']:,}</td><td>{item['disagreement_price']}</td></tr>"

                html = f"""
                <h3>🚗 قیمت روز خودروهای {text}</h3>
                <p><mark>🕒 زمان ثبت گزارش: {datetime.now(self.tehran).strftime('%H:%M:%S')}</mark></p>

                <table bordered striped compact>
                    <tr><th>🚘 خودرو</th><th>🏭 کارخانه</th><th>🏷️ بازار</th><th>📈 تغییر ۲۴ساعته</th><th>↔️ اختلاف</th></tr>
                    {message}
                </table>
                <tg-button-row>
                    <tg-button type="url" style="success" url="https://t.me/arzpricekshbot">ورود به ربات ↗</tg-button>
                </tg-button-row>
                """
                await sent.delete()
                await self.send_rich_message(update.effective_chat.id, html)

                return

            elif text == '🧮 تبدیل ارز به ریال 🧮':
                await self.reaction(update, context)
                await update.message.reply_text('🧮 مقدار و نام موردنظر را بفرست؛ مثلاً:\n<b>10 دلار</b>\n<b>25 یورو</b>\n<b>30 گرم طلا</b> یا <b>30 گرم</b>', 
                    parse_mode='HTML')
                return

            elif re.fullmatch(r'\s*[-0-9۰-۹٠٩]+(?:[.,][-0-9۰-۹٠٩]+)?\s+دلار\s*', text):
                await self.reaction(update, context)
                normalized_text = text.translate(str.maketrans(
                    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
                    '01234567890123456789'
                ))
                amount_text = normalized_text.split()[0].replace(',', '.')
                data = await self.get_arz(MAIN_API)
                dollar = data['currency_prices']['items'][0]
                toman = float(amount_text) * int(dollar['sell_price']['value'])
                time = datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')

                await update.message.reply_text(
                    f'\U0001f4b5 {amount_text} دلار = {int(toman):,} تومان\n\n🕒 <b>زمان:</b> {time}', parse_mode='HTML'
                )
                return
            
            elif re.fullmatch(r'\s*[-0-9۰-۹٠٩]+(?:[.,][-0-9۰-۹٠٩]+)?\s+یورو\s*', text):
                await self.reaction(update, context)
                normalized_text = text.translate(str.maketrans(
                    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
                    '01234567890123456789'
                ))
                amount_text = normalized_text.split()[0].replace(',', '.')
                data = await self.get_arz(MAIN_API)
                eurro = data['currency_prices']['items'][1]
                toman = float(amount_text) * int(eurro['sell_price']['value'])
                time = datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')

                await update.message.reply_text(
                    f'💷 {amount_text} یورو = {int(toman):,} تومان\n\n🕒 <b>زمان:</b> {time}', parse_mode='HTML'
                )
                return

            elif re.fullmatch(r'\s*[0-9۰-۹٠-٩]+(?:[.,][0-9۰-۹٠-٩]+)?\s+(?:گرم(?:\s+طلا)?|طلا)\s*', text):
                await self.reaction(update, context)
                normalized_text = text.translate(str.maketrans(
                    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
                    '01234567890123456789'
                ))
                amount_text = normalized_text.split()[0].replace(',', '.')
                data = await self.get_arz(MAIN_API)
                tala = data['gold_prices']['items'][1]['price']
                toman = float(amount_text) * int(tala)
                time = datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')

                await update.message.reply_text(
                    f'💰 {amount_text} گرم طلا = {int(toman):,}\n\n🕒 <b>زمان:</b> {time}', parse_mode='HTML'
                )
                return

        except requests.exceptions.RequestException:
            await update.message.reply_text("❌ دریافت اطلاعات ناموفق بود. لطفاً کمی بعد دوباره تلاش کن.")
            return

def auto_set_hours(job_queue):
    arz = Arz()

    if not arz.set:
        return False

    for schedule in arz.set:
        for hour, minute in schedule['Hours']:
            job_queue.run_daily(arz.send_daily, time=time(hour, minute, tzinfo=arz.tehran), chat_id=schedule['ID'], name=schedule['job_name'])

    return True
    
async def post_init(application):
    data = auto_set_hours(application.job_queue)

    if data:
        await application.bot.send_message(chat_id=ADMIN_ID, text='✅ زمان‌بندی‌های ذخیره‌شده فعال شدند.')
    else:
        await application.bot.send_message(chat_id=ADMIN_ID, text='ℹ️ زمان‌بندی ذخیره‌شده‌ای برای فعال‌سازی پیدا نشد.')

    await application.bot.set_my_commands([
        BotCommand('start', '🚀 شروع و نمایش منو'),
        BotCommand('update', '✨ مشاهده‌ی تغییرات نسخه'),
        BotCommand('set', '⏰ تنظیم ساعت گزارش قیمت'),
        BotCommand('myschedule', '🗓️ دیدن ساعت‌های فعال'),
        BotCommand('unset', '⏸️ توقف گزارش زمان‌بندی‌شده'),
        BotCommand('send', '📨 ارسال پیام به مدیر'),
        BotCommand('help', '📋 راهنمای دستورها')
    ])
    

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.post_init = post_init

    arz = Arz()
    application.add_handler(CommandHandler("start", arz.start))
    application.add_handler(CommandHandler("update", arz.update))
    application.add_handler(CommandHandler("manager", arz.send_to_user))
    application.add_handler(CommandHandler("send", arz.send_to_manager))
    application.add_handler(CommandHandler("set", arz.set_hours))
    application.add_handler(CommandHandler("myschedule", arz.myschedule))
    application.add_handler(CommandHandler("unset", arz.unset_hours))
    application.add_handler(CommandHandler("help", arz.help))
    application.add_handler(MessageHandler(filters.Regex(r'^⚙️ پنل مدیریت ⚙️$'), arz.admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, arz.take_price))
    application.add_handler(CallbackQueryHandler(arz.handle_panel))
    #application.job_queue.run_once(arz.check_update, when=5)

    application.run_polling()
