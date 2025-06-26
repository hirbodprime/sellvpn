import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sellvpn.settings')

import django
django.setup()  # ✅ You must do this before importing models

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler, filters
)

from telegram.constants import ChatMemberStatus
from asgiref.sync import sync_to_async

from vpnuser.models import VPNUser, SubscriptionPlan, VPNConfig, PaymentSettings,VPNDelivery



# --- UI Keyboards ---

def build_join_menu():
    return InlineKeyboardMarkup([
        # [InlineKeyboardButton("🔥 کانال اصلی ما", url="https://t.me/terrorday")],
        [InlineKeyboardButton("📛 کانال اختصاصی ها", url="https://t.me/V2rayngHiddify1")],
        [InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_membership")]
    ])

def build_main_vpn_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 خرید کانفینگ", callback_data="buy_config")],
        [InlineKeyboardButton("🧾 کانفینگ های من", callback_data="my_configs")],
                [InlineKeyboardButton("♻️ تمدید کانفینگ", callback_data="renew_config")]

    ])

def build_config_type_menu():
    return InlineKeyboardMarkup([
[InlineKeyboardButton("📦 لیست حجمی", callback_data="configs:volume")],
[InlineKeyboardButton("🚀 لیست نامحدود", callback_data="configs:unlimited")],
    [InlineKeyboardButton("⬅️ بازگشت", callback_data="back")]

    ],)

# --- Handlers ---
async def renew_config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user

    try:
        vpn_user = await sync_to_async(VPNUser.objects.get)(telegram_id=user.id)
    except VPNUser.DoesNotExist:
        await query.answer("❌ شما هنوز خریدی انجام نداده‌اید.", show_alert=True)
        return

    deliveries = await sync_to_async(list)(
        VPNDelivery.objects.filter(user=vpn_user).select_related('config', 'config__subscription_plan')
    )

    if not deliveries:
        await query.edit_message_text("❌ شما هنوز هیچ کانفیگی برای تمدید ندارید.", reply_markup=build_main_vpn_menu())
        return

    buttons = [
        [InlineKeyboardButton(
            f"{d.config.title} - {d.config.subscription_plan.label}",
            callback_data=f"renew:{d.config.id}"
        )]
        for d in deliveries
    ]
    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back")])

    await query.edit_message_text("♻️ یکی از کانفیگ‌ها را برای تمدید انتخاب کن:", reply_markup=InlineKeyboardMarkup(buttons))

from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest
async def back_to_last_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    last_menu = context.user_data.get("last_menu")

    try:
        if last_menu == "main_menu":
            await query.edit_message_text(
                "⬅️ بازگشت به منوی اصلی",
                reply_markup=build_main_vpn_menu()
            )
        elif last_menu == "config_type":
            await query.edit_message_text(
                "✅ نوع کانفینگ را انتخاب کن:",
                reply_markup=build_config_type_menu()
            )
            context.user_data["last_menu"] = "main_menu"

        elif last_menu == "duration":
            plans = await sync_to_async(list)(SubscriptionPlan.objects.all())
            buttons = [
                [InlineKeyboardButton(plan.label, callback_data=f"duration:{plan.id}")]
                for plan in plans
            ]
            buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back")])
            await query.edit_message_text(
                "📅 یکی از مدت‌ها را انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            context.user_data["last_menu"] = "config_type"

        elif last_menu == "config_list":
            selected_type = context.user_data.get("selected_type")
            plan_id = context.user_data.get("selected_plan_id")

            if not selected_type or not plan_id:
                await query.edit_message_text("❌ اطلاعات قبلی یافت نشد.")
                return

            configs = await sync_to_async(list)(
                VPNConfig.objects.filter(
                    type=selected_type,
                    subscription_plan_id=plan_id,
                    active=True
                )
            )

            buttons = [
                [InlineKeyboardButton(
                    f"{cfg.title} - {cfg.bandwidth_gb} گیگ - {cfg.price_toman:,} تومان",
                    callback_data=f"buyconfig:{cfg.id}"
                )]
                for cfg in configs
            ]
            context.user_data["last_menu"] = "duration"

            buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back")])

            await query.edit_message_text(
                "🕋 یکی از پلن‌ها رو انتخاب کن و برو برای پرداختش ✋",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        else:
            await query.edit_message_text("❌ منوی قبلی پیدا نشد.")
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("asfdasdf")
    user = update.effective_user
    chat_id = update.effective_chat.id

    await sync_to_async(VPNUser.objects.update_or_create)(
        telegram_id=user.id,
        defaults={"username": user.username, "first_name": user.first_name}
    )

    # Check only if private chat
    if update.message.chat.type != "private":
        return

    try:
        member = await context.bot.get_chat_member(chat_id="@V2rayngHiddify1", user_id=user.id)
        if member.status not in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]:
            raise Exception("not member")

        # ✅ Already joined
        await update.message.reply_text(
            "خوش آمدی 🎉\nیکی از گزینه‌های زیر را انتخاب کن:",
            reply_markup=build_main_vpn_menu()
        )

    except:
        # ❌ Not joined
        await update.message.reply_text(
            "🤖 رئیس، قبل از استفاده از امکانات من لطفا عضو کانال‌هامون شو",
            reply_markup=build_join_menu()
        )

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    user_id = user.id
    channel_ids = ["@V2rayngHiddify1"]  # Update these

    try:
        for channel in channel_ids:
            print(f"🔍 Checking membership for user {user_id} in channel {channel}")
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            print(f"✅ Status in {channel}: {member.status}")

            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await query.answer("❌ هنوز در همه‌ی کانال‌ها عضو نشدی.", show_alert=True)
                return

        print("✅ User is a member of all required channels")
        await query.edit_message_text("✅ عضویت تایید شد!", reply_markup=build_main_vpn_menu())

    except Exception as e:
        print(f"❌ Exception during membership check: {e}")
        await query.answer("❌ بررسی عضویت ناموفق بود.", show_alert=True)



async def buy_config_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ handle_config_selection TRIGGERED")
    context.user_data["last_menu"] = "main_menu"

    query = update.callback_query
    await query.edit_message_text("✅ نوع کانفینگ را انتخاب کن:", reply_markup=build_config_type_menu())
async def handle_config_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_type = query.data.split(":")[1]
    context.user_data["selected_type"] = selected_type
    context.user_data["last_menu"] = "config_type"

    plans = await sync_to_async(list)(SubscriptionPlan.objects.all())

    if not plans:
        await query.edit_message_text("❌ هیچ پلنی برای این نوع وجود ندارد.")
        return

    buttons = [
        [InlineKeyboardButton(plan.label, callback_data=f"duration:{plan.id}")]
        for plan in plans
    ]
    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back")])

    await query.edit_message_text(
        "📅 مرحله دوم:\nیکی از مدت‌ها را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_config_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    query = update.callback_query
    await query.answer()
    payment_settings = await sync_to_async(PaymentSettings.objects.get)(active=True)

    CARD_NUMBER = payment_settings.card_number
    CARD_NAME = payment_settings.card_holder_name
    ADMIN_USER_ID = payment_settings.admin_user_id
    config_id = int(query.data.split(":")[1])
    config = await sync_to_async(VPNConfig.objects.get)(id=config_id)

    context.user_data["selected_config_id"] = config_id

    message = (
        f"💳 لطفاً مبلغ *{config.price_toman:,} تومان* را به کارت زیر واریز کنید:\n\n"
        f"💳 شماره کارت: `{CARD_NUMBER}`\n"
        f"👤 به نام: *{CARD_NAME}*\n\n"
        f"سپس عکس فیش واریزی را برای من بفرستید تا تأیید کنم ✅"
    )

    buttons = [
        [InlineKeyboardButton("❌ لغو", callback_data="cancel_payment")]
    ]

    await query.edit_message_text(
        text=message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("❌ عملیات لغو شد.")
    await update.callback_query.edit_message_text("لغو شد. هر وقت خواستی دوباره امتحان کن.")

async def handle_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_settings = await sync_to_async(PaymentSettings.objects.get)(active=True)
    ADMIN_USER_ID = payment_settings.admin_user_id
    user = update.effective_user
    photo = update.message.photo[-1]  # highest quality

    config_id = context.user_data.get("selected_config_id") or context.user_data.get("renew_config_id")
    if not config_id:
        await update.message.reply_text("❗️مشخص نیست این عکس برای کدوم خرید هست.")
        return

    config = await sync_to_async(VPNConfig.objects.get)(id=config_id)
    subscription_plan = await sync_to_async(lambda: config.subscription_plan)()
    label = await sync_to_async(lambda: subscription_plan.label)()

    caption = (
        f"🧾 فیش واریزی جدید\n\n"
        f"👤 {user.first_name or ''} (@{user.username or '—'})\n"
        f"🆔 {user.id}\n"
        f"📦 کانفیگ: {config.title} ({label} - {config.bandwidth_gb} گیگ - {config.price_toman:,} تومان)"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=photo.file_id,
        caption=caption
    )

    await update.message.reply_text("✅ فیش ارسال شد. منتظر تأیید ادمین بمانید.")


async def handle_duration_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_id = int(query.data.split(":")[1])
    context.user_data["selected_plan_id"] = plan_id
    context.user_data["last_menu"] = "duration"

    selected_type = context.user_data.get("selected_type")
    if not selected_type:
        await query.edit_message_text("❌ نوع کانفینگ مشخص نیست.")
        return

    configs = await sync_to_async(list)(
        VPNConfig.objects.filter(
            type=selected_type,
            subscription_plan_id=plan_id,
            active=True
        )
    )

    if not configs:
        await query.edit_message_text("❌ برای این مدت هیچ کانفیگی وجود ندارد.")
        return
    context.user_data["last_menu"] = "duration"


    buttons = [
        [InlineKeyboardButton(
            f"{cfg.title} - {cfg.bandwidth_gb} گیگ - {cfg.price_toman:,} تومان",
            callback_data=f"buyconfig:{cfg.id}"
        )]
        for cfg in configs
    ]

    buttons.append([InlineKeyboardButton("⬅️ بازگشت", callback_data="back")])

    await query.edit_message_text(
        "🕋 مرحله سه:\nیکی از پلن‌ها رو انتخاب کن و برو برای پرداختش ✋",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
async def send_vpn_config_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    try:
        payment_settings = await sync_to_async(PaymentSettings.objects.get)(active=True)
        if admin_id != payment_settings.admin_user_id:
            await update.message.reply_text("❌ فقط ادمین می‌تونه این دستور رو اجرا کنه.")
            return
    except PaymentSettings.DoesNotExist:
        await update.message.reply_text("❌ تنظیمات پرداخت یافت نشد.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("❗️استفاده صحیح:\n/sendvpn @username config_id")
        return

    username = context.args[0].lstrip("@")
    config_id = context.args[1]

    # ✅ Robust user lookup (username or ID)
    try:
        print(f"🔍 Trying to find user by username: {username}")
        user = await sync_to_async(VPNUser.objects.get)(username=username)
        print(f"✅ Found user by username: {user.username} ({user.telegram_id})")
    except VPNUser.DoesNotExist:
        print(f"⚠️ No user with username '{username}' found.")
        if username.isdigit():
            try:
                print(f"🔍 Trying to find user by telegram_id: {username}")
                user = await sync_to_async(VPNUser.objects.get)(telegram_id=int(username))
                print(f"✅ Found user by telegram_id: {user.telegram_id}")
            except VPNUser.DoesNotExist:
                print(f"❌ No user with telegram_id {username} found.")
                await update.message.reply_text("❌ کاربر یافت نشد.")
                return
        else:
            print(f"❌ Invalid username and not a numeric ID.")
            await update.message.reply_text("❌ کاربر یافت نشد.")
            return


    try:
        config = await sync_to_async(VPNConfig.objects.get)(id=config_id)
        await sync_to_async(VPNDelivery.objects.create)(
            user=user,
            config=config,
            manually_sent=True
        )
        message = (
            f"🌐 کانفیگ شما آماده است!\n\n"
            f"📦 {config.title}\n"
            f"📶 {config.bandwidth_gb} گیگ\n"
            f"💰 {config.price_toman:,} تومان\n\n"
            f"🔑 کانفیگ:\n"
            f"`{config.config_text or 'ℹ️ لینک یا فایل کانفیگ ثبت نشده است.'}`\n\n"
            f"✅ لطفاً با پشتیبانی تماس بگیرید در صورت نیاز به راهنما."
        )

        await context.bot.send_message(
    chat_id=user.telegram_id,
    text=message,
    parse_mode="Markdown"
)
        await update.message.reply_text(f"✅ کانفیگ برای {user.username or user.telegram_id} ارسال شد.")

    except VPNConfig.DoesNotExist:
        await update.message.reply_text("❌ کانفیگ یافت نشد.")
    except Exception as e:
        print(f"❌ Error in /sendvpn: {e}")
        await update.message.reply_text("❌ خطایی رخ داد.")

async def send_long_message(chat_id, bot, text, chunk_size=4000):
    for i in range(0, len(text), chunk_size):
        await bot.send_message(chat_id=chat_id, text=text[i:i+chunk_size])


async def vpn_delivery_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment_settings = await sync_to_async(PaymentSettings.objects.get)(active=True)
    admin_id = payment_settings.admin_user_id

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ فقط ادمین می‌تونه این دستور رو اجرا کنه.")
        return

    from vpnuser.models import VPNConfig, VPNDelivery

    all_configs = await sync_to_async(list)(
        VPNConfig.objects.filter(active=True).select_related('subscription_plan')
    )

    deliveries = await sync_to_async(list)(
        VPNDelivery.objects.select_related('user', 'config')
    )
    delivered_map = {d.config.id: d for d in deliveries}

    if not all_configs:
        await update.message.reply_text("⛔️ هیچ کانفیگی در سیستم نیست.")
        return

    lines = ["📦 لیست تمام کانفیگ‌ها:\n"]

    for cfg in all_configs:
        delivered = delivered_map.get(cfg.id)
        base = (
            f"🆔 ID {cfg.id}\n"
            f"📦 {cfg.title}\n"
            f"📅 {cfg.subscription_plan.label}\n"
            f"📶 حجم: {cfg.bandwidth_gb} گیگ\n"
            f"💵 قیمت: {cfg.price_toman:,} تومان\n"
            f"🔑 کانفیگ:\n`{cfg.config_text or 'ثبت نشده'}`"
        )

        if delivered:
            username = delivered.user.username or f"ID {delivered.user.telegram_id}"
            delivered_str = delivered.delivered_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"{base}\n✅ ارسال‌شده به @{username} در {delivered_str}\n")
        else:
            lines.append(f"{base}\n❌ هنوز ارسال نشده\n")

    message = "\n".join(lines)
    await send_long_message(update.effective_chat.id, context.bot, message)


async def my_configs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data["last_menu"] = "main_menu"  # or wherever they came from

    try:
        vpn_user = await sync_to_async(VPNUser.objects.get)(telegram_id=user.id)
    except VPNUser.DoesNotExist:
        await update.callback_query.answer("❌ شما هنوز خریدی انجام نداده‌اید.", show_alert=True)
        return

    deliveries = await sync_to_async(list)(
        VPNDelivery.objects.filter(user=vpn_user).select_related('config', 'config__subscription_plan')
    )

    if not deliveries:
        await update.callback_query.edit_message_text(
            "❌ شما هنوز هیچ کانفیگی دریافت نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ بازگشت", callback_data="back")]
            ])
        )
        return

    lines = ["📦 کانفینگ‌های شما:"]
    for d in deliveries:
        cfg = d.config
        lines.append(
            f"📦 {cfg.title}\n"
            f"🕓 مدت: {cfg.subscription_plan.label}\n"
            f"💰 قیمت: {cfg.price_toman:,} تومان\n"
            f"🔑 کانفیگ:\n`{cfg.config_text or 'ثبت نشده'}`\n"
            f"⏱️ ارسال‌شده در: {d.delivered_at.strftime('%Y-%m-%d %H:%M')}"
        )

    await update.callback_query.edit_message_text(
        "\n\n".join(lines),
        parse_mode="Markdown"
    )
async def handle_renew_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    config_id = int(query.data.split(":")[1])
    config = await sync_to_async(VPNConfig.objects.get)(id=config_id)

    context.user_data["renew_config_id"] = config_id

    payment_settings = await sync_to_async(PaymentSettings.objects.get)(active=True)
    CARD_NUMBER = payment_settings.card_number
    CARD_NAME = payment_settings.card_holder_name

    # Safely retrieve foreign key in async context
    subscription_plan = await sync_to_async(lambda: config.subscription_plan)()
    label = await sync_to_async(lambda: subscription_plan.label)()

    message = (
        f"♻️ تمدید کانفیگ انتخاب‌شده:\n"
        f"📦 {config.title}\n"
        f"📅 {label}\n"
        f"💰 مبلغ: *{config.price_toman:,} تومان*\n\n"
        f"💳 شماره کارت: `{CARD_NUMBER}`\n"
        f"👤 به نام: *{CARD_NAME}*\n\n"
        f"لطفاً عکس فیش واریزی را برای تمدید ارسال کن."
    )

    buttons = [[InlineKeyboardButton("❌ لغو", callback_data="cancel_payment")]]
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_renewal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if "✅" not in message.text.strip():
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        return

    caption = message.reply_to_message.caption
    if not caption:
        return

    import re

    # Try to find user ID
    id_match = re.search(r"ID\s(\d+)", caption)
    user_id = None

    if id_match:
        user_id = int(id_match.group(1))
    else:
        username_match = re.search(r"@(\w+)", caption)
        if username_match:
            username = username_match.group(1)
            from vpnuser.models import VPNUser
            try:
                user_obj = await sync_to_async(VPNUser.objects.get)(username=username)
                user_id = user_obj.telegram_id
            except VPNUser.DoesNotExist:
                await message.reply_text("❌ Username not found in database.")
                return
        else:
            await message.reply_text("❌ Couldn't find user ID or username in the caption.")
            return

    # Extract config title if available
    config_title = "کانفیگ شما"
    title_match = re.search(r"کانفیگ:\s*(.+)", caption)
    if title_match:
        config_title = title_match.group(1).strip()

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ تمدید *{config_title}* با موفقیت تأیید شد.\nاز استفاده‌اش لذت ببر! 🎉",
            parse_mode="Markdown"
        )
        await message.reply_text("✅ پیام تأیید تمدید برای کاربر ارسال شد.")
    except Exception as e:
        await message.reply_text(f"❌ خطا در ارسال پیام به کاربر: {e}")


app = ApplicationBuilder().token("7625318827:AAGFm95bAiCzOr0E4izvS0fY2FmKprGidRo").concurrent_updates(True).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_config_type_selection, pattern="^configs:(volume|unlimited)$"))
app.add_handler(CallbackQueryHandler(back_to_last_menu, pattern="^back$"))
app.add_handler(CallbackQueryHandler(handle_renew_selection, pattern="^renew:[0-9]+$"))

app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))
app.add_handler(CallbackQueryHandler(buy_config_callback, pattern="^buy_config$"))
app.add_handler(CallbackQueryHandler(handle_duration_selection, pattern="^duration:[0-9]+$"))
app.add_handler(CallbackQueryHandler(handle_config_selection, pattern="^buyconfig:[0-9]+$"))
app.add_handler(CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"))
app.add_handler(MessageHandler(filters.PHOTO, handle_payment_photo))
app.add_handler(CommandHandler("sendvpn", send_vpn_config_to_user))
app.add_handler(CommandHandler("vpnlog", vpn_delivery_log))
app.add_handler(CallbackQueryHandler(my_configs_callback, pattern="^my_configs$"))
app.add_handler(CallbackQueryHandler(renew_config_callback, pattern="^renew_config$"))
app.add_handler(MessageHandler(
    filters.TEXT & filters.REPLY & filters.ChatType.PRIVATE,
    handle_renewal_confirmation
))

print("🤖 Bot is running...")

async def main():
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
