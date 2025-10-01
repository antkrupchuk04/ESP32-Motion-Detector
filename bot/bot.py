import os
import requests
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Налаштування ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SERVER_URL = os.environ.get("FLASK_SERVER_URL")  # URL до вашого Flask-сервера

# Головне меню
main_menu = ReplyKeyboardMarkup([
    [KeyboardButton("Показати останні 5 подій руху")],
    [KeyboardButton("Start")]
], resize_keyboard=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Виберіть дію з меню нижче:", reply_markup=main_menu)

# Показ останніх 5 подій руху
async def show_latest_motion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(f"{SERVER_URL}/motion/latest", timeout=5)
        if response.status_code == 200:
            data = response.json().get("latest_events", [])
            if not data:
                message = "Записів не знайдено."
            else:
                message = "Останні 5 подій руху:\n"
                for event in data:
                    ts_raw = event.get("timestamp")
                    motion = event.get("motion")

                    # Конвертація часу +3 години
                    try:
                        ts_dt = datetime.strptime(ts_raw, "%a, %d %b %Y %H:%M:%S %Z")
                        ts_dt += timedelta(hours=3)
                        ts_formatted = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        ts_formatted = ts_raw

                    message += f"- {ts_formatted}: {'⚠️ Рух' if motion else '❌ Немає руху'}\n"
        else:
            message = "Помилка при отриманні даних з сервера."
    except Exception as e:
        message = f"⚠️ Помилка: {e}"

    await update.message.reply_text(message, reply_markup=main_menu)

# Обробка вибору меню
async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Показати останні 5 подій руху":
        await show_latest_motion(update, context)
    elif text == "Start":
        await start(update, context)
    else:
        await update.message.reply_text("Невідомий вибір.", reply_markup=main_menu)

# Головна функція
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Показати останні 5 подій руху|Start)$"), handle_menu_choice))

    print("Бот працює...")
    app.run_polling()

if __name__ == "__main__":
    main()
