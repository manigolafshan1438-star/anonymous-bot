print("hello")
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


# =========================
# تنظیمات بات
# =========================

BOT_TOKEN = "8783954430:AAHoin_ebjnJ6KR7hTKOx3xGnmTLHK2mFjU"

# آیدی عددی تلگرام خودت
ADMIN_ID = 1452364528


WELCOME_TEXT = (
    "به چت ناشناس مانی خوش اومدی 🌹\n\n"
    "هر چیزی بخوای میتونی بفرستی:\n"
    "پیامت به صورت ناشناس برای مانی ارسال میشه."
)


# =========================
# ذخیره ارتباط پیام و کاربر
# =========================

MAP_FILE = "reply_map.json"
MAX_MAP_SIZE = 20000


def load_map():
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    return {}


def save_map(data):
    if len(data) > MAX_MAP_SIZE:
        old_keys = list(data.keys())[
            :len(data) - MAX_MAP_SIZE
        ]

        for key in old_keys:
            del data[key]

    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


REPLY_MAP = load_map()


# =========================
# دستور /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(WELCOME_TEXT)


# =========================
# کاربر → ادمین
# =========================

async def user_to_admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    msg = update.message

    if not msg:
        return

    user = update.effective_user

    username = (
        f"@{user.username}"
        if user.username
        else "ندارد"
    )

    try:

        header = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📩 پیام جدید\n\n"
                f"👤 نام: {user.full_name}\n"
                f"🔗 یوزرنیم: {username}\n"
                f"🆔 آیدی: {user.id}\n"
                f"📎 لینک پروفایل:\n"
                f"tg://user?id={user.id}"
            ),
        )

        copied = await context.bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
        )

    except TelegramError:

        await msg.reply_text(
            "❌ ارسال پیام ناموفق بود."
        )

        return

    # ذخیره ارتباط پیام ادمین با کاربر

    REPLY_MAP[str(header.message_id)] = user.id

    REPLY_MAP[str(copied.message_id)] = user.id

    save_map(REPLY_MAP)

    await msg.reply_text(
        "✅ پیامت برای مانی ارسال شد."
    )


# =========================
# ادمین → کاربر
# =========================

async def admin_to_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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


# =========================
# اجرای بات
# =========================

def main():

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    # دستور start

    app.add_handler(
        CommandHandler(
            "start",
            start,
            filters.ChatType.PRIVATE
        )
    )

    # فقط پیام‌های خصوصی

    private_messages = (
        filters.ChatType.PRIVATE
        & ~filters.COMMAND
    )

    # پیام‌های ادمین

    app.add_handler(
        MessageHandler(
            private_messages
            & filters.User(ADMIN_ID),
            admin_to_user
        )
    )

    # پیام‌های کاربران

    app.add_handler(
        MessageHandler(
            private_messages
            & ~filters.User(ADMIN_ID),
            user_to_admin
        )
    )

    print("🤖 Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()