from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import requests
import re
import os
from Keep_alive import keep_alive
from database import Database

# Bot token - Use environment variable for security
BOT_TOKEN = os.getenv('BOT_TOKEN', '7747088445:AAF36oSyqpEfzVzTKwfmRRSxfE2c0XRCCYo')

# Initialize database
db = Database()

# Admin user IDs
ADMIN_USERS = [6638596782, 7265096020]

# Mandatory channel to join
MANDATORY_CHANNEL = '@xAnonymous_Hacking'  # Your channel username

# Service costs
SERVICE_COSTS = {
    'number_info': 1.0,
    'aadhar_info': 2.0,
    'car_info': 1.5,
    'upi_info': 1.0,
    'email_check': 0.5
}

# Check if user is member of mandatory channel
async def check_channel_membership(context, user_id):
    try:
        # Try to get chat member info
        member = await context.bot.get_chat_member(chat_id=MANDATORY_CHANNEL, user_id=user_id)
        # Check if user is a member, admin, or creator
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        # If we can't check membership due to permissions, try alternative method
        try:
            # Try to get user info from the channel
            chat = await context.bot.get_chat(MANDATORY_CHANNEL)
            if chat:
                # If we reach here, at least the channel exists
                # For now, we'll assume user is not a member if we can't verify
                return False
        except Exception as e2:
            print(f"Channel access error: {e2}")
            # If channel is not accessible, skip the check (emergency fallback)
            return True
    return False

# Escape Markdown
def escape_markdown(text):
    if not text:
        return 'N/A'
    text = str(text)
    # Simple escaping for Telegram Markdown
    return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')

# Format results
def format_results(response_json, number):
    results = response_json.get("data", {}).get("results", [])
    if not results:
        return "❌ No results found."

    message = f"✅ {len(results)} Results Found:\n"
    for idx, result in enumerate(results, 1):
        mobile = result.get("📱 Mobile", "N/A")
        name = result.get("👤 Name", "N/A")
        father = result.get("👨‍👦 Father Name", "N/A")
        address = result.get("🏠 Address", "N/A").replace("!.!", "").replace("!NA!", "").strip()
        email = result.get("📧 Email", "N/A").replace("❌", "N/A")
        circle = result.get("📍 Circle", "N/A")
        aadhar = result.get("🆔 Aadhar Card", "N/A")
        alt = result.get("📞 Alt Number", "N/A") or "N/A"

        message += f"\n🔹 Result {idx}:\n"
        message += f"📱 Mobile: {mobile}\n"
        message += f"👤 Name: {name.strip() if name != 'N/A' else 'N/A'}\n"
        message += f"👴 Father's Name: {father.strip() if father != 'N/A' else 'N/A'}\n"
        message += f"🏠 Address: {address}\n"
        message += f"📧 Email: {email.strip() if email != 'N/A' else 'N/A'}\n"
        message += f"🔴 Circle: {circle.strip() if circle != 'N/A' else 'N/A'}\n"
        message += f"🆔 Aadhar: {aadhar.strip() if aadhar != 'N/A' else 'N/A'}\n"
        message += f"📲 Alternate Mobile: {alt.strip() if alt != 'N/A' else 'N/A'}\n"
        message += "-........................-\n"
    return message.strip()

# Check if user exists and register if new
def register_user(user):
    user_data = db.get_user(user.id)
    if not user_data:
        db.add_user(user.id, user.username, user.first_name)
        return True  # New user
    return False  # Existing user

# Main menu keyboard
def get_main_menu(user_id=None):
    keyboard = [
        [InlineKeyboardButton("📱 NUMBER INFO 🔍", callback_data="number_info")],
        [InlineKeyboardButton("💳 Credit Balance", callback_data="balance"),
         InlineKeyboardButton("👥 Refer & Earn 🎁", callback_data="referral")],
        [InlineKeyboardButton("💰 BUY CREDITS 💵", callback_data="buy_credits"),
         InlineKeyboardButton("🎫 REDEEM COUPON 🎁", callback_data="redeem_coupon")],
        [InlineKeyboardButton("📋 HOW TO USE ❓", callback_data="help")],
        [InlineKeyboardButton("📧 CHECK LEAKED EMAIL 🔍", callback_data="email_check")]
    ]
    
    # Add admin-only button for coupon generation
    if user_id and user_id in ADMIN_USERS:
        keyboard.append([InlineKeyboardButton("🎫 GENERATE COUPON 👑", callback_data="admin_generate_coupon")])
    
    return InlineKeyboardMarkup(keyboard)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Check if user is member of mandatory channel
    is_member = await check_channel_membership(context, user.id)
    
    if not is_member:
        join_msg = f"🔒 Access Restricted!\n\n"
        join_msg += f"To use KAAL CRACKER OSINT bot, you must first join our channel:\n\n"
        join_msg += f"📢 Channel: {MANDATORY_CHANNEL}\n"
        join_msg += f"🔗 Link: https://t.me/xAnonymous_Hacking\n\n"
        join_msg += f"✅ After joining, click /start again to get your 5 FREE credits!\n\n"
        join_msg += f"⚠️ This check cannot be bypassed!"
        
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/xAnonymous_Hacking"),
                    InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]]
        
        await update.message.reply_text(
            join_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Handle referral code
    referred_by = None
    if context.args:
        ref_code = context.args[0]
        referred_by = db.get_user_by_referral_code(ref_code)

    # Register user
    is_new = register_user(user)
    user_data = db.get_user(user.id)

    welcome_msg = f"KAAL CRACKER OSINT\n\n"
    welcome_msg += f"👤 User: 🇮🇳 x {user.first_name or user.username or 'User'}\n"
    welcome_msg += f"🔖 Username: @{user.username or 'N/A'}\n"
    welcome_msg += f"🆔 ID: {user.id}\n"
    welcome_msg += f"💰 Credits: {user_data[3]:.2f}\n"
    welcome_msg += f"👥 Referrals: {user_data[4]}\n\n"
    welcome_msg += f"Status: ACTIVE ✅\n\n"

    if is_new:
        welcome_msg += "🎉 Welcome! You've received 5.0 bonus credits!\n"
        if referred_by:
            welcome_msg += "🎁 Referral bonus applied!\n"

    welcome_msg += "🤖 Bot Owner: @KAALCRACKERYT\n\n"
    welcome_msg += "Select a service below:"

    await update.message.reply_text(
        welcome_msg,
        reply_markup=get_main_menu(user.id)
    )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Special handling for membership check
    if query.data == "check_membership":
        is_member = await check_channel_membership(context, user_id)
        
        if not is_member:
            not_joined_msg = f"❌ You haven't joined the channel yet!\n\n"
            not_joined_msg += f"📢 Please join: {MANDATORY_CHANNEL}\n"
            not_joined_msg += f"🔗 Link: https://t.me/xAnonymous_Hacking\n\n"
            not_joined_msg += f"✅ After joining, click 'Check Again' button."
            
            try:
                await query.edit_message_text(
                    not_joined_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/xAnonymous_Hacking"),
                         InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]
                    ])
                )
            except Exception as e:
                # If edit fails, try to send a new message
                await query.message.reply_text(not_joined_msg, reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url="https://t.me/xAnonymous_Hacking"),
                     InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]
                ]))
            return
        else:
            # User has joined, proceed with registration
            user = query.from_user
            is_new = register_user(user)
            user_data = db.get_user(user.id)
            
            welcome_msg = f"✅ Welcome to KAAL CRACKER OSINT!\n\n"
            welcome_msg += f"👤 User: 🇮🇳 x {user.first_name or user.username or 'User'}\n"
            welcome_msg += f"🔖 Username: @{user.username or 'N/A'}\n"
            welcome_msg += f"🆔 ID: {user.id}\n"
            welcome_msg += f"💰 Credits: {user_data[3]:.2f}\n"
            welcome_msg += f"👥 Referrals: {user_data[4]}\n\n"
            welcome_msg += f"Status: ACTIVE ✅\n\n"
            
            if is_new:
                welcome_msg += "🎉 You've received 5.0 bonus credits for joining!\n"
            
            welcome_msg += "🤖 Bot Owner: @KAALCRACKERYT\n\n"
            welcome_msg += "Select a service below:"
            
            try:
                await query.edit_message_text(
                    welcome_msg,
                    reply_markup=get_main_menu(user.id)
                )
            except Exception as e:
                await query.message.reply_text(welcome_msg, reply_markup=get_main_menu(user.id))
            return

    # Check channel membership for all other actions
    is_member = await check_channel_membership(context, user_id)
    if not is_member:
        access_denied_msg = f"🔒 Access Denied!\n\n"
        access_denied_msg += f"You must join our channel to use this bot:\n"
        access_denied_msg += f"📢 {MANDATORY_CHANNEL}\n"
        access_denied_msg += f"🔗 https://t.me/xAnonymous_Hacking\n\n"
        access_denied_msg += f"⚠️ This check cannot be bypassed!"
        
        try:
            await query.edit_message_text(
                access_denied_msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url="https://t.me/xAnonymous_Hacking"),
                     InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]
                ])
            )
        except Exception as e:
            await query.message.reply_text(access_denied_msg, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url="https://t.me/xAnonymous_Hacking"),
                 InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]
            ]))
        return

    user_data = db.get_user(user_id)
    if not user_data:
        await query.edit_message_text("❌ Please use /start first!")
        return

    if query.data == "balance":
        stats = db.get_user_stats(user_id)
        balance_msg = f"💳 Your Account Details\n\n"
        balance_msg += f"💰 Credits: {user_data[3]:.2f}\n"
        balance_msg += f"👥 Referrals: {user_data[4]}\n"
        balance_msg += f"📊 Total Services Used: {stats['total_usage']}\n"
        balance_msg += f"📅 Member Since: {user_data[6][:10]}\n\n"

        if stats['transactions']:
            balance_msg += "📋 Recent Transactions:\n"
            for trans in stats['transactions'][:3]:
                balance_msg += f"• {trans[0]}: {trans[1]:+.1f} - {trans[2]}\n"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            balance_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "referral":
        ref_code = db.get_referral_code(user_id)
        ref_msg = f"👥 Referral System 🎁\n\n"
        ref_msg += f"🔗 Your Referral Code: {ref_code}\n"
        ref_msg += f"👥 Total Referrals: {user_data[4]}\n\n"
        ref_msg += f"💰 Earn 1 Credit for each referral!\n"
        ref_msg += f"🎁 New users get 5 credits bonus!\n\n"
        ref_msg += f"📤 Share this link:\n"
        ref_msg += f"https://t.me/{context.bot.username}?start={ref_code}"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            ref_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "buy_credits":
        buy_msg = f"💰 Buy Credits 💳\n\n"
        buy_msg += f"💵 Pricing:\n"
        buy_msg += f"• 10 Credits = ₹50\n"
        buy_msg += f"• 25 Credits = ₹100\n"
        buy_msg += f"• 50 Credits = ₹180\n"
        buy_msg += f"• 100 Credits = ₹300\n\n"
        buy_msg += f"📞 Contact @KAALCRACKERYT to purchase credits\n"
        buy_msg += f"💸 Payment: UPI/Bank Transfer"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            buy_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "help":
        help_msg = f"📋 How to Use ❓\n\n"
        help_msg += f"🔍 Number Info: 1 Credit per search\n"
        help_msg += f"📧 Email Check: 0.5 Credits per check\n\n"
        help_msg += f"💡 Tips:\n"
        help_msg += f"• Refer friends to earn credits\n"
        help_msg += f"• Buy credits for unlimited access\n"
        help_msg += f"• Contact support for help"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            help_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "redeem_coupon":
        redeem_msg = f"🎫 Redeem Coupon 🎁\n\n"
        redeem_msg += f"💰 Current Credits: {user_data[3]:.2f}\n\n"
        redeem_msg += f"To redeem a coupon, use:\n"
        redeem_msg += f"/redeem <coupon_code>\n\n"
        redeem_msg += f"Example: /redeem WELCOME100\n\n"
        redeem_msg += f"📞 Contact @KAALCRACKERYT to get coupon codes"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            redeem_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_generate_coupon":
        if user_id not in ADMIN_USERS:
            await query.edit_message_text("❌ Access denied!")
            return
            
        admin_msg = f"🎫 Generate Coupon 👑\n\n"
        admin_msg += f"📋 Instructions:\n"
        admin_msg += f"Use: /createcoupon <code> <credits> [max_uses] [expires_days]\n\n"
        admin_msg += f"💡 Examples:\n"
        admin_msg += f"• /createcoupon WELCOME100 10 50 30\n"
        admin_msg += f"  Creates 'WELCOME100' with 10 credits, 50 uses, expires in 30 days\n\n"
        admin_msg += f"• /createcoupon BONUS50 5 100 15\n"
        admin_msg += f"  Creates 'BONUS50' with 5 credits, 100 uses, expires in 15 days\n\n"
        admin_msg += f"📊 Check coupon stats with:\n"
        admin_msg += f"/couponstats <coupon_code>\n\n"
        admin_msg += f"⚠️ This feature is only available to admins"

        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            admin_msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "main_menu":
        welcome_msg = f"KAAL CRACKER OSINT\n\n"
        welcome_msg += f"💰 Credits: {user_data[3]:.2f}\n"
        welcome_msg += f"👥 Referrals: {user_data[4]}\n\n"
        welcome_msg += f"Select a service below:"

        await query.edit_message_text(
            welcome_msg,
            reply_markup=get_main_menu(user_id)
        )

    else:
        await query.edit_message_text(
            f"Please send the required information for {query.data.replace('_', ' ').title()}.\n\n"
            f"Use: /search <your_query>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]])
        )

# Search command
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check channel membership
    is_member = await check_channel_membership(context, user_id)
    if not is_member:
        join_msg = f"🔒 Access Denied!\n\n"
        join_msg += f"You must join our channel to use this bot:\n"
        join_msg += f"📢 {MANDATORY_CHANNEL}\n"
        join_msg += f"🔗 https://t.me/xAnonymous_Hacking\n\n"
        join_msg += f"⚠️ This check cannot be bypassed!"
        
        await update.message.reply_text(join_msg)
        return

    # Check if user exists
    user_data = db.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Please use /start first!")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a search query.\n"
            "Usage: /search 7505974322"
        )
        return

    # Check credits
    cost = SERVICE_COSTS['number_info']
    if user_data[3] < cost:
        await update.message.reply_text(
            f"❌ Insufficient credits!\n"
            f"Required: {cost} credits\n"
            f"Your balance: {user_data[3]:.2f} credits\n\n"
            f"💰 Buy more credits or refer friends!"
        )
        return

    query_text = context.args[0]
    api_url = f"https://glonova.in/o0s.php/?ng={query_text}"

    try:
        response = requests.get(api_url, timeout=10)
        if response.ok:
            json_data = response.json()
            results = json_data.get("data", {}).get("results", [])
            
            # Check if actual data was found
            if results:
                # Data found - deduct credits
                if not db.deduct_credits(user_id, cost):
                    await update.message.reply_text("❌ Failed to process payment!")
                    return
                
                # Log service usage
                db.log_service_usage(user_id, 'number_info', query_text)
                
                formatted = format_results(json_data, query_text)
                # Add credit info to response
                updated_balance = db.get_user(user_id)[3]
                formatted += f"\n\n💳 Credits Used: {cost}\n💰 Remaining: {updated_balance:.2f}"
            else:
                # No data found - don't deduct credits
                formatted = "❌ No results found. No credits deducted."

        else:
            formatted = f"❌ Failed with status {response.status_code}. No credits deducted."

    except Exception as e:
        formatted = f"❌ Error occurred: {escape_markdown(str(e))}. No credits deducted."

    await update.message.reply_text(formatted)

# Redeem coupon command
async def redeem_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check channel membership
    is_member = await check_channel_membership(context, user_id)
    if not is_member:
        join_msg = f"🔒 Access Denied!\n\n"
        join_msg += f"You must join our channel to use this bot:\n"
        join_msg += f"📢 {MANDATORY_CHANNEL}\n"
        join_msg += f"🔗 https://t.me/xAnonymous_Hacking\n\n"
        join_msg += f"⚠️ This check cannot be bypassed!"
        
        await update.message.reply_text(join_msg)
        return

    # Check if user exists
    user_data = db.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Please use /start first!")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a coupon code.\n"
            "Usage: /redeem <coupon_code>\n"
            "Example: /redeem WELCOME100"
        )
        return

    coupon_code = context.args[0].upper()
    result = db.redeem_coupon(user_id, coupon_code)

    if result["success"]:
        # Get updated user data
        updated_user = db.get_user(user_id)
        success_msg = f"✅ {result['message']}\n\n"
        success_msg += f"💰 Your Credits: {updated_user[3]:.2f}"
        await update.message.reply_text(success_msg)
    else:
        await update.message.reply_text(f"❌ {result['message']}")

# Admin commands
async def add_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_USERS:
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
        return

    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])

        db.update_credits(user_id, amount, 'ADMIN_ADD', f'Admin credit addition by {update.effective_user.id}')
        await update.message.reply_text(f"✅ Added {amount} credits to user {user_id}")

    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or amount")

async def create_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_USERS:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /createcoupon <code> <credits> [max_uses] [expires_days]\n"
            "Example: /createcoupon WELCOME100 10 50 30"
        )
        return

    try:
        code = context.args[0].upper()
        credits = float(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 1
        expires_days = int(context.args[3]) if len(context.args) > 3 else 30

        if db.create_coupon(code, credits, max_uses, update.effective_user.id, expires_days):
            coupon_msg = f"✅ Coupon Created Successfully!\n\n"
            coupon_msg += f"🎫 Code: {code}\n"
            coupon_msg += f"💰 Credits: {credits}\n"
            coupon_msg += f"📊 Max Uses: {max_uses}\n"
            coupon_msg += f"⏰ Expires in: {expires_days} days"
            await update.message.reply_text(coupon_msg)
        else:
            await update.message.reply_text("❌ Coupon code already exists!")

    except ValueError:
        await update.message.reply_text("❌ Invalid parameters")

async def coupon_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_USERS:
        return

    if not context.args:
        await update.message.reply_text("Usage: /couponstats <coupon_code>")
        return

    coupon_code = context.args[0].upper()
    stats = db.get_coupon_stats(coupon_code)

    if not stats:
        await update.message.reply_text("❌ Coupon not found!")
        return

    code, credits, max_uses, current_uses, created_at, expires_at, status = stats
    
    stats_msg = f"📊 Coupon Statistics\n\n"
    stats_msg += f"🎫 Code: {code}\n"
    stats_msg += f"💰 Credits: {credits}\n"
    stats_msg += f"📊 Uses: {current_uses}/{max_uses}\n"
    stats_msg += f"📅 Created: {created_at[:10]}\n"
    stats_msg += f"⏰ Expires: {expires_at[:10]}\n"
    stats_msg += f"🔄 Status: {status}"

    await update.message.reply_text(stats_msg)

# Main
if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("redeem", redeem_coupon))
    app.add_handler(CommandHandler("addcredits", add_credits))
    app.add_handler(CommandHandler("createcoupon", create_coupon))
    app.add_handler(CommandHandler("couponstats", coupon_stats))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Add 15 credits to user 5112205166
    db.update_credits(5112205166, 15.0, 'ADMIN_ADD', 'Admin credit addition - bulk add')
    print("✅ Added 15 credits to user 5112205166")

    print("🤖 Nuclear Cyber OSINT Bot is running...")
    print("💳 Credit system activated")
    print("👥 Referral system enabled")

    app.run_polling()