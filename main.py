import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN
from polling import main


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Status bot : Running 🟢")


def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("status", status))
    app.run_polling()


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    main()