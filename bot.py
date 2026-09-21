import requests
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

API = 'https://tgju.apidarkness.workers.dev'

class Arz:
    def __init__(self):
        self.keyboard = [
            ['🪙 قیمت سکه 🪙', '💰 قیمت طلا 💰'],
            ['💱 قیمت ارز ها 💱'],
            ['🚗 قیمت خودرو داخلی 🚗'],
            ['🚗 خودرو های وارداتی 🚗']
        ]

        self.carkeyboard = [
            ['هیوندای', 'کیا', 'تویوتا'],
            ['بنز', 'بی ام و', 'فولکس واگن'],
            ['MZDA', 'ولوو', 'آئودی'],
            ['MG', 'BYD', 'GAC'],
            ['چانگان', 'ونوسیا', 'اشکودا'],
            ['🔙 بازگشت']
        ]

    async def get_arz(self, url):
        response = requests.get(url, timeout=10).json()
        return response['data']

    async def get_car(self, url):
        response = requests.get(url, timeout=10).json()
        return response['cars']
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        name = user.full_name
        user_id = user.id
        print(f"User: '{name}', ID: '{user_id}' started the bot.")

        await update.message.reply_text(
            f"سلام {name} 👋\nبرای دیدن انواع قیمت ها از گزینه های زیر استفاده کن.",
            reply_markup=ReplyKeyboardMarkup(self.keyboard, resize_keyboard=True)
        )

    async def send_long_message(self, update: Update, message: str, chunk_size: int = 3000):
        for i in range(0, len(message), chunk_size):
            await update.message.reply_text(message[i:i + chunk_size])

    async def take_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text is None:
            return

        exception = ['price_chf', 'price_cny', 'price_jpy', 'price_cad', 'price_krw', 'price_aud', 'price_nzd', 'price_sgd', 'price_inr', 'price_pkr',
                    'price_syp', 'price_afn', 'price_dkk', 'price_sek', 'price_nok', 'price_sar', 'price_myr', 'price_thb', 'price_hkd', 'price_rub',
                    'price_azn', 'price_amd', 'price_gel', 'price_kgs', 'price_tjs', 'price_tmt']
        
        try:
            if text in '💱 قیمت ارز ها 💱':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                await sent.edit_text('در حال ارسال...')
                data = await self.get_arz(f'{API}/currency')
                message = "<pre>💱 قیمت ارزها 💱\n\n"
                for item in data:
                    if item['key'] in exception:
                        continue
                    message += (
                        f" - {item['name']}\n"
                        f" - قیمت: {item['price'] // 10}\n"
                        f" - کمترین: {item['min'] // 10}\n"
                        f" - بیشینه: {item['max'] // 10}\n"
                        f" - اپدیت: {item['updated_at']}\n\n"
                    )

            elif text in '🪙 قیمت سکه 🪙':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                await sent.edit_text('در حال ارسال...')
                data = await self.get_arz(f'{API}/coin')
                message = "<pre>🪙 قیمت سکه 🪙\n\n"
                for item in data:
                    if item['key'] == 'retail_sekee':
                        break
                    message += (
                        f" - 🪙 {item['name']}\n"
                        f" - قیمت: {item['price'] // 10}\n"
                        f" - کمترین: {item['min'] // 10}\n"
                        f" - بیشینه: {item['max'] // 10}\n"
                        f" - اپدیت: {item['updated_at']}\n\n"
                    )

            elif text in '💰 قیمت طلا 💰':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                await sent.edit_text('در حال ارسال...')
                data = await self.get_arz(f'{API}/gold')
                message = "<pre>💰 قیمت طلا 💰\n\n"
                for item in data:
                    if item['key'] == 'geram18' or item['key'] == 'geram24':
                        message += (
                            f" - 💰 {item['name']}\n"
                            f" - قیمت: {item['price'] // 10}\n"
                            f" - کمینه: {item['min'] // 10}\n"
                            f" - بیشینه: {item['max'] // 10}\n"
                            f" - اپدیت: {item['updated_at']}\n\n"
                        )
                    if item['key'] == 'geram24':
                        break

            elif text in '🚗 قیمت خودرو داخلی 🚗':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                await sent.edit_text('در حال ارسال...')

                irankhodro = await self.get_car('https://car.apidarkness.workers.dev/dakheli/irankhodro')

                saipa = await self.get_car('https://car.apidarkness.workers.dev/dakheli/saipa')

                message = "🚗 قیمت خودرو های ایران خودرو 🚗\n\n"
                for item in irankhodro:
                    message += (
                        f" - 🚗 {item['name']}\n"
                        f" - قیمت کارخانه: {item['factory_price_txt']}\n"
                        f" - قیمت بازار: {item['bazar_price_txt']}\n"
                        f" - تغییرات 24 ساعته: {item['change_price']}\n"
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n\n"
                    )
                await self.send_long_message(update, message)

                message = "🚗 قیمت خودرو های سایپا 🚗\n\n"
                for item in saipa:
                    message += (
                        f" - 🚗 {item['name']}\n"
                        f" - قیمت کارخانه: {item['factory_price_txt']}\n"
                        f" - قیمت بازار: {item['bazar_price_txt']}\n"
                        f" - تغییرات 24 ساعته: {item['change_price']}\n"
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n\n"
                    )
                await self.send_long_message(update, message)
                return

            elif text in '🚗 خودرو های وارداتی 🚗':
                await update.message.reply_text(
                    "🚗 لیست خودرو های وارداتی 🚗\nلطفا یکی از آنها را انتخاب کنید",
                    reply_markup=ReplyKeyboardMarkup(self.carkeyboard, resize_keyboard=True)
                )
                return

            elif text in '🔙 بازگشت':
                await update.message.reply_text(
                    "بازگشت به منوی اصلی",
                    reply_markup=ReplyKeyboardMarkup(self.keyboard, resize_keyboard=True)
                )
                return

            elif text in ['هیوندای', 'کیا', 'تویوتا', 'بنز', 'بی ام و', 'فولکس واگن', 'مزدا', 'ولوو', 'آئودی', 'MG', 'BYD', 'GAC', 'چانگان', 'ونوسیا', 'اشکودا']:
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                await sent.edit_text('در حال ارسال...')
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
                if url is None:
                    await update.message.reply_text("❌ خودرو انتخابی نامعتبر است.")
                    return

                data = await self.get_car(f'https://car.apidarkness.workers.dev/varedati/{url}')
                message = f"🚗 قیمت خودرو های {text} 🚗\n\n"
                for item in data:
                    message += (
                        f" - 🚗 {item['name']}\n"
                        f" - قیمت کارخانه: {item['factory_price_txt']}\n"
                        f" - قیمت بازار: {item['bazar_price_txt']}\n"
                        f" - تغییرات 24 ساعته: {item['change_price']}\n"
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n\n"
                    )
                await self.send_long_message(update, message)
                return
            
            message += "</pre>"
            await update.message.reply_text(message, parse_mode='HTML')
            return
        
        except requests.exceptions.RequestException:
            await update.message.reply_text("❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            return

if __name__ == '__main__':
    token = os.getenv('MY_TOKEN')
    application = ApplicationBuilder().token(token).build()

    arz = Arz()
    application.add_handler(CommandHandler("start", arz.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, arz.take_price))

    print("Bot is running...")
    application.run_polling()
