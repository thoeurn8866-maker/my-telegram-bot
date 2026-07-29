import os
import threading
import logging
import pandas as pd
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

# --- ផ្នែកបង្កើត Fake Web Server សម្រាប់ Render Free Plan ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Alive!"

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# ដំឡើង Web Server ឱ្យដើរអមជាមួយ Bot
threading.Thread(target=keep_alive).start()
# --------------------------------------------------------

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SPOUSE_NAME, CHILDREN_NAME, CHILDREN_AGE = range(3)
EXCEL_FILE = "family_data.xlsx"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ជម្រាបសួរ! សូមបញ្ចូល **ឈ្មោះប្តី ឬប្រពន្ធ** របស់អ្នក៖")
    return SPOUSE_NAME

async def get_spouse_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['spouse_name'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **ឈ្មោះកូន** របស់អ្នក (បើមានច្រើន បំបែកដោយសញ្ញាក្បៀស `,`)៖")
    return CHILDREN_NAME

async def get_children_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['children_name'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **អាយុរបស់កូន**៖")
    return CHILDREN_AGE

async def save_to_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['children_age'] = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name

    new_data = {
        'Telegram User ID': [user_id],
        'អ្នកបញ្ចូលទិន្នន័យ': [user_name],
        'ឈ្មោះប្តី/ប្រពន្ធ': [context.user_data['spouse_name']],
        'ឈ្មោះកូន': [context.user_data['children_name']],
        'អាយុកូន': [context.user_data['children_age']]
    }
    
    df_new = pd.DataFrame(new_data)

    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(EXCEL_FILE, index=False)
    else:
        df_new.to_excel(EXCEL_FILE, index=False)

    await update.message.reply_text("✅ **បានរក្សាទុកទិន្នន័យជោគជ័យ!**\nវាយ `/export` ដើម្បីទាញយក Excel។")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("បានបោះបង់ប្រតិបត្តិការ។")
    return ConversationHandler.END

# ⚠️ ជំនួសលេខ 123456789 ដោយ Telegram User ID ពិតប្រាកដរបស់បង (ជាលេខ)
ADMIN_USER_ID = 2127600841 

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # ពិនិត្យមើលថា តើអ្នកដែលវាយ /export ជា Admin ដែរឬទេ?
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ សុំទោស! មានតែ Admin ប៉ុណ្ណោះដែលមានសិទ្ធិទាញយកឯកសារ Excel នេះបាន។")
        return

    # ប្រសិនបើជា Admin ឱ្យទាញយកបានធម្មតា
    if os.path.exists(EXCEL_FILE):
        await update.message.reply_document(
            document=open(EXCEL_FILE, 'rb'),
            filename=EXCEL_FILE,
            caption="📊 នេះជាឯកសារ Excel ទិន្នន័យដែលបានប្រមូល!"
        )
    else:
        await update.message.reply_text("មិនទាន់មានទិន្នន័យនៅឡើយទេ។")

if __name__ == '__main__':
    # ⚠️ ជំនួស Token របស់បងនៅទីនេះ
    TOKEN = '8600631446:AAHIC7AHYdisa34d48peLaHgOdF-xzb4IfM'

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SPOUSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spouse_name)],
            CHILDREN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_children_name)],
            CHILDREN_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_to_excel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('export', export_excel))

    app.run_polling()
