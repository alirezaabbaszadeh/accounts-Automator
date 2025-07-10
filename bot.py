import json
import os
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import pyotp

DATA_FILE = 'data.json'
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
TOKEN = os.getenv('BOT_TOKEN')

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"products": {}, "pending": []}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def admin_required(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext):
        if update.effective_user.id != ADMIN_ID:
            update.message.reply_text('Unauthorized')
            return
        return func(update, context)
    return wrapped


def start(update: Update, context: CallbackContext):
    update.message.reply_text('Welcome! Use /products to see available items.')


def list_products(update: Update, context: CallbackContext):
    data = load_data()
    if not data['products']:
        update.message.reply_text('No products available.')
        return
    msg = []
    for pid, p in data['products'].items():
        msg.append(f"{pid}. {p['name']} - {p['price']}")
    update.message.reply_text('\n'.join(msg))


def add_product(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 5:
        update.message.reply_text('Usage: /add_product <name> <price> <username> <password> <secret>')
        return
    name, price, username, password, secret = args[0], args[1], args[2], args[3], args[4]
    data = load_data()
    pid = str(len(data['products']) + 1)
    data['products'][pid] = {
        'name': name,
        'price': price,
        'username': username,
        'password': password,
        'secret': secret,
        'buyers': []
    }
    save_data(data)
    update.message.reply_text(f'Product {name} added with id {pid}')


def buy(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        update.message.reply_text('Usage: /buy <product_id>')
        return
    pid = args[0]
    data = load_data()
    if pid not in data['products']:
        update.message.reply_text('Invalid product id')
        return
    context.user_data['buy_pid'] = pid
    update.message.reply_text('Please send payment screenshot to complete purchase.')


def handle_photo(update: Update, context: CallbackContext):
    pid = context.user_data.get('buy_pid')
    if not pid:
        return
    data = load_data()
    data['pending'].append({'user_id': update.effective_user.id, 'product_id': pid})
    save_data(data)
    update.message.reply_text('Payment received, awaiting approval.')
    context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)


def approve(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        update.message.reply_text('Usage: /approve <user_id> <product_id>')
        return
    uid, pid = int(args[0]), args[1]
    data = load_data()
    pending = [p for p in data['pending'] if p['user_id'] == uid and p['product_id'] == pid]
    if not pending:
        update.message.reply_text('No pending purchase found')
        return
    data['pending'] = [p for p in data['pending'] if not (p['user_id'] == uid and p['product_id'] == pid)]
    prod = data['products'][pid]
    prod['buyers'].append(uid)
    save_data(data)
    context.bot.send_message(chat_id=uid, text=f"Purchase approved. Username: {prod['username']} Password: {prod['password']} Use /otp {pid} to get 2FA code.")
    update.message.reply_text('Approved')


def otp(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        update.message.reply_text('Usage: /otp <product_id>')
        return
    pid = args[0]
    data = load_data()
    prod = data['products'].get(pid)
    if not prod:
        update.message.reply_text('Invalid product id')
        return
    if update.effective_user.id not in prod['buyers'] and update.effective_user.id != ADMIN_ID:
        update.message.reply_text('You are not a buyer of this product')
        return
    otp_code = pyotp.TOTP(prod['secret']).now()
    update.message.reply_text(f'OTP: {otp_code}')


def list_buyers(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        update.message.reply_text('Usage: /list_buyers <product_id>')
        return
    pid = args[0]
    data = load_data()
    prod = data['products'].get(pid)
    if not prod:
        update.message.reply_text('Invalid product id')
        return
    buyers = prod['buyers']
    update.message.reply_text('Buyers: ' + ', '.join(map(str, buyers)) if buyers else 'No buyers')


def remove_buyer(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        update.message.reply_text('Usage: /remove_buyer <product_id> <user_id>')
        return
    pid, uid = args[0], int(args[1])
    data = load_data()
    prod = data['products'].get(pid)
    if not prod:
        update.message.reply_text('Invalid product id')
        return
    if uid in prod['buyers']:
        prod['buyers'].remove(uid)
        save_data(data)
        update.message.reply_text('Buyer removed')
    else:
        update.message.reply_text('Buyer not found')


def main():
    if not TOKEN:
        print('BOT_TOKEN not set')
        return
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('products', list_products))
    dp.add_handler(CommandHandler('add_product', add_product, filters=Filters.user(user_id=ADMIN_ID)))
    dp.add_handler(CommandHandler('buy', buy))
    dp.add_handler(CommandHandler('approve', approve, filters=Filters.user(user_id=ADMIN_ID)))
    dp.add_handler(CommandHandler('otp', otp))
    dp.add_handler(CommandHandler('list_buyers', list_buyers, filters=Filters.user(user_id=ADMIN_ID)))
    dp.add_handler(CommandHandler('remove_buyer', remove_buyer, filters=Filters.user(user_id=ADMIN_ID)))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
