# accounts-Automator

This repository contains a simple Telegram bot example for selling products. The bot allows an admin user to manage products and approve purchases. After approval, the bot generates time-based authentication codes (TOTP) for the buyer using a shared secret.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a Telegram bot and obtain the bot token.
3. Set the following environment variables before running:
   - `TELEGRAM_TOKEN`: token for your bot
   - `ADMIN_ID`: Telegram user ID of the admin

Run the bot with:
```bash
python bot.py
```

## Commands

- `/addproduct <id> <price> <secret>` – add or update a product. Only the admin can run this.
- `/buy <product_id>` – buyer starts the purchase process and sends an image as payment proof.
- `/approve <product_id> <user_id>` – admin approves a buyer and sends them instructions to receive the code.
- `/code <product_id>` – buyer receives the current authenticator code (valid for 30 seconds) for the product.
- `/listbuyers <product_id>` – admin views buyers for a product.
- `/removebuyer <product_id> <user_id>` – admin removes a buyer from a product.

Product and buyer data is stored in `data.json` in the working directory.
