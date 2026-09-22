import requests
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

MAIN_API = os.getenv('Main_API')
CAR_API = os.getenv('Car_API')

class Arz:
    def __init__(self):
        self.keyboard = [
            ['💱 خلاصه قیمت ها 🪙'],
            ['🪙 قیمت سکه 🪙', '💰 قیمت طلا 💰'],
            ['\U0001f4b5 قیمت ارز ها \U0001f4b5'],
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

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        name = user.full_name

        await context.bot.set_message_reaction(chat_id=update.message.chat_id,
                message_id=update.message.message_id,
                reaction=['\U0001f60d']
            )
        
        await update.message.reply_text(
            f"سلام {name} 👋\nبرای دیدن انواع قیمت ها از گزینه های زیر استفاده کن.",
            reply_markup=ReplyKeyboardMarkup(self.keyboard, resize_keyboard=True)
            )

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
        
        exception = ['price_chf', 'price_cny', 'price_jpy', 'price_cad', 'price_krw', 'price_aud', 'price_nzd', 'price_sgd', 'price_inr', 'price_pkr',
                    'price_syp', 'price_afn', 'price_dkk', 'price_sek', 'price_nok', 'price_sar', 'price_myr', 'price_thb', 'price_hkd', 'price_rub',
                    'price_azn', 'price_amd', 'price_gel', 'price_kgs', 'price_tjs', 'price_tmt']
        
        try:
            if text in '\U0001f4b5 قیمت ارز ها \U0001f4b5':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                data = await self.get_arz(f'{MAIN_API}/currency')
                if not data:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                message = "\U0001f4b5 قیمت ارزها \U0001f4b5\n\n"
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
                        f" - کمترین: {item['min'] // 10}\n"
                        f" - بیشینه: {item['max'] // 10}\n"
                        f" - اپدیت: {item['updated_at']}\n\n"
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
                            f" - اپدیت: {item['updated_at']}\n\n"
                        )
                    if item['key'] == 'geram24':
                        break

            elif text in '💱 خلاصه قیمت ها 🪙':
                sent = await update.message.reply_text('در حال دریافت اطلاعات... لطفاً صبر کنید.')
                arz = await self.get_arz(f'{MAIN_API}/currency')
                coin = await self.get_arz(f'{MAIN_API}/coin')
                gold = await self.get_arz(f'{MAIN_API}/gold')
                if not arz or not coin or not gold:
                    await sent.edit_text('خطایی رخ داده است❌\nلطفا بعدا تلاش کنید')
                    return
                await sent.edit_text('در حال ارسال...')
                await sent.delete()

                dollar = arz[0]
                eurro = arz[1]
                seke = coin[1]
                tala_18 = gold[0]
                tala_24 = gold[2]
  

                message = '💱 خلاصه قیمت ها 🪙\n\n'
                message += (
                    f" - \U0001f4b5 {dollar['name']}\n"
                    f" - قیمت: {dollar['price'] // 10}\n"
                    f" - کمینه: {dollar['min'] // 10}\n"
                    f" - بیشینه: {dollar['max'] // 10}\n"
                    f" - اپدیت: {dollar['updated_at']}\n\n"
                    f" - 💷 {eurro['name']}\n"
                    f" - قیمت: {eurro['price'] // 10}\n"
                    f" - کمینه: {eurro['min'] // 10}\n"
                    f" - بیشینه: {eurro['max'] // 10}\n"
                    f" - اپدیت: {eurro['updated_at']}\n\n"
                    f" - 🪙 {seke['name']}\n"
                    f" - قیمت: {seke['price'] // 10}\n"
                    f" - کمینه: {seke['min'] // 10}\n"
                    f" - بیشینه: {seke['max'] // 10}\n"
                    f" - اپدیت: {seke['updated_at']}\n\n"
                    f" - 💰 طلای 18 عیار\n"
                    f" - قیمت: {tala_18['price'] // 10}\n"
                    f" - کمینه: {tala_18['min'] // 10}\n"
                    f" - بیشینه: {tala_18['max'] // 10}\n"
                    f" - اپدیت: {tala_18['updated_at']}\n\n"
                    f" - 💰 {tala_24['name']}\n"
                    f" - قیمت: {tala_24['price'] // 10}\n"
                    f" - کمینه: {tala_24['min'] // 10}\n"
                    f" - بیشینه: {tala_24['max'] // 10}\n"
                    f" - اپدیت: {tala_24['updated_at']}\n\n"
                )

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
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n\n"
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
                        f" - اختلاف قیمت کارخانه و بازار: {item['disagreement_price']}\n\n"
                    )
                await self.send_long_message(update, message)
                return
            
            await update.message.reply_text(message)
            return

        except requests.exceptions.RequestException:
            await update.message.reply_text("❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")
            return

if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')

    webhook_url = os.getenv('WEBHOOK_URL')

    port = int(os.environ.get('PORT', 10000))

    application = ApplicationBuilder().token(token).build()

    arz = Arz()
    application.add_handler(CommandHandler("start", arz.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, arz.take_price))
    
    application.run_webhook(
        listen='0.0.0.0',
        port=port,
        url_path='webhook',
        webhook_url=f"{webhook_url.rstrip('/')}/webhook"
    )
