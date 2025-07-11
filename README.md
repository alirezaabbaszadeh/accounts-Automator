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
2. Create `data.json` (already included). Set the following environment variables **before** running the bot:
   - `ADMIN_ID` – Telegram user ID of the admin
   - `ADMIN_PHONE` – phone number shown when users run `/contact`
   
   `bot.py` does not provide real defaults for these values, so you must set them explicitly.
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

Run the container with your bot token:

```bash
docker run --rm accounts-bot <TOKEN>
```
