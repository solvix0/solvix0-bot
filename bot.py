import asyncio
import base64
import logging
import os
import urllib.parse

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
AUTH_SERVER = os.getenv("AUTH_SERVER", "https://solvix0-auth-production.up.railway.app")
REQUEST_TIMEOUT_SECONDS = 10

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Raised when an auth flow step fails."""


def decode_redirect_url(encoded_value: str) -> str:
    """Decode deep-link redirect value from url-safe base64 to URL string."""
    if not encoded_value:
        raise AuthError("missing_redirect")

    padded_value = encoded_value + "=" * (-len(encoded_value) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded_value).decode("utf-8")
    except Exception as exc:
        raise AuthError("invalid_redirect_encoding") from exc

    redirect_url = urllib.parse.unquote(decoded).strip()
    parsed = urllib.parse.urlparse(redirect_url)
    if parsed.scheme not in {"http", "https"}:
        raise AuthError("unsupported_redirect_scheme")

    return redirect_url


def _post_login(uid: int) -> dict:
    response = requests.post(
        f"{AUTH_SERVER}/tg-login",
        json={"uid": uid},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise AuthError("invalid_server_response")
    return payload


async def fetch_auth_payload(uid: int) -> dict:
    try:
        return await asyncio.to_thread(_post_login, uid)
    except requests.HTTPError as exc:
        logger.warning("Auth server returned HTTP error: %s", exc)
        raise AuthError("auth_http_error") from exc
    except requests.RequestException as exc:
        logger.error("Auth server request failed: %s", exc)
        raise AuthError("auth_connection_error") from exc


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    args = context.args

    if not update.message:
        return

    if args and args[0].startswith("auth_"):
        encoded_url = args[0][5:]
        try:
            redirect_url = decode_redirect_url(encoded_url)
            data = await fetch_auth_payload(user.id)
        except AuthError as exc:
            reason = str(exc)
            if reason.startswith("invalid_redirect") or reason.startswith("unsupported_redirect") or reason == "missing_redirect":
                await update.message.reply_text("❌ رابط غير صالح.")
            else:
                await update.message.reply_text("⚠️ خطأ مؤقت في الخادم، حاول لاحقاً.")
            return

        if data.get("token"):
            await update.message.reply_html(
                "✅ <b>تم تسجيل الدخول بنجاح!</b>\n\n"
                f"🔙 <a href='{redirect_url}'>اضغط هنا للعودة إلى Solvix0</a>",
                disable_web_page_preview=True,
            )
            return

        await update.message.reply_text(
            "❌ عذراً، أنت غير عضو في المجموعة الرسمية.\n"
            "انضم أولاً ثم عُد وحاول مجدداً."
        )
        return

    await update.message.reply_html(
        f"👋 مرحباً <b>{user.first_name}</b>!\n\n"
        "بوت تسجيل الدخول الاحترافي لتطبيق <b>Solvix0</b>\n\n"
        "للبدء استخدم رابط تسجيل الدخول من التطبيق.\n"
        "للدعم: @solvix0"
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required. Set it as an environment variable.")

    logger.info("🚀 البوت @solvix0_bot يعمل الآن بنجاح")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
