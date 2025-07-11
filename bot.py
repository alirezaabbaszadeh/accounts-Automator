# Telegram bot for managing product sales with TOTP support
import json
import logging
import os
import sys
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import pyotp

DATA_FILE = Path('data.json')
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
except ValueError as e:
    logging.error("ADMIN_ID must be an integer")
    raise SystemExit("ADMIN_ID must be an integer") from e
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "+989152062041")  # manager contact number

logging.basicConfig(level=logging.INFO)


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'products': {}, 'pending': []}


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


data = load_data()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome! Use /products to list products.')


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send admin phone number."""
    await update.message.reply_text(f'Admin phone: {ADMIN_PHONE}')


def product_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton('Buy', callback_data=f'buy:{product_id}')]])


async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data['products']:
        await update.message.reply_text('No products available')
        return
    for pid, info in data['products'].items():
        text = f"{pid}: {info['price']}\n{info.get('name', '')}"
        await update.message.reply_text(text, reply_markup=product_keyboard(pid))


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = query.data.split(':')[1]
    context.user_data['buy_pid'] = pid
    await query.message.reply_text('Send payment proof as a photo to proceed.')


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = context.user_data.get('buy_pid')
    if not pid:
        return
    photo = update.message.photo[-1]
    file_id = photo.file_id
    data['pending'].append({'user_id': update.message.from_user.id, 'product_id': pid, 'file_id': file_id})
    save_data(data)
    await update.message.reply_text('Payment submitted. Wait for admin approval.')
    await context.bot.send_photo(ADMIN_ID, file_id, caption=f"/approve {update.message.from_user.id} {pid}")


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        pid = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /approve <user_id> <product_id>')
        return
    for p in data['pending']:
        if p['user_id'] == user_id and p['product_id'] == pid:
            data['pending'].remove(p)
            buyers = data['products'].setdefault(pid, {}).setdefault('buyers', [])
            if user_id not in buyers:
                buyers.append(user_id)
            save_data(data)
            creds = data['products'][pid]
            msg = f"Username: {creds.get('username')}\nPassword: {creds.get('password')}"
            await context.bot.send_message(user_id, msg)
            await context.bot.send_message(user_id, f"Use /code {pid} to get your current authenticator code.")
            await update.message.reply_text('Approved.')
            return
    await update.message.reply_text('Pending purchase not found.')


async def code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = context.args[0]
    except IndexError:
        await update.message.reply_text('Usage: /code <product_id>')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    if update.message.from_user.id not in product.get('buyers', []):
        await update.message.reply_text('You have not purchased this product.')
        return
    secret = product.get('secret')
    if not secret:
        await update.message.reply_text('No TOTP secret set for this product.')
        return
    totp = pyotp.TOTP(secret)
    await update.message.reply_text(f'Code: {totp.now()}')


async def addproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        price = context.args[1]
        username = context.args[2]
        password = context.args[3]
        secret = context.args[4]
    except IndexError:
        await update.message.reply_text('Usage: /addproduct <id> <price> <username> <password> <secret>')
        return
    data['products'][pid] = {
        'price': price,
        'username': username,
        'password': password,
        'secret': secret,
        'buyers': []
    }
    save_data(data)
    await update.message.reply_text('Product added')


async def editproduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        field = context.args[1]
        value = context.args[2]
    except IndexError:
        await update.message.reply_text(
            'Usage: /editproduct <id> <field> <value>'
        )
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    if field not in {'price', 'username', 'password', 'secret'}:
        await update.message.reply_text('Invalid field')
        return
    product[field] = value
    save_data(data)
    await update.message.reply_text('Product updated')


async def resend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
    except IndexError:
        await update.message.reply_text('Usage: /resend <product_id> [user_id]')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    buyers = product.get('buyers', [])
    if len(context.args) > 1:
        try:
            uid = int(context.args[1])
        except ValueError:
            await update.message.reply_text('Invalid user id')
            return
        buyers = [uid] if uid in buyers else []
    if not buyers:
        await update.message.reply_text('No buyers to send to')
        return
    msg = f"Username: {product.get('username')}\nPassword: {product.get('password')}"
    for uid in buyers:
        await context.bot.send_message(uid, msg)
        await context.bot.send_message(uid, f"Use /code {pid} to get your current authenticator code.")
    await update.message.reply_text('Credentials resent')


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
    except IndexError:
        await update.message.reply_text('Usage: /stats <product_id>')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    buyers = product.get('buyers', [])
    text = (
        f"Price: {product.get('price')}\n"
        f"Total buyers: {len(buyers)}"
    )
    await update.message.reply_text(text)


async def buyers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
    except IndexError:
        await update.message.reply_text('Usage: /buyers <product_id>')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    buyers_list = product.get('buyers', [])
    await update.message.reply_text('Buyers: ' + ', '.join(map(str, buyers_list)) if buyers_list else 'No buyers')


async def deletebuyer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
        uid = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /deletebuyer <product_id> <user_id>')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    if uid in product.get('buyers', []):
        product['buyers'].remove(uid)
        save_data(data)
        await update.message.reply_text('Buyer removed')
    else:
        await update.message.reply_text('Buyer not found')


async def clearbuyers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        pid = context.args[0]
    except IndexError:
        await update.message.reply_text('Usage: /clearbuyers <product_id>')
        return
    product = data['products'].get(pid)
    if not product:
        await update.message.reply_text('Product not found')
        return
    product['buyers'] = []
    save_data(data)
    await update.message.reply_text('All buyers removed')


def main(token: str):
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('contact', contact))
    app.add_handler(CommandHandler('products', products))
    app.add_handler(CallbackQueryHandler(buy_callback, pattern=r'^buy:'))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler('approve', approve))
    app.add_handler(CommandHandler('code', code))
    app.add_handler(CommandHandler('addproduct', addproduct))
    app.add_handler(CommandHandler('editproduct', editproduct))
    app.add_handler(CommandHandler('buyers', buyers))
    app.add_handler(CommandHandler('deletebuyer', deletebuyer))
    app.add_handler(CommandHandler('clearbuyers', clearbuyers))
    app.add_handler(CommandHandler('resend', resend))
    app.add_handler(CommandHandler('stats', stats))

    app.run_polling()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python bot.py <TOKEN>')
    else:
        main(sys.argv[1])
