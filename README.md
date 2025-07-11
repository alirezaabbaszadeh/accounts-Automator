# accounts-Automator

This project contains a simple Telegram bot for selling products with manual payment approval and two-factor authentication codes.

## Features
- Admin can add products with price, credentials, and TOTP secret.
- Users can browse products and submit payment proof.
- Admin approves purchases and credentials are sent to the buyer.
- Buyers can obtain a current authenticator code with `/code <product_id>`.
- Admin can list and manage buyers.
- Admin can edit product fields with `/editproduct` and resend credentials with
  `/resend`.
- Stats for each product available via `/stats`.
- Users can view the admin phone number with `/contact`.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. The bot stores its state in a `data.json` file which is ignored by Git.
   The file will be created automatically on first run if it doesn't exist.
   If you prefer to create it manually, start with the following content:

   ```json
   {"products": {}, "pending": []}
   ```

   Set the following environment variables explicitly:
   - `ADMIN_ID` – Telegram user ID of the admin
   - `ADMIN_PHONE` – phone number shown when users run `/contact`
3. Run the bot with your bot token:
   ```bash
   python bot.py <TOKEN>
   ```

This is a minimal implementation and does not include persistent database storage or full error handling.

## Docker

A `Dockerfile` is provided to run the bot in a container.

Build the image:

```bash
docker build -t accounts-bot .
```

Run the container with your bot token. You can also set environment variables
for the admin using `-e` flags:

```bash
docker run --rm -e ADMIN_ID=<YOUR_ID> -e ADMIN_PHONE=<YOUR_PHONE> accounts-bot <TOKEN>
```
