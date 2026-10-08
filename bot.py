import requests
import os
import json
import base64
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from cryptography.fernet import Fernet
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

MAIN_API = os.getenv('Main_API')
USD_API = os.getenv('USD')
CAR_API = os.getenv('Car_API')
CHART_API = os.getenv('Chart')
OIL = os.getenv('Oil')
GIT = os.getenv('GIT_Token')
KEY = os.getenv('Key')
ADMIN_ID = int(os.getenv('Admin_ID'))
VERSION = '1.2.0'

class Arz:
    def __init__(self):
        self.tehran = ZoneInfo("Asia/Tehran")
        self.fernet = Fernet(KEY)

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
        
        for chat_id in users:
            await context.bot.send_message(
                chat_id=chat_id['ID'],
                text=f'آپدیت نسخه v{VERSION} منتشر شد.\n\n'
                     '- برای اعمال آپدیت بر روی دستور زیر بزنید:\n'
                     '/update'
            )
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
        
        await update.message.reply_text(
            f"سلام {name} 👋\nبرای دیدن انواع قیمت ها از گزینه های زیر استفاده کن.",
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

        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )

        text = (f'نسخه: v{VERSION}\n\n'
                '<b> تغییرات:</b>\n'
                '1. دو منبع دیگه برای قیمت دلار اضافه شد.\n\n'
                '2. با ارسال (<b>دلار</b>، <b>یورو</b>، <b>طلا</b>) علاوه بر قیمت، نمودار آن را دریافت کنید.\n\n'
                '3. قیمت <b>نفت</b> به لیست <b>خلاصه قیمت ها</b> اضافه شد.'
        )
        
        await update.message.reply_text(text=text, parse_mode='HTML', reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        text = (
            '📋 دستورات ربات:\n\n'
            '/start - شروع و نمایش منو\n'
            '/update - آپدیت ربات\n'
            '/send - ارسال پیام به مدیر\n'
            '/help - نمایش دستورات\n'
            'یا از دکمه‌های زیر صفحه برای دریافت قیمت‌ها استفاده کنید.'
        )
        await update.message.reply_text(text)

    async def admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private' and update.effective_user.id != ADMIN_ID:
            return

        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        self.inline_keyboard = [
            [InlineKeyboardButton('📊 تعداد کاربران 📊', callback_data='users')],
            [InlineKeyboardButton('📨 پیام همگانی 📨', callback_data='messages')]
        ]

        reply_markup = InlineKeyboardMarkup(self.inline_keyboard)
        await update.message.reply_text('پنل مدیریت مدیر فعال شد.⚙️',
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
            message = f'📊 تعداد کل کاربران: {count}\n'
            message += '📋 لیست کاربران\n\n'
            for i, user in enumerate(data, start=1):
                message += (
                    f'{i}. {user['Name']} - {user['ID']}\n\n'
                )
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

        elif choose == 'messages':
            await query.edit_message_text('متن مورد نظر را به همراه /manager ارسال کنید.', reply_markup=InlineKeyboardMarkup(keyboard))

        elif choose == 'back':
            await query.edit_message_text('پنل مدیریت فعال شد.⚙️',
                reply_markup=InlineKeyboardMarkup(self.inline_keyboard))

    async def send_to_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )

        text = update.message.text.strip() if update.message.text else ''
        if not text.startswith('/manager'):
            await update.message.reply_text('در پیام باید /manager وجود داشته باشد، مانند:\n/manager all سلام\n/manager 123456789 سلام')
            return

        rest = text[len('/manager'):].strip()
        if not rest:
            await update.message.reply_text('فرمت نامعتبر است. مثال:\n/manager all سلام\n/manager 123456789 سلام')
            return

        target = rest.split()[0]
        msg = ' '.join(rest.split()[1:]).strip()

        if not msg:
            await update.message.reply_text('متن پیام را هم وارد کنید. مثال:\n/manager all سلام\n/manager 123456789 سلام')
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
            await update.message.reply_text(f'پیام همگانی به {sent} کاربر ارسال شد.' + (f' | {failed} خطا داشت.' if failed else ''))
            return

        if target.isdigit() or (target.startswith('-') and target[1:].isdigit()):
            try:
                chat_id = int(target)
                await context.bot.send_message(chat_id=chat_id, text=msg)
                await update.message.reply_text(f'پیام به آیدی {chat_id} ارسال شد.')
            except Exception as exc:
                await update.message.reply_text(f'ارسال به آیدی {target} انجام نشد.\nخطا: {exc}')
            return

        await update.message.reply_text('آیدی نامعتبر است. مثال:\n/manager all سلام\n/manager 123456789 سلام')

    async def send_to_manager(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        text = update.message.text
        if '/send' not in text:
            await update.message.reply_text('در پیام باید /send وجود داشته باشد، مانند:\n/send سلام این یک پیام ارسالی به مدیر است.')
            return 

        if text == '/send':
            await update.message.reply_text('در پیام باید /send وجود داشته باشد، مانند:\n/send سلام این یک پیام ارسالی به مدیر است.')
            return
        
        msg = text.replace('/send', '')
        await context.bot.send_message(chat_id=ADMIN_ID, text=f'پیام از کاربر {update.effective_user.full_name} - ({update.effective_user.id}):\n\n{msg}')
        await update.message.reply_text('پیام شما به مدیر ارسال شد.')

    async def send_long_message(self, update: Update, message: str, chunk_size: int = 3000):
        for i in range(0, len(message), chunk_size):
            await update.message.reply_text(message[i:i + chunk_size])

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
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(MAIN_API)
                dollar = await self.get_arz(USD_API)
                data = data['currency_prices']['items']
                dollar = dollar['sources']['alanchand']
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                indexs = [6, 1, 2, 3, 4, 9, 15, 19]
                message = "\U0001f4b5 قیمت ارزها \U0001f4b5\n\n"
                message += (
                    f" - قیمت دلار\n"
                    f" - قیمت: {int(dollar['price_toman']):,} تومان\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                )

                for idx in indexs:
                    item = data[idx]
                    message += (
                        f" - {item['name_persian']}\n"
                        f" - قیمت: {int(item['sell_price']['value']):,} {item['currency']}\n"
                        f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    )
                await update.message.reply_text(message)
                return
            
            elif text == '🪙 قیمت سکه 🪙':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(MAIN_API)
                data = data['gold_prices']['items']

                today = datetime.now(self.tehran).strftime('%m/%d/%Y')
                emami_data = self.data['emami'] if self.data['date'] == today else []
                azadi_data = self.data['azadi'] if self.data['date'] == today else []
                nim_data = self.data['nim'] if self.data['date'] == today else []
                rob_data = self.data['rob'] if self.data['date'] == today else []

                if self.data.get('date') != today:
                    self.data['date'] = today

                message = "🪙 قیمت سکه 🪙\n\n"
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

                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message += (
                    f" - 🪙 سکه امامی\n"
                    f" - قیمت: {int(emami['price']):,} {emami['currency']}\n"
                    f" - بیشینه: {max_emami:,} تومان\n"
                    f" - کمینه: {min_emami:,} تومان\n"
                    f" - حباب قیمتی: {int(emami['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🪙 سکه بهار آزادی\n"
                    f" - قیمت: {int(azadi['price']):,} {azadi['currency']}\n"
                    f" - بیشینه: {max_azadi:,} تومان\n"
                    f" - کمینه: {min_azadi:,} تومان\n"
                    f" - حباب قیمتی: {int(azadi['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🪙 نیم سکه\n"
                    f" - قیمت: {int(nim['price']):,} {nim['currency']}\n"
                    f" - بیشینه: {max_nim:,} تومان\n"
                    f" - کمینه: {min_nim:,} تومان\n"
                    f" - حباب قیمتی: {int(nim['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🪙 ربع سکه\n"
                    f" - قیمت: {int(rob['price']):,} {rob['currency']}\n"
                    f" - بیشینه: {max_rob:,} تومان\n"
                    f" - کمینه: {min_rob:,} تومان\n"
                    f" - حباب قیمتی: {int(rob['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                )
                await update.message.reply_text(message)

                if flag:
                    self.upload_price(self.data)
                return
            
            elif text == '💰 قیمت طلا 💰':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(MAIN_API)
                data = data['gold_prices']['items']
                tala_18 = data[1]

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

                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = "💰 قیمت طلا 💰\n\n"
                message += (
                    f" - 💰 طلای 18 عیار\n"
                    f" - قیمت: {int(tala_18['price']):,} {tala_18['currency']}\n"
                    f" - بیشینه: {max_price:,} تومان\n"
                    f" - کیمینه: {min_price:,} تومان\n"
                    f" - حباب قیمتی: {int(tala_18['bubble']['amount']):,}\n"
                    f" - اپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                )
                await update.message.reply_text(message)

                if flag:
                    self.upload_price(self.data)
                return
            
            elif text == '💱 خلاصه قیمت ها 🪙':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(MAIN_API)
                dollar = await self.get_arz(USD_API)
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
                dollar = dollar['sources']['alanchand']
                eurro = data['currency_prices']['items'][1]
                seke_emami = data['gold_prices']['items'][2]
                seke = data['gold_prices']['items'][3]
                tala_18 = data['gold_prices']['items'][1]
                oil = oil['items'][0]

                if int(tether['price_toman']) not in tether_data:
                    tether_data.append(int(tether['price_toman']))
                    self.data['tether'] = tether_data
                    flag = True

                if int(dollar['price_toman']) not in usd_data:
                    usd_data.append(int(dollar['price_toman']))
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


                message = '💱 خلاصه قیمت ها 🪙\n\n'
                message += (
                    f" - \U0001f4b8 قیمت {tether['name_persian']}\n"
                    f" - قیمت: {int(tether['price_toman']):,} تومان\n"
                    f" - بیشینه: {tether_max:,} تومان\n"
                    f" - کمینه: {tether_min:,} تومان\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - \U0001f4b5 قیمت دلار\n"
                    f" - قیمت: {int(dollar['price_toman']):,} تومان\n"
                    f" - بیشینه: {usd_max:,} تومان\n"
                    f" - کمینه: {usd_min:,} تومان\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 💷 {eurro['name_persian']}\n"
                    f" - قیمت: {int(eurro['sell_price']['value']):,} {eurro['currency']}\n"
                    f" - بیشینه: {eur_max:,} تومان\n"
                    f" - کمینه: {eur_min:,} تومان\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🪙 سکه امامی\n"
                    f" - قیمت: {int(seke_emami['price']):,} {seke_emami['currency']}\n"
                    f" - بیشینه: {emami_max:,} تومان\n"
                    f" - کمینه: {emami_min:,} تومان\n"
                    f" - حباب قیمتی: {int(seke_emami['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🪙 سکه بهار آزادی\n"
                    f" - قیمت: {int(seke['price']):,} {seke['currency']}\n"
                    f" - بیشینه: {azadi_max:,} تومان\n"
                    f" - کمینه: {azadi_min:,} تومان\n"
                    f" - حباب قیمتی: {int(seke['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 💰 طلای 18 عیار\n"
                    f" - قیمت: {int(tala_18['price']):,} {tala_18['currency']}\n"
                    f" - بیشینه: {tala_max:,} تومان\n"
                    f" - کمینه: {tala_min:,} تومان\n"
                    f" - حباب قیمتی: {int(tala_18['bubble']['amount']):,}\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    f" - 🛢️ {oil['name']}\n"
                    f" - قیمت: {oil['price']} دلار\n"
                    f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                )

                await sent.edit_text('در حال ارسال...')
                await sent.delete()
                await update.message.reply_text(message)

                if flag:
                    self.upload_price(self.data)
                return
            
            elif text == '🚗 خودرو های داخلی 🚗':
                await self.reaction(update, context)
                await update.message.reply_text(
                    "🚗 لیست خودرو های داخلی 🚗\nیکی از آنها را انتخاب کنید",
                    reply_markup=ReplyKeyboardMarkup(self.dakhelikeyboard, resize_keyboard=True)
                )
                return

            elif text == '🚗 خودرو های وارداتی 🚗':
                await self.reaction(update, context)
                await update.message.reply_text(
                    "🚗 لیست خودرو های وارداتی 🚗\nیکی از آنها را انتخاب کنید",
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
                    "بازگشت به منوی اصلی",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
                return

            elif text in ['ایران خودرو', 'سایپا', 'مدیران خودرو', 'کرمان موتور', 'بهمن موتور', 'سایر']:
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')

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
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = f"🚗 قیمت خودرو های {text} 🚗\n\n"
                for item in data:
                    message += (
                        f" - 🚗 {item['name']}\n"
                        f" - قیمت کارخانه: {item['factory_price_txt']}\n"
                        f" - قیمت بازار: {item['bazar_price_txt']}\n"
                        f" - تغییرات 24 ساعته: {item['change_price']}\n"
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n"
                        f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    )
                await self.send_long_message(update, message)
                return

            elif text in ['هیوندای', 'کیا', 'تویوتا', 'بنز', 'بی ام و', 'فولکس واگن', 'مزدا', 'ولوو', 'آئودی', 'نیسان', 'هوندا', 'میتسوبیشی', 'MG', 'BYD', 'GAC', 'چانگان', 'ونوسیا', 'اشکودا']:
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')

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
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = f"🚗 قیمت خودرو های {text} 🚗\n\n"
                for item in data:
                    message += (
                        f" - 🚗 {item['name']}\n"
                        f" - قیمت کارخانه: {item['factory_price_txt']}\n"
                        f" - قیمت بازار: {item['bazar_price_txt']}\n"
                        f" - تغییرات 24 ساعته: {item['change_price']}\n"
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n"
                        f" - آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S')}\n\n"
                    )
                await self.send_long_message(update, message)
                return

            elif text == 'دلار':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                usd = await self.get_arz(f'{CHART_API}/api/history.json')
                await sent.edit_text('در حال ارسال نمودار...')
                await sent.delete()
                
                caption = (
                    f'\U0001f4b5 قیمت دلار: {int(usd['latest']['price_toman']):,} تومان\n'
                    f'🕒 آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')}'
                )

                await update.message.reply_photo(photo='https://github.com/itsyebekhe/nabz/raw/main/charts/usd.png', caption=caption)
                return

            elif text == 'یورو':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                eur = await self.get_arz(f'{CHART_API}/api/history_eur.json')
                await sent.edit_text('در حال ارسال نمودار...')
                await sent.delete()
                
                caption = (
                    f'💷 قیمت یورو: {int(eur['latest']['price_toman']):,} تومان\n'
                    f'🕒 آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')}'
                )

                await update.message.reply_photo(photo=f'https://github.com/itsyebekhe/nabz/raw/main/charts/eur.png', caption=caption)
                return

            elif text == 'طلا':
                await self.reaction(update, context)
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                gold = await self.get_arz(f'{CHART_API}/api/history_gold_18k.json')
                await sent.edit_text('در حال ارسال نمودار...')
                await sent.delete()

                caption = (
                    f'💰 قیمت طلا: {int(gold['latest']['price_toman']):,} تومان\n'
                    f'🕒 آپدیت: {datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')}'
                )

                await update.message.reply_photo(photo=f'https://github.com/itsyebekhe/nabz/raw/main/charts/gold_18k.png', caption=caption)
                return

            elif text == '🧮 تبدیل ارز به ریال 🧮':
                await self.reaction(update, context)
                await update.message.reply_text('برای تبدیل طلا و ارز های (دلار، یورو) مقدار به همراه نام وارد کنید. مانند:\n<b>10 دلار</b>\n<b>25 یورو</b>\n<b>30 گرم طلا یا 30 طلا</b>', 
                    parse_mode='HTML')
                return

            elif re.fullmatch(r'\s*[-0-9۰-۹٠٩]+(?:[.,][-0-9۰-۹٠٩]+)?\s+دلار\s*', text):
                await self.reaction(update, context)
                normalized_text = text.translate(str.maketrans(
                    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
                    '01234567890123456789'
                ))
                amount_text = normalized_text.split()[0].replace(',', '.')
                data = await self.get_arz(USD_API)
                dollar = data['sources']['alanchand']['price_toman']
                toman = float(amount_text) * int(dollar)
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
                euro = data['currency_prices']['items'][1]
                toman = float(amount_text) * int(euro['sell_price']['value'])
                time = datetime.now(self.tehran).strftime('%H:%M:%S | %Y/%m/%d')

                await update.message.reply_text(
                    f'💷 {amount_text} یورو = {int(toman):,} تومان\n\n🕒 <b>زمان:</b> {time}', parse_mode='HTML'
                )
                return

            elif re.fullmatch(r'\s*[-0-9۰-۹٠٩]+(?:[.,][-0-9۰-۹٠٩]+)?\s+(?:گرم\s+)?طلا\s*', text):
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
            await update.message.reply_text("❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            return

if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        raise RuntimeError('WEBHOOK_URL is not set. Example: https://your-app-name.onrender.com')

    port = int(os.environ.get('PORT', 10000))

    application = ApplicationBuilder().token(token).build()

    arz = Arz()
    application.add_handler(CommandHandler("start", arz.start))
    application.add_handler(CommandHandler("update", arz.update))
    application.add_handler(CommandHandler("manager", arz.send_to_user))
    application.add_handler(CommandHandler("send", arz.send_to_manager))
    application.add_handler(CommandHandler("help", arz.help))
    application.add_handler(MessageHandler(filters.Regex(r'^⚙️ پنل مدیریت ⚙️$'), arz.admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, arz.take_price))
    application.add_handler(CallbackQueryHandler(arz.handle_panel))

    application.run_webhook(
        listen='0.0.0.0',
        port=port,
        url_path='webhook',
        webhook_url=f"{webhook_url.rstrip('/')}/webhook"
    )
