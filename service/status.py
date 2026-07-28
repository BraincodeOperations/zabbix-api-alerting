from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# ...

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Status bot : Running 🟢")

# setelah bikin Application
app.add_handler(CommandHandler("status", status))