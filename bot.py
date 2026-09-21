import json
import os

from telegram import Update
from telegram.error import Forbidden, TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1452364528

WELCOME_TEXT = (
    "به چت ناشناس مانی خوش اومدی 🌹\n\n"
    "هر چیزی بخوای می‌تونی بفرستی: متن، ویس، عکس، فیلم، استیکر، فایل و ...\n"
    "پیامت به صورت ناشناس برای مانی ارسال میشه."
)

MAP_FILE = "reply_map.json"
MAX_MAP_SIZE = 20000


def load_map() -> dict:
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_map(data: dict) -> None:
    if len(data) > MAX_MAP_SIZE:
        for key in list(data.keys())[:len(data) - MAX_MAP_SIZE]:
            del data[key]

    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


REPLY_MAP = load_map()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(WELCOME_TEXT)


async def user_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg:
        return

    user = update.effective_user

    if not user:
        return

    try:
        header = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📩 پیام جدید\n\n"
                f"🆔 ID: {user.id}\n\n"
                "↩️ برای پاسخ، روی پیام ناشناس Reply کن."
            ),
        )

        copied = await context.bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )

        REPLY_MAP[str(header.message_id)] = user.id
        REPLY_MAP[str(copied.message_id)] = user.id

        save_map(REPLY_MAP)

        await msg.reply_text(
            "✅ پیامت برای مانی ارسال شد."
        )

    except TelegramError:
        await msg.reply_text(
            "❌ ارسال پیام ناموفق بود، بعداً دوباره تلاش کن."
        )


async def admin_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if not msg:
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "برای جواب دادن، روی پیام کاربر ریپلای کن ↩️"
        )
        return

    target_id = REPLY_MAP.get(
        str(msg.reply_to_message.message_id)
    )

    if not target_id:
        await msg.reply_text(
            "❌ کاربر این پیام پیدا نشد."
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=target_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )

        await msg.reply_text(
            "✅ ارسال شد."
        )

    except Forbidden:
        await msg.reply_text(
            "❌ این کاربر ربات را بلاک کرده."
        )

    except TelegramError:
        await msg.reply_text(
            "❌ ارسال ناموفق بود."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN در Railway تنظیم نشده است."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start,
            filters.ChatType.PRIVATE
        )
    )

    private_messages = (
        filters.ChatType.PRIVATE
        & ~filters.COMMAND
    )

    app.add_handler(
        MessageHandler(
            private_messages & filters.User(ADMIN_ID),
            admin_to_user
        )
    )

    app.add_handler(
        MessageHandler(
            private_messages & ~filters.User(ADMIN_ID),
            user_to_admin
        )
    )

    print("🤖 Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
