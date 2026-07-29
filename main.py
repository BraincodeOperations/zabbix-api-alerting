import logging
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TOKEN
from service.zabbix.polling import main
from service.zabbix.polling_curr_problems import main as current_problem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    username = update.effective_user.username
    full_name = update.effective_user.full_name

    logging.info(
        f"/status | chat_id={chat_id} | type={chat_type} | user={full_name} (@{username})"
    )

    await update.message.reply_text("Status bot : Running 🟢")

def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("status", status))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=main, daemon=True).start()
    threading.Thread(target=current_problem, daemon=True).start()

    # bot dijalankan di main thread
    run_bot()