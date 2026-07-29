import logging
import os
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# បើក Logs សម្រាប់មើល Error
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# កំណត់ជំហាននៃកិច្ចសន្ទនា (Conversation States)
SPOUSE_NAME, CHILDREN_NAME, CHILDREN_AGE = range(3)

EXCEL_FILE = "family_data.xlsx"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ចាប់ផ្តើមសួរព័ត៌មាន"""
    await update.message.reply_text(
        "ជម្រាបសួរ! ខ្ញុំជា Bot សម្រាប់កត់ត្រាទិន្នន័យគ្រួសារ។\n\n"
        "សូមបញ្ចូល **ឈ្មោះប្តី ឬប្រពន្ធ** របស់អ្នក៖"
    )
    return SPOUSE_NAME


async def get_spouse_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """រក្សាទុកឈ្មោះប្តី/ប្រពន្ធ រួចសួរឈ្មោះកូន"""
    context.user_data['spouse_name'] = update.message.text
    
    await update.message.reply_text(
        "សូមអរគុណ! បន្ទាប់មក សូមបញ្ចូល **ឈ្មោះកូន** របស់អ្នក "
        "(បើមានកូនច្រើន សូមសរសេររៀបរាប់ ដោយប្រើសញ្ញាក្បៀស `,` បំបែក)៖"
    )
    return CHILDREN_NAME


async def get_children_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """រក្សាទុកឈ្មោះកូន រួចសួរអាយុកូន"""
    context.user_data['children_name'] = update.message.text
    
    await update.message.reply_text(
        "សូមបញ្ចូល **អាយុរបស់កូន** "
        "(ឧទាហរណ៍៖ ៥ ឆ្នាំ, ៨ ឆ្នាំ ឬសរសេរតាមលំដាប់ឈ្មោះកូន)៖"
    )
    return CHILDREN_AGE


async def save_to_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """រក្សាទុកអាយុកូន រួច Export ទិន្នន័យទាំងអស់ចូល Excel"""
    context.user_data['children_age'] = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name

    # បង្កើត Dictionary នៃទិន្នន័យដែលបានប្រមូល
    new_data = {
        'Telegram User ID': [user_id],
        'អ្នកបញ្ចូលទិន្នន័យ': [user_name],
        'ឈ្មោះប្តី/ប្រពន្ធ': [context.user_data['spouse_name']],
        'ឈ្មោះកូន': [context.user_data['children_name']],
        'អាយុកូន': [context.user_data['children_age']]
    }
    
    df_new = pd.DataFrame(new_data)

    # បើមានឯកសារ Excel រួចហើយ ត្រូវបន្ថែមទិន្នន័យថ្មីចូល បើមិនទាន់មាន ត្រូវបង្កើតថ្មី
    if os.path.exists(EXCEL_FILE):
        df_existing = pd.read_excel(EXCEL_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(EXCEL_FILE, index=False)
    else:
        df_new.to_excel(EXCEL_FILE, index=False)

    await update.message.reply_text(
        "✅ **បានរក្សាទុកទិន្នន័យជោគជ័យ!**\n\n"
        "អ្នកអាចវាយបញ្ជា `/export` ដើម្បីទាញយកឯកសារ Excel បានគ្រប់ពេល។\n"
        "ឬវាយ `/start` ដើម្បបញ្ចូលទិន្នន័យថ្មីម្តងទៀត។"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """បោះបង់ការបញ្ចូលទិន្នន័យ"""
    await update.message.reply_text("បានបោះបង់ប្រតិបត្តិការ។", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ផ្ញើឯកសារ Excel ទៅកាន់អ្នកប្រើប្រាស់"""
    if os.path.exists(EXCEL_FILE):
        await update.message.reply_document(
            document=open(EXCEL_FILE, 'rb'),
            filename=EXCEL_FILE,
            caption="📊 នេះជាឯកសារ Excel ទិន្នន័យដែលបានប្រមូល!"
        )
    else:
        await update.message.reply_text("មិនទាន់មានទិន្នន័យនៅក្នុងប្រព័ន្ធនៅឡើយទេ។ សូមវាយ `/start` ដើម្បីបញ្ចូលទិន្នន័យ។")


if __name__ == '__main__':
    # ដាក់ Token របស់ Bot អ្នកនៅទីនេះ
    TOKEN = '8600631446:AAHIC7AHYdisa34d48peLaHgOdF-xzb4IfM'

    app = ApplicationBuilder().token(TOKEN).build()

    # កំណត់ Conversation Handler សម្រាប់ការសួរសំណួរតាមលំដាប់
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

    print("Bot កំពុងដំណើរការ...")
    app.run_polling()