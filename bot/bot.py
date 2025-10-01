import os
import requests
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Telegram Bot Token ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# --- Ваш Flask сервер (де розгорнутий ендпоінт) ---
FLASK_SERVER_URL = os.environ.get("FLASK_SERVER_URL")  # Наприклад: http://yourserver.com:12345

KYIV_TZ = pytz.timezone("Europe/Kiev")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Останні 5 подій руху", callback_data="latest_motion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Виберіть дію:", reply_markup=reply_markup)

# Обробка натискання кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "latest_motion":
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/motion/latest", timeout=5)
            if response.status_code == 200:
                data = response.json().get("latest_events", [])
                if not data:
                    text = "Записів не знайдено."
                else:
                    text = "Останні 5 подій руху:\n"
                    for event in data:
                        ts_str = event.get("timestamp")
                        motion = event.get("motion")

                        # Конвертація у datetime + Kyiv timezone
                        try:
                            ts_utc = datetime.fromisoformat(ts_str)  # з рядка ISO з сервера
                            ts_kyiv = ts_utc.astimezone(KYIV_TZ)
                            ts_formatted = ts_kyiv.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            ts_formatted = ts_str  # якщо конвертація не вдасться

                        text += f"- {ts_formatted}: {'⚠️ Рух' if motion else '❌ Немає руху'}\n"
            else:
                text = "Помилка при отриманні даних з сервера."
        except Exception as e:
            text = f"Помилка: {e}"

        await query.edit_message_text(text=text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()
