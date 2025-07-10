# accounts-Automator

This project contains a simple Telegram bot for selling products with manual payment approval and two-factor authentication codes.

## Features
- Admin can add products with price, credentials, and TOTP secret.
- Users can browse products and submit payment proof.
- Admin approves purchases and credentials are sent to the buyer.
- Buyers can obtain a current authenticator code with `/code <product_id>`.
- Admin can list and manage buyers.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `data.json` (already included) and set `ADMIN_ID` in `bot.py` to your Telegram user ID.
3. Run the bot with your bot token:
   ```bash
   python bot.py <TOKEN>
   ```

This is a minimal implementation and does not include persistent database storage or full error handling.
