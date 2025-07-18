import os
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes, CallbackQueryHandler
)

# --- Configuration Constants ---
(FIRST_NAME, LAST_NAME, EMAIL, PHONE, PRIVATE_INSURANCE) = range(5)
ADMIN_CHANNEL = "@rakbriut"
BACK_TO_CHANNEL_LINK = "https://t.me/rakbriut"
CRM_API_URL = "https://api.scallacrm.co.il//modules/Webforms/capture.php"

# --- Conversation Handlers (start, first_name, last_name, email, phone functions remain unchanged) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://wlab.co.il/wp-content/uploads/2020/02/Wlab_landing_main-pic-new.jpg"
    )
    await update.message.reply_text(
        "היי! 👋\n"
        "<b>נעים להכיר, אני הבוט של WLAB.</b>\n\n"
        "🧬 <b>בדיקה אחת יכולה לשנות לכם את החיים –</b> אלפי לקוחות כבר שיפרו את התזונה וההרגשה שלהם בעזרתנו.\n\n"
        "🔹 <b>התהליך פשוט מאוד:</b>\n"
        "ממלאים כאן פרטים, ואנחנו שולחים לכם עלון מידע מסודר.\n"
        "צוות האבחון שלנו ייצור אתכם קשר בהקדם לכל שאלה והתאמה אישית.\n\n"
        "💡 <b>רוצים לקבל את כל הפרטים על הבדיקה?</b>\n"
        "ממלאים טופס קצר ומתחילים 😊\n\n"
        "<i>כל הפרטים נשמרים בפרטיות מלאה!</i>",
        parse_mode="HTML"
    )
    await update.message.reply_text(
        "1️⃣ <b>שם פרטי:</b>",
        parse_mode="HTML"
    )
    return FIRST_NAME

async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.message.text.strip()
    if not user_first_name or len(user_first_name) < 2:
        await update.message.reply_text("❗️נא להכניס שם פרטי תקין (לפחות 2 תווים):")
        return FIRST_NAME
    context.user_data["firstname"] = user_first_name
    await update.message.reply_text(
        "2️⃣ <b>שם משפחה:</b>",
        parse_mode="HTML"
    )
    return LAST_NAME

async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_last_name = update.message.text.strip()
    if not user_last_name or len(user_last_name) < 2:
        await update.message.reply_text("❗️נא להכניס שם משפחה תקין (לפחות 2 תווים):")
        return LAST_NAME
    context.user_data["lastname"] = user_last_name
    await update.message.reply_text(
        "📧 3️⃣ <b>אימייל ליצירת קשר:</b>",
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
        "📞 4️⃣ <b>מספר טלפון:</b>",
        parse_mode="HTML"
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text.strip()
    if not re.match(r"^[\d\-\+ ]{8,14}$", phone_number):
        await update.message.reply_text(
            "❗️נא להכניס מספר טלפון תקין (רק ספרות, מינימום 8 תווים):"
        )
        return PHONE
    context.user_data["mobile"] = phone_number
    keyboard = [
        [InlineKeyboardButton("✅ יש לי ביטוח פרטי", callback_data='yes_private_insurance')],
        [InlineKeyboardButton("❌ אין לי ביטוח פרטי", callback_data='no_private_insurance')]
    ]
    await update.message.reply_text(
        "5️⃣ <b>האם יש לך ביטוח פרטי?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PRIVATE_INSURANCE


async def private_insurance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query for the private insurance question,
    pushes the lead data to CRM, sends confirmation, and ends the conversation.
    Telegram-specific user profile data (username, first_name, last_name, chat_id)
    is now EXCLUDED as per user request.
    """
    print("DEBUG: Entered private_insurance function!") # Keep this for now for debugging
    query = update.callback_query
    await query.answer()

    if query.data == "yes_private_insurance":
        insurance_status = "יש לי ביטוח פרטי"
    else:
        insurance_status = "אין לי ביטוח פרטי"
    context.user_data["ביטוח פרטי"] = insurance_status

    scalla_public_id = os.getenv("SCALLA_PUBLIC_ID")
    crm_success_message = "" # Initialize for scope

    if not scalla_public_id:
        print("שגיאה: משתנה סביבה SCALLA_PUBLIC_ID לא הוגדר!")
        crm_success_message = "❌ שגיאה פנימית בבוט: מזהה CRM חסר. הליד לא נשלח ל-CRM."
    else:
        lead_data = {
            "firstname": context.user_data['firstname'],
            "lastname": context.user_data['lastname'],
            "email": context.user_data['email'],
            "mobile": context.user_data['mobile'],
            "ביטוח פרטי": context.user_data['ביטוח פרטי'],
            "leadsource": "טלגרם",
            "publicid": scalla_public_id,
            # Removed the 'description' field with Telegram user info
        }

        try:
            response = requests.post(CRM_API_URL, data=lead_data)
            response.raise_for_status()

            if response.status_code == 200 and "success" in response.text.lower():
                crm_success_message = "✅ הליד נשלח בהצלחה ל-CRM!"
            else:
                crm_success_message = (f"⚠️ אירעה שגיאה בשליחת הליד ל-CRM. "
                                       f"סטטוס: {response.status_code}. "
                                       f"תגובה: {response.text[:200]}...")
                print(f"CRM API Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            crm_success_message = f"❌ שגיאת תקשורת עם ה-CRM: {e}"
            print(f"Error pushing lead to CRM: {e}")

    # Send lead details to the Admin Channel - simplified, no Telegram user data
    lead_text = (
        "📥 <b>ליד חדש מבוט WLAB:</b>\n"
        f"👤 <b>שם פרטי:</b> {context.user_data['firstname']}\n"
        f"👤 <b>שם משפחה:</b> {context.user_data['lastname']}\n"
        f"📧 <b>אימייל:</b> {context.user_data['email']}\n"
        f"📞 <b>טלפון:</b> {context.user_data['mobile']}\n"
        f"🛡️ <b>ביטוח פרטי:</b> {context.user_data['ביטוח פרטי']}\n"
        f"🌐 <b>מקור ליד:</b> טלגרם\n\n"
        f"<i>סטטוס CRM: {crm_success_message}</i>"
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
    print("TOKEN (first 5 chars):", repr(token[:5]) + "...")
    if not token:
        print("שגיאה: לא הוגדר טוקן בוט. ודא שהגדרת TELEGRAM_BOT_TOKEN במשתני הסביבה!")
        exit(1)

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            PRIVATE_INSURANCE: [CallbackQueryHandler(private_insurance)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)

    print("הבוט עלה בהצלחה ומוכן לקבל לידים!")
    app.run_polling()

if __name__ == "__main__":
    main()
