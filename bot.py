import requests
import os
from datetime import datetime, time
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

MAIN_API = os.getenv('Main_API')
CAR_API = os.getenv('Car_API')
VERSION = '0.6.1'
tehran = ZoneInfo("Asia/Tehran")

class Arz:
    def __init__(self):
        self.keyboard = [
            ['💱 خلاصه قیمت ها 🪙'],
            ['🪙 قیمت سکه 🪙', '💰 قیمت طلا 💰'],
            ['💱 قیمت ارز ها 💱'],
            ['🚗 خودرو های داخلی 🚗'],
            ['🚗 خودرو های وارداتی 🚗']
        ]

        self.carkeyboard = [
            ['هیوندای', 'کیا', 'تویوتا'],
            ['بنز', 'بی ام و', 'فولکس واگن'],
            ['مزدا', 'ولوو', 'آئودی'],
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

    async def get_arz(self, url):
        response = requests.get(url, timeout=10).json()
        return response['data']

    async def get_car(self, url):
        response = requests.get(url, timeout=10).json()
        return response['cars']

    async def check_update(self, context: ContextTypes.DEFAULT_TYPE):
        if context.bot_data.get('last_version') == VERSION:
            return

        started_users = context.bot_data.get('started_users', set())
        if not started_users:
            context.bot_data['last_version'] = VERSION
            return

        for chat_id in started_users:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'آپدیت نسخه {VERSION} منتشر شد.\n\n'
                     '- برای اعمال آپدیت مجدد /start کنید.'
            )

        context.bot_data['last_version'] = VERSION
        return

    async def send_daily(self, context: ContextTypes.DEFAULT_TYPE):
        crypto = await self.get_arz(f'{MAIN_API}/crypto')
        arz = await self.get_arz(f'{MAIN_API}/currency')
        coin = await self.get_arz(f'{MAIN_API}/coin')
        gold = await self.get_arz(f'{MAIN_API}/gold')
        if not crypto or not arz or not coin or not gold:
            return False

        tether = crypto[2]
        dollar = arz[0]
        eurro = arz[1]
        seke = coin[1]
        tala_18 = gold[0]
        tala_24 = gold[2]

        message = '💱 خلاصه قیمت ها 🪙\n\n'
        message += (
            f" - \U0001f4b8 {tether['name_fa']}\n"
            f" - قیمت: {tether['price_irl'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
            f" - \U0001f4b5 {dollar['name']}\n"
            f" - قیمت: {dollar['price'] // 10}\n"
            f" - کمینه: {dollar['min'] // 10}\n"
            f" - بیشینه: {dollar['max'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
            f" - 💷 {eurro['name']}\n"
            f" - قیمت: {eurro['price'] // 10}\n"
            f" - کمینه: {eurro['min'] // 10}\n"
            f" - بیشینه: {eurro['max'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
            f" - 🪙 {seke['name']}\n"
            f" - قیمت: {seke['price'] // 10}\n"
            f" - کمینه: {seke['min'] // 10}\n"
            f" - بیشینه: {seke['max'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
            f" - 💰 طلای 18 عیار\n"
            f" - قیمت: {tala_18['price'] // 10}\n"
            f" - کمینه: {tala_18['min'] // 10}\n"
            f" - بیشینه: {tala_18['max'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
            f" - 💰 {tala_24['name']}\n"
            f" - قیمت: {tala_24['price'] // 10}\n"
            f" - کمینه: {tala_24['min'] // 10}\n"
            f" - بیشینه: {tala_24['max'] // 10}\n"
            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
        )

        if context.job is not None:
            await context.bot.send_message(chat_id=context.job.chat_id, text=message)
        return message

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user = update.effective_user
            name = user.full_name

            await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                    message_id=update.message.message_id,
                    reaction=['❤️']
                )
            
            await update.message.reply_text(
                f"سلام {name} 👋\nبرای دیدن انواع قیمت ها از گزینه های زیر استفاده کن.",
                reply_markup=ReplyKeyboardMarkup(self.keyboard, resize_keyboard=True)
                )

            await update.message.reply_text(f'نسخه: {VERSION}\n\n'
                    'تغییرات:\n'
                    '- تنظیم ساعت ارسال خودکار توسط کاربر\n'
                    '- اضافه شدن کامند /set برای تنظیم ساعت ارسال خودکار\n'
                    '- آپدیت هر دقیقه لیست با هر درخواست\n'
                )
            return
        
        except Exception as e:
            update.message.reply_text(e)
            return
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        text = (
            '📋 دستورات ربات:\n\n'
            '/start - شروع و نمایش منو\n'
            '/set 03 10 18 - تنظیم ساعت ارسال خودکار\n\n'
            'یا از دکمه‌های زیر صفحه برای دریافت قیمت‌ها استفاده کنید.'
        )
        await update.message.reply_text(text)

    async def set_hours(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        if len(context.args) == 0:
            await update.message.reply_text('لطفا ساعت ها را وارد کنید مانند:\n/set 03 10 18 ...')
            return

        try:
            hours = list(int(h) for h in context.args)
        except ValueError:
            await update.message.reply_text('ساعت ها باید عدد باشد!')
            return
        for h in hours:
            if not 0 <= h <=23:
                await update.message.reply_text("ساعت باید بین 0 تا 23 باشد.")
                return
            
        job_name = f'chat_id_{update.effective_chat.id}'

        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        for h in hours:
            context.job_queue.run_daily(self.send_daily, time=time(h, 0, tzinfo=tehran), chat_id=update.effective_chat.id, name=job_name)
        await update.message.reply_text(f'زمانبندی ارسال خودکار لیست قیمت برای ساعت های {hours} انجام شد')
        return

    async def send_long_message(self, update: Update, message: str, chunk_size: int = 3000):
        for i in range(0, len(message), chunk_size):
            await update.message.reply_text(message[i:i + chunk_size])

    async def take_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text is None:
            return

        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f44d']
            )
        
        try:
            if text in '💱 قیمت ارز ها 💱':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(f'{MAIN_API}/currency')
                if not data:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                indexs = [0, 9, 1, 2, 3, 4, 21, 22, 23, 24, 25]
                message = "\U0001f4b5 قیمت ارزها \U0001f4b5\n\n"
                for idx in indexs:
                    item = data[idx]
                    message += (
                        f" - {item['name']}\n"
                        f" - قیمت: {item['price'] // 10}\n"
                        f" - کمینه: {item['min'] // 10}\n"
                        f" - بیشینه: {item['max'] // 10}\n"
                        f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
                    )

            elif text in '🪙 قیمت سکه 🪙':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(f'{MAIN_API}/coin')
                if not data:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = "🪙 قیمت سکه 🪙\n\n"
                for item in data:
                    if item['key'] == 'retail_sekee':
                        break
                    message += (
                        f" - 🪙 {item['name']}\n"
                        f" - قیمت: {item['price'] // 10}\n"
                        f" - کمینه: {item['min'] // 10}\n"
                        f" - بیشینه: {item['max'] // 10}\n"
                        f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
                    )

            elif text in '💰 قیمت طلا 💰':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(f'{MAIN_API}/gold')
                if not data:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = "💰 قیمت طلا 💰\n\n"
                for item in data:
                    if item['key'] == 'geram18' or item['key'] == 'geram24':
                        message += (
                            f" - 💰 {item['name']}\n"
                            f" - قیمت: {item['price'] // 10}\n"
                            f" - کمینه: {item['min'] // 10}\n"
                            f" - بیشینه: {item['max'] // 10}\n"
                            f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
                        )
                    if item['key'] == 'geram24':
                        break

            elif text in '💱 خلاصه قیمت ها 🪙':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                result = await self.send_daily(context)
                if result is False:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()
                await update.message.reply_text(result)
                return
            
            elif text in '🚗 خودرو های داخلی 🚗':
                await update.message.reply_text(
                    "🚗 لیست خودرو های داخلی 🚗\nیکی از آنها را انتخاب کنید",
                    reply_markup=ReplyKeyboardMarkup(self.dakhelikeyboard, resize_keyboard=True)
                )
                return

            elif text in '🚗 خودرو های وارداتی 🚗':
                await update.message.reply_text(
                    "🚗 لیست خودرو های وارداتی 🚗\nیکی از آنها را انتخاب کنید",
                    reply_markup=ReplyKeyboardMarkup(self.carkeyboard, resize_keyboard=True)
                )
                return

            elif text in '🔙 بازگشت':
                await update.message.reply_text(
                    "بازگشت به منوی اصلی",
                    reply_markup=ReplyKeyboardMarkup(self.keyboard, resize_keyboard=True)
                )
                return

            elif text in ['ایران خودرو', 'سایپا', 'مدیران خودرو', 'کرمان موتور', 'بهمن موتور', 'سایر']:
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
                        f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
                    )
                await self.send_long_message(update, message)
                return

            elif text in ['هیوندای', 'کیا', 'تویوتا', 'بنز', 'بی ام و', 'فولکس واگن', 'مزدا', 'ولوو', 'آئودی', 'MG', 'BYD', 'GAC', 'چانگان', 'ونوسیا', 'اشکودا']:
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
                        f" - اپدیت: {datetime.now(tehran).strftime('%H:%M:%S')}\n\n"
                    )
                await self.send_long_message(update, message)
                return
            
            await update.message.reply_text(message)
            return

        except requests.exceptions.RequestException:
            await update.message.reply_text("❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            return

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand('start', 'شروع و نمایش منو'),
        BotCommand('set', 'تنظیم ساعت ارسال خودکار'),
        BotCommand('help', 'راهنمای دستورات')
    ])
        
if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        raise RuntimeError('WEBHOOK_URL is not set. Example: https://your-app-name.onrender.com')

    port = int(os.environ.get('PORT', 10000))

    application = ApplicationBuilder().token(token).build()

    application.post_init = post_init

    arz = Arz()
    application.add_handler(CommandHandler("start", arz.start))
    application.add_handler(CommandHandler("set", arz.set_hours))
    application.add_handler(CommandHandler("help", arz.help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, arz.take_price))
    application.job_queue.run_once(arz.check_update, when=5)

    application.run_webhook(
        listen='0.0.0.0',
        port=port,
        url_path='webhook',
        webhook_url=f"{webhook_url.rstrip('/')}/webhook"
    )
