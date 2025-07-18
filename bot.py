import os
import re
import requests # Make sure you have 'requests' installed (pip install requests)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes, CallbackQueryHandler
)

# --- Configuration Constants ---
# Define conversation states for the ConversationHandler
(FIRST_NAME, LAST_NAME, EMAIL, PHONE, PRIVATE_INSURANCE) = range(5)

# Admin channel to send lead notifications (e.g., your private channel)
ADMIN_CHANNEL = "@rakbriut"

# URLs for images and channel links
# This URL is defined but currently unused in the 'start' function.
# WELCOME_IMG_URL = "https://wlab.co.il/wp-content/uploads/2025/07/bot-cover.jpg"
BACK_TO_CHANNEL_LINK = "https://t.me/rakbriut"

# CRM API Endpoint (Scalla CRM webform capture)
CRM_API_URL = "https://api.scallacrm.co.il//modules/Webforms/capture.php"

# --- Conversation Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. Clears user data, sends welcome messages,
    and initiates the lead capture conversation by asking for the first name.
    """
    context.user_data.clear() # Clear any previous conversation data for this user

    # Send logo image
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="https://wlab.co.il/wp-content/uploads/2020/02/Wlab_landing_main-pic-new.jpg"
    )

    # Send introductory text message
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

    # Prompt for the first piece of information (First Name)
    await update.message.reply_text(
        "1️⃣ <b>שם פרטי:</b>", # Asking for first name
        parse_mode="HTML"
    )
    return FIRST_NAME # Transition to the FIRST_NAME state

async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives and validates the user's first name, then asks for the last name.
    """
    user_first_name = update.message.text.strip()
    if not user_first_name or len(user_first_name) < 2:
        await update.message.reply_text("❗️נא להכניס שם פרטי תקין (לפחות 2 תווים):")
        return FIRST_NAME # Stay in FIRST_NAME state for re-entry
    context.user_data["firstname"] = user_first_name # Store as 'firstname' for CRM
    await update.message.reply_text(
        "2️⃣ <b>שם משפחה:</b>", # Asking for last name
        parse_mode="HTML"
    )
    return LAST_NAME # Transition to the LAST_NAME state

async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives and validates the user's last name, then asks for the email.
    """
    user_last_name = update.message.text.strip()
    if not user_last_name or len(user_last_name) < 2:
        await update.message.reply_text("❗️נא להכניס שם משפחה תקין (לפחות 2 תווים):")
        return LAST_NAME # Stay in LAST_NAME state for re-entry
    context.user_data["lastname"] = user_last_name # Store as 'lastname' for CRM
    await update.message.reply_text(
        "📧 3️⃣ <b>אימייל ליצירת קשר:</b>", # Asking for email
        parse_mode="HTML"
    )
    return EMAIL # Transition to the EMAIL state

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives and validates the user's email, then asks for the phone number.
    """
    user_email = update.message.text.strip()
    # Basic email regex validation
    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_pattern, user_email) or len(user_email) > 100:
        await update.message.reply_text(
            "❗️כתובת אימייל לא תקינה. אנא נסה/י שוב:"
        )
        return EMAIL # Stay in EMAIL state for re-entry
    context.user_data["email"] = user_email # Store as 'email' for CRM
    await update.message.reply_text(
        "📞 4️⃣ <b>מספר טלפון:</b>", # Asking for phone
        parse_mode="HTML"
    )
    return PHONE # Transition to the PHONE state

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives and validates the user's phone number, then asks about private insurance.
    """
    phone_number = update.message.text.strip()
    # Flexible phone validation (8-14 digits, allows +, -, space)
    if not re.match(r"^[\d\-\+ ]{8,14}$", phone_number):
        await update.message.reply_text(
            "❗️נא להכניס מספר טלפון תקין (רק ספרות, מינימום 8 תווים):"
        )
        return PHONE # Stay in PHONE state for re-entry
    context.user_data["mobile"] = phone_number # Store as 'mobile' for CRM

    # Present inline keyboard for private insurance question
    keyboard = [
        [InlineKeyboardButton("✅ יש לי ביטוח פרטי", callback_data='yes_private_insurance')],
        [InlineKeyboardButton("❌ אין לי ביטוח פרטי", callback_data='no_private_insurance')]
    ]
    await update.message.reply_text(
        "5️⃣ <b>האם יש לך ביטוח פרטי?</b>", # Asking about private insurance
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PRIVATE_INSURANCE # Transition to the PRIVATE_INSURANCE state

async def private_insurance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the callback query for the private insurance question,
    pushes the lead data to CRM, sends confirmation, and ends the conversation.
    """
    query = update.callback_query
    await query.answer() # Acknowledge the callback query

    # Map the callback_data to the CRM's expected value for 'ביטוח פרטי'
    # IMPORTANT: These string values MUST exactly match the options in your CRM's dropdown.
    if query.data == "yes_private_insurance":
        insurance_status = "יש לי ביטוח פרטי"
    else: # query.data == "no_private_insurance"
        insurance_status = "אין לי ביטוח פרטי"
    context.user_data["ביטוח פרטי"] = insurance_status # Store using CRM field name

    # Retrieve CRM Public ID from environment variables
    scalla_public_id = os.getenv("SCALLA_PUBLIC_ID")
    if not scalla_public_id:
        print("שגיאה: משתנה סביבה SCALLA_PUBLIC_ID לא הוגדר!")
        # Fallback for user or admin if public ID is missing (highly unlikely on Railway if set)
        crm_success_message = "❌ שגיאה פנימית בבוט: מזהה CRM חסר."
    else:
        # Prepare lead data for CRM (keys must match CRM form field names)
        user_info = query.from_user
        telegram_username = user_info.username if user_info.username else '---'
        telegram_first_name = user_info.first_name if user_info.first_name else '---'
        telegram_last_name = user_info.last_name if user_info.last_name else '---'
        telegram_chat_id = query.effective_chat.id

        lead_data = {
            "firstname": context.user_data['firstname'],
            "lastname": context.user_data['lastname'],
            "email": context.user_data['email'],
            "mobile": context.user_data['mobile'],
            "ביטוח פרטי": context.user_data['ביטוח פרטי'], # CRM field name as per screenshot
            "leadsource": "טלגרם", # Fixed value for the CRM's 'leadsource' field from screenshot
            "publicid": scalla_public_id, # The Public ID required by Scalla CRM
            # Add extra Telegram user details to the 'description' field in CRM
            "description": (f"Lead from Telegram Bot.\n"
                            f"Telegram Username: @{telegram_username}\n"
                            f"Telegram First Name: {telegram_first_name}\n"
                            f"Telegram Last Name: {telegram_last_name}\n"
                            f"Telegram Chat ID: {telegram_chat_id}")
        }

        # --- Push data to CRM ---
        crm_success_message = ""
        try:
            # Use 'data' parameter for form-urlencoded submission
            response = requests.post(CRM_API_URL, data=lead_data)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # Check CRM API response (you might need to adjust based on Scalla's actual success response)
            if response.status_code == 200 and "success" in response.text.lower():
                crm_success_message = "✅ הליד נשלח בהצלחה ל-CRM!"
            else:
                crm_success_message = (f"⚠️ אירעה שגיאה בשליחת הליד ל-CRM. "
                                       f"סטטוס: {response.status_code}. "
                                       f"תגובה: {response.text[:200]}...") # Log first 200 chars of response
                print(f"CRM API Error: {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            crm_success_message = f"❌ שגיאת תקשורת עם ה-CRM: {e}"
            print(f"Error pushing lead to CRM: {e}")

    # Send lead details to the Admin Channel
    lead_text = (
        "📥 <b>ליד חדש מבוט WLAB:</b>\n"
        f"👤 <b>שם פרטי:</b> {context.user_data['firstname']}\n"
        f"👤 <b>שם משפחה:</b> {context.user_data['lastname']}\n"
        f"📧 <b>אימייל:</b> {context.user_data['email']}\n"
        f"📞 <b>טלפון:</b> {context.user_data['mobile']}\n"
        f"🛡️ <b>ביטוח פרטי:</b> {context.user_data['ביטוח פרטי']}\n"
        f"🌐 <b>מקור ליד:</b> טלגרם\n" # Explicitly state lead source
        f"👤 <b>טלגרם (שם משתמש):</b> @{telegram_username}\n"
        f"👤 <b>טלגרם (שם פרטי):</b> {telegram_first_name}\n"
        f"👤 <b>טלגרם (שם משפחה):</b> {telegram_last_name}\n"
        f"🆔 <b>צ'אט ID:</b> <code>{telegram_chat_id}</code>\n\n"
        f"<i>סטטוס CRM: {crm_success_message}</i>" # Inform about CRM status
    )
    await context.bot.send_message(chat_id=ADMIN_CHANNEL, text=lead_text, parse_mode="HTML")

    # Send confirmation message to the user
    await query.edit_message_text(
        "✅ <b>תודה! הפרטים התקבלו בהצלחה.</b>\n"
        "צוות השיווק שלנו יחזור אליך בקרוב.\n\n"
        "🔗 לחזרה אל ערוץ הפרסום:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 מעבר לערוץ", url=BACK_TO_CHANNEL_LINK)]
        ])
    )
    context.user_data.clear() # Clear user data after successful lead capture
    return ConversationHandler.END # End the conversation

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /cancel command. Clears user data and ends the conversation.
    """
    await update.message.reply_text("❌ הפעולה בוטלה. יום נעים!")
    context.user_data.clear()
    return ConversationHandler.END

# --- Main Bot Application Setup ---

def main():
    """
    Sets up and runs the Telegram bot application.
    Retrieves the bot token from environment variables.
    """
    # Get Telegram Bot Token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    print("TOKEN (first 5 chars):", repr(token[:5]) + "...") # Print partial token for security
    if not token:
        print("שגיאה: לא הוגדר טוקן בוט. ודא שהגדרת TELEGRAM_BOT_TOKEN במשתני הסביבה!")
        exit(1) # Exit if the token is not found

    # Build the Telegram Application
    app = ApplicationBuilder().token(token).build()

    # Define the conversation handler
    # entry_points: Where the conversation starts (e.g., /start command)
    # states: Dictionary mapping states to handlers for specific message types
    # fallbacks: Handlers if the user inputs something unexpected or uses /cancel
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

    # Add the conversation handler to the application
    app.add_handler(conv_handler)

    print("הבוט עלה בהצלחה ומוכן לקבל לידים!")
    # Start polling for updates from Telegram
    app.run_polling()

if __name__ == "__main__":
    main()
