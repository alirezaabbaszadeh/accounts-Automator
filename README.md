# Accounts Automator

This repository contains a simple Telegram bot for selling products. The bot
allows administrators to manage products and confirm purchases. After purchase
confirmation, users can retrieve time-based one-time passwords (TOTP) generated
from a provided secret.

## Features

- **Admin commands**
  - `/addproduct <name> <price> <quantity>` – add a new product
  - `/editproduct <name> <price> <quantity>` – edit an existing product
  - `/confirm <user_id> <username> <password> <secret>` – confirm a purchase
  - `/listbuyers <product>` – list buyers of a product
  - `/deletebuyer <user_id>` – remove a buyer
- **User commands**
  - `/listproducts` – list available products
  - `/buy <product>` – start a purchase and send payment screenshot
  - `/getcode` – retrieve the current TOTP code
  - `/myorders` – list your purchases and their status

Product and purchase data are stored in `data.json` in the repository
folder.

## Setup

1. Install dependencies:
   ```bash
   pip install python-telegram-bot pyotp
   ```
2. Set the `BOT_TOKEN` environment variable with your bot's token.
3. Run the bot:
   ```bash
   python bot.py
   ```

Edit `ADMIN_IDS` in `bot.py` and populate it with the Telegram user IDs of the
administrators who can manage products and confirm purchases.
