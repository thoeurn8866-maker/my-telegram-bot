import os
import threading
import logging
import pandas as pd
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

# --- ផ្នែក Web Server សម្រាប់ Render Free Plan ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Alive!"

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

threading.Thread(target=keep_alive).start()
# --------------------------------------------------------

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SPOUSE_NAME, CHILDREN_NAME, CHILDREN_AGE = range(3)
EXCEL_FILE = "family_data.xlsx"

# ⚠️ ជំនួសលេខ 123456789 ដោយ Telegram User ID របស់បង (មើលពី @userinfobot)
ADMIN_USER_ID = 2127600841 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return ConversationHandler.END

    user_id = update.message.from_user.id
    user_first_name = update.message.from_user.first_name
    chat_type = update.message.chat.type

    # ---------------- ពិនិត្យមើលថា តើគាត់ធ្លាប់បំពេញព័ត៌មានរួចហើយឬនៅ ----------------
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            if 'Telegram User ID' in df.columns and user_id in df['Telegram User ID'].values:
                await update.message.reply_text(
                    f"⚠️ សុំទោស {user_first_name}! គណនីរបស់អ្នកបានបំពេញព័ត៌មាននៅក្នុងប្រព័ន្ធរួចរាល់ហើយ។\n"
                    f"អ្នកមិនអាចបញ្ចូលទិន្នន័យសាជាថ្មីម្តងទៀតបានទេ។"
                )
                return ConversationHandler.END
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")
    # --------------------------------------------------------------------------------

    # ប្រសិនបើចុច /start នៅក្នុង Telegram Group
    if chat_type in ['group', 'supergroup']:
        bot_username = context.bot.username
        # បង្កើតប៊ូតុងសម្រាប់ចុចទៅ Private Chat
        keyboard = [
            [InlineKeyboardButton("💬 ចុចទីនេះដើម្បីបំពេញព័ត៌មាន (Private)", url=f"https://t.me/{bot_username}?start=fill_data")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"ជម្រាបសួរ {user_first_name}! ដើម្បីរក្សាការសម្ងាត់ព័ត៌មាន សូមចុចប៊ូតុងខាងក្រោមដើម្បីបំពេញព័ត៌មាននៅក្នុង Chat ផ្ទាល់ជាមួយ Bot ៖",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # ប្រសិនបើនៅក្នុង Private Chat ចាប់ផ្តើមសួរសំណួរ
    await update.message.reply_text(
        f"ជម្រាបសួរ {user_first_name}! ខ្ញុំជា Bot សូមធ្វើបច្ចុប្បន្នភាពបញ្ជីឈ្មោះនៃចំនួនសហព័ន្ធ(ប្តី-ប្រពន្ធ ពុំមានមុខរបរ) និងកូនក្នុងបន្ទុក ដែលមានអាយុពី ១៥ឆ្នាំ ដល់២៥ឆ្នាំ(ជាសិស្ស-និស្សិត)  
        របស់ថ្នាក់ដឺកនាំ-និយោជិត ទ.ក. ទាំងអស់ គិតមកដល់ថ្ងៃ២៤-០៧-២០២៦។\n\n"
        f"សូមបញ្ចូល **ឈ្មោះប្តី ឬប្រពន្ធ** របស់អ្នក៖"
    )
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

    await update.message.reply_text(f"✅ បានរក្សាទុកទិន្នន័យរបស់ {user_name} ជោគជ័យ!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("បានបោះបង់ការបញ្ចូលទិន្នន័យ។")
    return ConversationHandler.END

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ សុំទោស! មានតែ Admin ប៉ុណ្ណោះដែលមានសិទ្ធិទាញយកឯកសារ Excel នេះ។")
        return

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
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            SPOUSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spouse_name)],
            CHILDREN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_children_name)],
            CHILDREN_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_to_excel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_user=True,
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('export', export_excel))

    app.run_polling()
