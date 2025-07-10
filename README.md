# accounts-Automator

A simple Telegram bot for managing product sales with two-factor authentication (OTP) support. The bot allows an admin to add products, approve purchases, and buyers to request OTP codes.

## Usage

Set the following environment variables before running:

- `BOT_TOKEN` – Telegram bot token
- `ADMIN_ID` – numeric Telegram user ID of the bot administrator

Run the bot:

```bash
python3 bot.py
```

## Commands

- `/products` – list available products
- `/buy <id>` – start purchase flow for a product
- `/otp <id>` – get the current OTP for a purchased product
- Admin-only commands:
  - `/add_product <name> <price> <username> <password> <secret>`
  - `/approve <user_id> <product_id>`
  - `/list_buyers <product_id>`
  - `/remove_buyer <product_id> <user_id>`

## Testing

Run the tests with:

```bash
python -m pytest
```
