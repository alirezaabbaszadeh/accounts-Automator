import json
import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import pyotp

DATA_FILE = "data.json"

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        DATA = json.load(f)
else:
    DATA = {"products": {}, "purchases": {}}

admin_ids_env = os.environ.get("ADMIN_IDS", "")
# Comma-separated admin Telegram user IDs
ADMIN_IDS = [int(i.strip()) for i in admin_ids_env.split(',') if i.strip()]


def save_data() -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(DATA, f, indent=2)


def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("Access denied")
            return
        return await func(update, context)

    return wrapper


@admin_required
async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /addproduct <name> <price> <quantity>"
        )
        return
    name, price, quantity = context.args[0], context.args[1], context.args[2]
    DATA["products"][name] = {
        "price": price,
        "quantity": int(quantity),
    }
    save_data()
    await update.message.reply_text(f"Product {name} added")


@admin_required
async def editproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /editproduct <name> <price> <quantity>"
        )
        return
    name, price, quantity = context.args[0], context.args[1], context.args[2]
    if name not in DATA["products"]:
        await update.message.reply_text("Product not found")
        return
    DATA["products"][name] = {
        "price": price,
        "quantity": int(quantity),
    }
    save_data()
    await update.message.reply_text(f"Product {name} updated")


async def listproducts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = []
    for name, info in DATA["products"].items():
        lines.append(
            f"{name} - price: {info['price']} quantity: {info['quantity']}"
        )
    if not lines:
        await update.message.reply_text("No products available")
    else:
        await update.message.reply_text("\n".join(lines))


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /buy <product>")
        return
    product = context.args[0]
    if product not in DATA["products"]:
        await update.message.reply_text("Product not found")
        return
    await update.message.reply_text("Please send payment screenshot")
    user_id = update.effective_user.id
    DATA["purchases"][str(user_id)] = {
        "product": product,
        "status": "pending",
    }
    save_data()


@admin_required
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text(
            "Usage: /confirm <user_id> <username> <password> <secret>"
        )
        return
    user_id, username, password, secret = (
        context.args[0],
        context.args[1],
        context.args[2],
        context.args[3],
    )
    if user_id not in DATA["purchases"]:
        await update.message.reply_text("Purchase not found")
        return
    DATA["purchases"][user_id].update(
        {
            "status": "confirmed",
            "username": username,
            "password": password,
            "secret": secret,
        }
    )
    save_data()
    await context.bot.send_message(
        int(user_id),
        f"Purchase confirmed.\nUsername: {username}\nPassword: {password}\nUse /getcode to receive your authenticator code.",
    )
    await update.message.reply_text("Purchase confirmed")


async def getcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    purchase = DATA["purchases"].get(user_id)
    if not purchase or purchase.get("status") != "confirmed":
        await update.message.reply_text("No confirmed purchase found")
        return
    secret = purchase["secret"]
    totp = pyotp.TOTP(secret)
    code = totp.now()
    await update.message.reply_text(f"Your code: {code}")


async def myorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List the user's purchases with product name and status."""
    user_id = str(update.effective_user.id)
    orders = []
    for uid, info in DATA["purchases"].items():
        if uid == user_id or info.get("user_id") == user_id:
            product = info.get("product", "unknown")
            status = info.get("status", "pending")
            orders.append(f"{product} - {status}")

    if not orders:
        await update.message.reply_text("No purchases found")
    else:
        await update.message.reply_text("\n".join(orders))


@admin_required
async def listbuyers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /listbuyers <product>")
        return
    product = context.args[0]
    buyers = [
        uid
        for uid, info in DATA["purchases"].items()
        if info.get("product") == product and info.get("status") == "confirmed"
    ]
    if not buyers:
        await update.message.reply_text("No buyers")
    else:
        await update.message.reply_text("Buyers: " + ", ".join(buyers))


@admin_required
async def deletebuyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /deletebuyer <user_id>")
        return
    user_id = context.args[0]
    if user_id in DATA["purchases"]:
        del DATA["purchases"][user_id]
        save_data()
        await update.message.reply_text("Buyer removed")
    else:
        await update.message.reply_text("Buyer not found")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /listproducts to see available products"
    )


if __name__ == "__main__":
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("Please set BOT_TOKEN environment variable")
        raise SystemExit(1)
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("listproducts", listproducts))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("getcode", getcode))
    application.add_handler(CommandHandler("myorders", myorders))

    application.add_handler(CommandHandler("addproduct", addproduct))
    application.add_handler(CommandHandler("editproduct", editproduct))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CommandHandler("listbuyers", listbuyers))
    application.add_handler(CommandHandler("deletebuyer", deletebuyer))

    application.run_polling()
