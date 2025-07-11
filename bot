import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes, CallbackQueryHandler
)

(COMPANY, EMAIL, PHONE, HAS_CHANNEL) = range(4)

ADMIN_CHANNEL = "@rakbriut"  # הערוץ החדש
WELCOME_IMG_URL = "https://cdn.prod.website-files.com/68529250c93c3df9b3d2a728/685f20f981c6304043571f33_logo-svg.svg"
BACK_TO_CHANNEL_LINK = "https://t.me/rakbriut"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=WELCOME_IMG_URL)
    await update.message.reply_text(
        "תודה שהתעניינת בפוסט-אד – פלטפורמת הפרסום המובילה בטלגרם לתוצאות מבוססות ביצועים.\n\n"
        "אנא שתף/י מידע קצר:\n"
        "1. שם החברה"
    )
    return COMPANY

async def company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company"] = update.message.text
    await update.message.reply_text("2. אימייל")
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("3. מספר טלפון")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("כן", callback_data='yes'), InlineKeyboardButton("לא", callback_data='no')]
    ]
    await update.message.reply_text(
        "4. האם יש לחברה ערוץ טלגרם?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return HAS_CHANNEL

async def has_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    has_channel = "כן" if query.data == "yes" else "לא"
    context.user_data["has_channel"] = has_channel

    lead_text = (
        "📥 ליד חדש מבוט PostAd:\n"
        f"שם החברה: {context.user_data['company']}\n"
        f"אימייל: {context.user_data['email']}\n"
        f"טלפון: {context.user_data['phone']}\n"
        f"האם יש ערוץ טלגרם: {context.user_data['has_channel']}\n"
        f"טלגרם: @{query.from_user.username if query.from_user.username else '---'}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHANNEL, text=lead_text)

    await query.edit_message_text(
        "✅ תודה על שיתוף הפרטים! צוות השיווק שלנו יחזור אליך בקרוב.\n\n"
        "לחזרה אל ערוץ הפרסום:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("חזור אל ערוץ הפרסום", url=BACK_TO_CHANNEL_LINK)]
        ])
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("בוט הופסק. יום נעים!")
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    print("TOKEN:", repr(token))  # לשורת דיבאג בלוג
    if not token:
        print("שגיאה: לא הוגדר טוקן בוט. ודא שהגדרת TELEGRAM_BOT_TOKEN במשתני הסביבה!")
        exit(1)

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, company)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            HAS_CHANNEL: [CallbackQueryHandler(has_channel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)

    print("הבוט עלה בהצלחה ומוכן לקבל לידים!")
    app.run_polling()

if __name__ == "__main__":
    main()
