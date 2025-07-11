import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes, CallbackQueryHandler
)

(COMPANY, EMAIL, PHONE, HAS_CHANNEL) = range(4)

ADMIN_CHANNEL = "@rakbriut"
WELCOME_IMG_URL = "https://wlab.co.il/wp-content/uploads/2025/07/bot-cover.jpg"
BACK_TO_CHANNEL_LINK = "https://t.me/rakbriut"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=WELCOME_IMG_URL
    )
    await update.message.reply_text(
        "👋🏻 <b>ברוך/ה הבא/ה ל-PostAd!</b>\n"
        "פלטפורמת הפרסום המובילה בטלגרם ללידים חכמים.\n\n"
        "אנא השלם/י את הפרטים (1/4):\n"
        "🏢 <b>שם החברה</b>",
        parse_mode="HTML"
    )
    return COMPANY

async def company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    company_name = update.message.text.strip()
    if not company_name or len(company_name) < 2:
        await update.message.reply_text("❗️נא להכניס שם חברה תקין (לפחות 2 תווים):")
        return COMPANY
    context.user_data["company"] = company_name
    await update.message.reply_text(
        "📧 (2/4) <b>אימייל ליצירת קשר</b>",
        parse_mode="HTML"
    )
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_email = update.message.text.strip()
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_pattern, user_email) or len(user_email) > 100:
        await update.message.reply_text(
            "❗️כתובת אימייל לא תקינה. אנא נסה/י שוב:"
        )
        return EMAIL
    context.user_data["email"] = user_email
    await update.message.reply_text(
        "📞 (3/4) <b>מספר טלפון</b>",
        parse_mode="HTML"
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    # אפשרות לולידציה בסיסית: 9-12 ספרות, רק מספרים (ישראל/בינ"ל)
    if not re.match(r"^[\d\-\+ ]{8,14}$", phone):
        await update.message.reply_text(
            "❗️נא להכניס מספר טלפון תקין (רק ספרות, מינימום 8 תווים):"
        )
        return PHONE
    context.user_data["phone"] = phone
    keyboard = [
        [InlineKeyboardButton("✅ כן", callback_data='yes'), InlineKeyboardButton("❌ לא", callback_data='no')]
    ]
    await update.message.reply_text(
        "📢 (4/4) <b>האם יש לחברה ערוץ טלגרם?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return HAS_CHANNEL

async def has_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    has_channel = "כן" if query.data == "yes" else "לא"
    context.user_data["has_channel"] = has_channel

    lead_text = (
        "📥 <b>ליד חדש מבוט PostAd:</b>\n"
        f"🏢 <b>שם החברה:</b> {context.user_data['company']}\n"
        f"📧 <b>אימייל:</b> {context.user_data['email']}\n"
        f"📞 <b>טלפון:</b> {context.user_data['phone']}\n"
        f"📢 <b>האם יש ערוץ טלגרם:</b> {context.user_data['has_channel']}\n"
        f"👤 <b>טלגרם:</b> @{query.from_user.username if query.from_user.username else '---'}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHANNEL, text=lead_text, parse_mode="HTML")

    await query.edit_message_text(
        "✅ <b>תודה! הפרטים התקבלו בהצלחה.</b>\n"
        "צוות השיווק שלנו יחזור אליך בקרוב.\n\n"
        "🔗 לחזרה אל ערוץ הפרסום:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 מעבר לערוץ", url=BACK_TO_CHANNEL_LINK)]
        ])
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ הפעולה בוטלה. יום נעים!")
    context.user_data.clear()
    return ConversationHandler.END

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    print("TOKEN:", repr(token))
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
