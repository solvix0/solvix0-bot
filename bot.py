import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import base64
import urllib.parse

# ==================== بياناتك الجاهزة ====================
BOT_TOKEN = "8476333752:AAF9uvZ6j7K_kt9hF-1mM5vBK4eN74p1PRk"  # توكن @solvix0_bot
AUTH_SERVER = "https://solvix0-auth-production.up.railway.app"  # سيرفرك

# لوغ للتصحيح
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # الكلمات بعد /start

    if args and args[0].startswith("auth_"):
        # استخراج رابط العودة
        encoded_url = args[0][5:]  # نحذف "auth_"
        try:
            redirect_url = base64.urlsafe_b64decode(encoded_url).decode('utf-8')
            redirect_url = urllib.parse.unquote(redirect_url)
        except Exception as e:
            await update.message.reply_text("❌ رابط العودة غير صالح.")
            logger.error(f"خطأ في فك التشفير: {e}")
            return

        # إرسال user.id إلى سيرفرك
        try:
            response = requests.post(
                f"{AUTH_SERVER}/tg-login",
                json={"uid": user.id},
                timeout=10
            )
            data = response.json()

            if "token" in data:
                await update.message.reply_html(
                    f"✅ <b>تم تسجيل الدخول بنجاح!</b>\n\n"
                    f"يمكنك الآن العودة إلى تطبيق Solvix0.\n\n"
                    f"<a href='{redirect_url}'>🔙 اضغط هنا للعودة تلقائياً</a>",
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    "❌ عذراً، أنت غير عضو في المجموعة الرسمية.\n\n"
                    "انضم إلى المجموعة أولاً ثم عد وحاول مرة أخرى."
                )
        except Exception as e:
            logger.error(f"خطأ في الاتصال بالسيرفر: {e}")
            await update.message.reply_text("⚠️ حدث خطأ مؤقت، حاول مرة أخرى بعد قليل.")
    else:
        # رسالة ترحيب عادية
        await update.message.reply_html(
            f"👋 مرحباً <b>{user.first_name}</b>!\n\n"
            f"أنا بوت تسجيل الدخول الخاص بتطبيق <b>Solvix0</b>.\n\n"
            f"إذا تم توجيهك إليّ من التطبيق، اضغط /start مرة أخرى أو عد إلى التطبيق.\n\n"
            f"للدعم: @baraka784"
        )

def main():
    print("البوت @solvix0_bot يعمل الآن بنجاح 🚀")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()