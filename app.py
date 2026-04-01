import os
import io
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from spam_engine import scan_for_spam, scan_emails

load_dotenv()
SUDO_USERS = [int(id.strip()) for id in os.getenv("SUDO_USERS", "").split(",") if id.strip()]

def is_sudo(update: Update) -> bool:
    return update.effective_user.id in SUDO_USERS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update): return
    await update.message.reply_text("Welcome! Type /scan to check your Gmail.")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update): return

    status = await update.message.reply_text("🔍 Scanning emails...")
    
    try:
        result = await asyncio.to_thread(scan_for_spam)
        
        if isinstance(result, dict):
            report_text = str(result.get("text", result))
        else:
            report_text = str(result)

        if len(report_text) < 500:
            await status.edit_text(f"✅ **Report**\n\n{report_text}", parse_mode='Markdown')
        else:
            await status.edit_text("📄 Report is large. Sending as a text file...")
            
            output = io.BytesIO(report_text.encode('utf-8'))
            output.name = "gmail_spam_report.txt"
            
            await update.message.reply_document(
                document=output,
                caption="✅ Full Gmail Scan Report (Detailed)"
            )

    except Exception as e:
        err_msg = str(e)[:200]
        await status.edit_text(f"❌ Error: {err_msg}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update): return

    user_query = " ".join(context.args)

    if not user_query:
        await update.message.reply_text("❌ Please provide a search term. Example: `/search GitHub`")
        return

    status = await update.message.reply_text(f"🔍 Searching for: **{user_query}**...", parse_mode='Markdown')
    
    try:
        result = await asyncio.to_thread(scan_emails, user_query)
        
        report_text = str(result)

        if len(report_text) < 500:
            await status.edit_text(f"✅ **Results**\n\n{report_text}", parse_mode='Markdown')
        else:
            await status.edit_text("📄 Results are long. Sending file...")
            output = io.BytesIO(report_text.encode('utf-8'))
            output.name = f"search_{user_query}.txt"
            await update.message.reply_document(document=output)

    except Exception as e:
        await status.edit_text(f"❌ Search Error: {str(e)[:100]}")

if __name__ == "__main__":
    token = os.getenv("BOT_FATHER_TOKEN")
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("search",search_command))
    
    print(f"Bot started. Sudo users: {SUDO_USERS}")
    app.run_polling()
