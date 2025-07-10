import os
import json
import pyotp
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"products": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the shop bot")


def add_product(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != os.environ.get('ADMIN_ID'):
        return
    args = context.args
    if len(args) < 3:
        update.message.reply_text("Usage: /addproduct <id> <price> <secret>")
        return
    pid, price, secret = args[0], args[1], args[2]
    data = load_data()
    data['products'][pid] = {"price": price, "secret": secret, "buyers": []}
    save_data(data)
    update.message.reply_text(f"Product {pid} added.")


def buy(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 1:
        update.message.reply_text("Usage: /buy <product_id>")
        return
    pid = args[0]
    data = load_data()
    if pid not in data['products']:
        update.message.reply_text("Product not found")
        return
    context.user_data['pending_product'] = pid
    update.message.reply_text("Send payment proof as an image.")


def handle_photo(update: Update, context: CallbackContext):
    pid = context.user_data.get('pending_product')
    if not pid:
        return
    admin_id = os.environ.get('ADMIN_ID')
    if admin_id:
        context.bot.send_message(admin_id, f"Payment proof from {update.effective_user.id} for product {pid}.")
        context.bot.forward_message(admin_id, update.message.chat_id, update.message.message_id)
    context.user_data['pending_photo'] = update.message.message_id


def approve(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != os.environ.get('ADMIN_ID'):
        return
    args = context.args
    if len(args) < 2:
        update.message.reply_text("Usage: /approve <product_id> <user_id>")
        return
    pid, uid = args[0], args[1]
    data = load_data()
    if pid not in data['products']:
        update.message.reply_text("Product not found")
        return
    if uid not in data['products'][pid]['buyers']:
        data['products'][pid]['buyers'].append(uid)
        save_data(data)
    context.bot.send_message(uid, f"Your purchase for product {pid} is approved.")
    context.bot.send_message(uid, f"Use /code {pid} to get your authentication code.")
    update.message.reply_text("Approved.")


def code(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 1:
        update.message.reply_text("Usage: /code <product_id>")
        return
    pid = args[0]
    data = load_data()
    if pid not in data['products']:
        update.message.reply_text("Product not found")
        return
    if str(update.effective_user.id) not in data['products'][pid]['buyers']:
        update.message.reply_text("You are not a buyer of this product.")
        return
    secret = data['products'][pid]['secret']
    totp = pyotp.TOTP(secret)
    update.message.reply_text(f"Code: {totp.now()}")


def list_buyers(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != os.environ.get('ADMIN_ID'):
        return
    args = context.args
    if len(args) < 1:
        update.message.reply_text("Usage: /listbuyers <product_id>")
        return
    pid = args[0]
    data = load_data()
    if pid not in data['products']:
        update.message.reply_text("Product not found")
        return
    buyers = data['products'][pid]['buyers']
    update.message.reply_text("Buyers:\n" + "\n".join(buyers))


def remove_buyer(update: Update, context: CallbackContext):
    if str(update.effective_user.id) != os.environ.get('ADMIN_ID'):
        return
    args = context.args
    if len(args) < 2:
        update.message.reply_text("Usage: /removebuyer <product_id> <user_id>")
        return
    pid, uid = args[0], args[1]
    data = load_data()
    if pid in data['products'] and uid in data['products'][pid]['buyers']:
        data['products'][pid]['buyers'].remove(uid)
        save_data(data)
        update.message.reply_text("Removed")
    else:
        update.message.reply_text("Not found")


def main():
    token = os.environ['TELEGRAM_TOKEN']
    updater = Updater(token)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('addproduct', add_product))
    dp.add_handler(CommandHandler('buy', buy))
    dp.add_handler(CommandHandler('approve', approve))
    dp.add_handler(CommandHandler('code', code))
    dp.add_handler(CommandHandler('listbuyers', list_buyers))
    dp.add_handler(CommandHandler('removebuyer', remove_buyer))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
