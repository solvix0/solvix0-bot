import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import base64
import urllib.parse

# بياناتك
BOT_TOKEN = "8476333752:AAF9uvZ6j7K_kt9hF-1mM5vBK4eN74p1PRk"
AUTH_SERVER = "https://solvix0-auth-production.up.railway.app"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if args and args[0].startswith("auth_"):
        encoded_url = args[0][5:]
        try:
            redirect_url = base64.urlsafe_b64decode(encoded_url + '===').decode('utf-8')  # padding fix
            redirect_url = urllib.parse.unquote(redirect_url)
        except Exception as e:
            logger.error(f"Decode error: {e}")
            await update.message.reply_text("❌ رابط غير صالح.")
            return

        try:
            response = requests.post(f"{AUTH_SERVER}/tg-login", json={"uid": user.id}, timeout=10)
            data = response.json()

            if "token" in data:
                await update.message.reply_html(
                    f"✅ <b>تم تسجيل الدخول بنجاح!</b>\n\n"
                    f"🔙 <a href='{redirect_url}'>اضغط هنا للعودة إلى Solvix0</a>",
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    "❌ عذراً، أنت غير عضو في المجموعة الرسمية.\n"
                    "انضم أولاً ثم عُد وحاول مجدداً."
                )
        except Exception as e:
            logger.error(f"Server error: {e}")
            await update.message.reply_text("⚠️ خطأ مؤقت، حاول لاحقاً.")
    else:
        await update.message.reply_html(
            f"👋 مرحباً <b>{user.first_name}</b>!\n\n"
            f"بوت تسجيل الدخول لتطبيق <b>Solvix0</b>\n\n"
            f"للدعم: @solvix0"
        )

def main():
    print("🚀 البوت @solvix0_bot يعمل الآن بنجاح!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # الطريقة الصحيحة لـ Railway (بدون asyncio.run)
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
