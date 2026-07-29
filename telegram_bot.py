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

HEAD_NAME, SPOUSE_NAME, CHILD_INFO = range(3)
EXCEL_FILE = "family_data.xlsx"

# ⚠️ ជំនួសលេខ ID Admin របស់អ្នកនៅទីនេះ
ADMIN_USER_ID = 2127600841 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return ConversationHandler.END

    user_id = update.message.from_user.id
    user_first_name = update.message.from_user.first_name

    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            if 'Telegram User ID' in df.columns and user_id in df['Telegram User ID'].values:
                await update.message.reply_text(
                    f"⚠️ **ជម្រាបសួរ {user_first_name}!** គណនីរបស់អ្នកបានបំពេញព័ត៌មាននៅក្នុងប្រព័ន្ធរួចរាល់ហើយ។\n\n"
                    f"ប្រសិនបើចង់កែប្រែព័ត៌មាន សូមទាក់ទងទៅ Admin។"
                )
                return ConversationHandler.END
        except Exception as e:
            logging.error(f"Error reading Excel file: {e}")

    await update.message.reply_text(
        f"ជម្រាបសួរ {user_first_name}! នេះជាប្រព័ន្ធប្រមូលទិន្នន័យបច្ចុប្បន្នភាពសហព័ន្ធ និងកូនក្នុងបន្ទុក។\n\n"
        f"១. សូមបញ្ចូល **ឈ្មោះពេញរបស់មន្ត្រី/បុគ្គលិក (ម្ចាស់សាមីខ្លួន)** ៖"
    )
    return HEAD_NAME

async def get_head_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['head_name'] = update.message.text
    await update.message.reply_text(
        "២. សូមបញ្ចូល **ឈ្មោះសហព័ន្ធ (ប្តី ឬប្រពន្ធ) ដែលគ្មានមុខរបរ** ៖\n"
        "*(ចំណាំ៖ ប្រសិនបើគ្មាន ឬសហព័ន្ធមានមុខរបរ សូមវាយពាក្យថា 'គ្មាន')*"
    )
    return SPOUSE_NAME

async def get_spouse_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['spouse_name'] = update.message.text
    await update.message.reply_text(
        "៣. សូមបញ្ចូល **ព័ត៌មានកូនក្នុងបន្ទុក អាយុ ១៥ ដល់ ២៥ ឆ្នាំ (ជាសិស្ស-និស្សិត)** ៖\n\n"
        "រៀបរាប់តាមទម្រង់៖ `ឈ្មោះកូន - អាយុ - កំពុងសិក្សាថ្នាក់/សាលា`\n"
        "*(ឧទាហរណ៍៖ សុខ ចាន់ - ១៨ ឆ្នាំ - សិស្សវិទ្យាល័យ)*\n\n"
        "*(ប្រសិនបើគ្មានកូនក្នុងលក្ខខណ្ឌនេះទេ សូមវាយពាក្យថា 'គ្មាន')*"
    )
    return CHILD_INFO

async def save_to_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['child_info'] = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name

    new_data = {
        'Telegram User ID': [user_id],
        'អ្នកបញ្ចូលទិន្នន័យ': [user_name],
        'ឈ្មោះមន្ត្រី/បុគ្គលិក': [context.user_data['head_name']],
        'សហព័ន្ធគ្មានមុខរបរ (ប្តី/ប្រពន្ធ)': [context.user_data['spouse_name']],
        'ព័ត៌មានកូនបន្ទុក (អាយុ ១៥-២៥ ឆ្នាំ ជាសិស្ស-និស្សិត)': [context.user_data['child_info']]
    }
    
    df_new = pd.DataFrame(new_data)

    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(EXCEL_FILE, index=False)
    else:
        df_new.to_excel(EXCEL_FILE, index=False)

    await update.message.reply_text(f"✅ **បានរក្សាទុកទិន្នន័យបច្ចុប្បន្នភាពរបស់ {context.user_data['head_name']} ជោគជ័យ!**")
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
            caption="📊 នេះជាបញ្ជីឈ្មោះបច្ចុប្បន្នភាព!"
        )
    else:
        await update.message.reply_text("មិនទាន់មានទិន្នន័យនៅឡើយទេ។")

async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        return

    if os.path.exists(EXCEL_FILE):
        os.remove(EXCEL_FILE)
        await update.message.reply_text("🧹 បានលុបទិន្នន័យចាស់រៀបរយ!")
    else:
        await update.message.reply_text("គ្មានទិន្នន័យត្រូវលុបទេ។")

# ----------------- 🗑️ FEATURE ថ្មី៖ លុបសមាជិកជាក់លាក់ -----------------
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ សុំទោស! មានតែ Admin ប៉ុណ្ណោះដែលមានសិទ្ធិប្រើ Command នេះ។")
        return

    if not context.args:
        await update.message.reply_text("⚠️ សូមវាយបញ្ចូល ID ដែលត្រូវលុប។\nឧទាហរណ៍៖ `/delete_user 123456789`", parse_mode="Markdown")
        return

    target_id = int(context.args[0])

    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        if 'Telegram User ID' in df.columns and target_id in df['Telegram User ID'].values:
            # លុបបន្ទាត់ទិន្នន័យដែលមាន ID នោះចេញ
            df = df[df['Telegram User ID'] != target_id]
            df.to_excel(EXCEL_FILE, index=False)
            await update.message.reply_text(f"🗑️ បានលុបទិន្នន័យសមាជិកដែលមាន ID `{target_id}` ចេញពីប្រព័ន្ធជោគជ័យ!\nឥឡូវគាត់អាចចូលបំពេញឡើងវិញបាន។", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ រកមិនឃើញ ID `{target_id}` នៅក្នុងបញ្ជី Excel ទេ។", parse_mode="Markdown")
    else:
        await update.message.reply_text("មិនទាន់មានទិន្នន័យនៅឡើយទេ។")
# ------------------------------------------------------------------------

if __name__ == '__main__':
    # ⚠️ ជំនួស Token របស់បងនៅទីនេះ
    TOKEN = '8600631446:AAHIC7AHYdisa34d48peLaHgOdF-xzb4IfM'

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
        ],
        states={
            HEAD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_head_name)],
            SPOUSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_spouse_name)],
            CHILD_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_to_excel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_user=True,
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('export', export_excel))
    app.add_handler(CommandHandler('reset', reset_data))
    app.add_handler(CommandHandler('delete_user', delete_user))

    app.run_polling()
