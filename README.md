# Alice BP

Blood Pressure Measurements with Alice and Telegram.

## About the Project

This project allows users to link their Yandex.Alice account with their Telegram account to record and track their blood pressure measurements.

## Features

*   **Account Linking:** Securely link your Alice and Telegram accounts using a one-time token.
*   **Record Measurements:** Record your blood pressure measurements (systolic, diastolic, and pulse) through Alice.
*   **View Measurements:** View your last recorded measurement through Alice.
*   **Unlinking:** Unlink your accounts from either Alice or Telegram.
*   **Rate Limiting:** To prevent abuse, token generation is rate-limited.
*   **Audit Logging:** All linking attempts are logged for security purposes.
*   **Secure Telegram ID Handling:** Telegram user IDs are hashed using HMAC-SHA256 before storage to protect user privacy.

## How to Use

### Telegram

*   `/start` - Start the bot and get a greeting message.
*   `/link` - Initiate account linking and receive a one-time code.
*   `/unlink` - Unlink your Alice and Telegram accounts.
*   `/help` - Get help on how to use the bot.

### Alice

*   **"Свяжи аккаунт <КОД>"** - Complete the account linking process using the code from Telegram (e.g., "Свяжи аккаунт мост-627").
*   **"Запомни давление 120 на 80"** - Record a new blood pressure measurement.
*   **"Покажи последнее давление"** - View your last recorded measurement.
*   **"Отвяжи аккаунт"** - Unlink your Alice and Telegram accounts.

## API Endpoints

### Alice Skill Endpoints

*   `POST /alice_webhook/`: Receives and processes webhook requests from Yandex.Alice.
*   `GET /api/v1/link/status/`: Checks the linking status of Alice and Telegram accounts.
*   `POST /api/v1/link/unlink/`: Unlinks Alice and Telegram accounts.
*   `GET /api/v1/users/by-telegram/<str:telegram_id>/`: Retrieves user information by Telegram ID.
*   `POST /api/v1/link/generate-token/`: Generates a one-time token for account linking.
*   `GET /api/v1/measurements/`: Retrieves a list of blood pressure measurements.
*   `POST /api/v1/measurements/`: Records a new blood pressure measurement.
*   `GET /api/v1/measurements/<id>/`: Retrieves a specific blood pressure measurement by ID.
*   `PUT /api/v1/measurements/<id>/`: Updates a specific blood pressure measurement by ID.
*   `PATCH /api/v1/measurements/<id>/`: Partially updates a specific blood pressure measurement by ID.
*   `DELETE /api/v1/measurements/<id>/`: Deletes a specific blood pressure measurement by ID.

### Python Anywhere Background Endpoints

*   `GET /background/`: Provides a status page for the external bot subprocess.
*   `GET /background/start/`: Starts the external bot subprocess.
*   `POST /webhook/`: Proxies incoming webhook requests to the local bot server.

### Telegram Bot API Endpoints (Consumed)

The Telegram bot consumes the following endpoints from the Alice Skill API:

*   `GET /api/v1/measurements/`: Retrieves blood pressure measurements (for last week's report and last measurement).
*   `GET /api/v1/users/by-telegram/<str:telegram_id>/`: Retrieves user information by Telegram ID to check linking status.
*   `POST /api/v1/link/generate-token/`: Generates a one-time token for account linking.
*   `POST /api/v1/link/unlink/`: Unlinks Alice and Telegram accounts.

For full details on these endpoints, refer to the "Alice Skill Endpoints" section.

## Security

### Webhook Security

To secure the webhooks and ensure that requests are only coming from Yandex and Telegram, the application uses secret tokens. You must configure these for the application to work correctly with webhooks.

### Telegram ID Hashing

For privacy and security, Telegram user IDs are hashed using HMAC-SHA256 before being stored in the database. The hashing is performed at the API boundary, ensuring that plaintext Telegram IDs never enter the database.

**Required Environment Variables:**

*   **`TELEGRAM_ID_HMAC_KEY`**: A secret key used for HMAC-SHA256 hashing of Telegram user IDs. This must be a secure, random string. Generate it using one of the methods described in the "Token Generation Examples" section below.
*   **`LINK_SECRET`**: A secret key used for hashing account linking tokens. This must be a secure, random string. Generate it using one of the methods described in the "Token Generation Examples" section below.

**Important:** Both `TELEGRAM_ID_HMAC_KEY` and `LINK_SECRET` are required and must be set in your environment. The application will fail to start if these are not configured.

#### Token Generation Examples

You can use one of the following commands to generate a secure random string for your tokens:

**Using `openssl`:**
```bash
openssl rand -hex 32
```

**Using `/dev/urandom` (on Linux/macOS):**
```bash
head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32
```

**Django:**
```bash
echo "SECRET_KEY=$(uv run - <<'PY'                                                                                                     ─╯
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
PY
)" >> .env
chmod 600 .env
```


### Alice (Yandex.Dialogs)

The Alice webhook is secured using a token passed in the URL as a query parameter.

1.  **Generate a Secret:** Create a long, random, and secure string for your secret token.
2.  **Set Environment Variable:** Set the `ALICE_WEBHOOK_SECRET` environment variable to your generated secret.
3.  **Configure Webhook URL:** In the Yandex.Dialogs console, set your webhook URL to:
    ```
    https://your-domain.com/alice_webhook?token=YOUR_SECRET_TOKEN
    ```
    Replace `YOUR_SECRET_TOKEN` with the secret you generated.

4.  **Get the Full URL:** To easily get the full, correctly formatted webhook URL, run the following management command:
    ```bash
    uv run manage.py print_alice_webhook
    ```
    This will print the URL to your console, which you can then copy and paste into the Yandex.Dialogs console.

### Telegram

The Telegram bot webhook is secured using a secret token sent in the `X-Telegram-Bot-Api-Secret-Token` header.

1.  **Generate a Secret:** Create a long, random, and secure string for your secret token (1-256 characters: A-Z, a-z, 0-9, _ and -).
2.  **Set Environment Variable:** Set the `BOT_WEBHOOK_SECRET` environment variable to your generated secret.
3.  **Set Webhook with Telegram:** When you set your webhook URL with the Telegram Bot API, include the `secret_token` parameter. The bot application will handle this automatically if you are running it in webhook mode.

#### Local Development Note

When running the application locally with a tunneling service like `localtunnel` (`loca.lt`), be aware that these services often **do not forward custom HTTP headers**. This means the `X-Telegram-Bot-Api-Secret-Token` header sent by Telegram will not reach your application.

To handle this during local development, simply **do not set** the `BOT_WEBHOOK_SECRET` environment variable in your `.env` file. The application is configured to bypass the secret check when this variable is empty.

In a **production environment**, you **must** set `BOT_WEBHOOK_SECRET` to a secure value. The application will then enforce the secret token check.



## User Management

This project now includes a link between the Django `User` model and the Alice `AliceUser` model. This allows for more robust authentication and authorization.

### API Authentication

Access to the `/api/v1/measurements/` endpoint is restricted to authenticated Django users. Users can only view their own measurements. Superusers can view all measurements.

## Management Commands

This project includes custom management commands to help with user administration.

### `check_user_timezone`

Check the timezone for a user by their Alice User ID or Telegram User ID.

**Usage:**

```bash
uv run manage.py check_user_timezone --alice-user-id <alice_user_id>
```

or

```bash
uv run manage.py check_user_timezone --telegram-user-id <telegram_user_id>
```

You can also list all users and their timezones:

```bash
uv run manage.py check_user_timezone --list-all
```

### `update_user_timezone`

Update the timezone for a user.

**Usage:**

```bash
uv run manage.py update_user_timezone --alice-user-id <alice_user_id> --timezone <timezone>
```

or

```bash
uv run manage.py update_user_timezone --telegram-user-id <telegram_user_id> --timezone <timezone>
```

Example:

```bash
uv run manage.py update_user_timezone --alice-user-id "some_long_id" --timezone "Europe/Moscow"
```

### `migrate_telegram_ids`

Migrates existing plaintext Telegram user IDs to HMAC-SHA256 hashed values. This command is useful when upgrading from a version that stored plaintext IDs to the current version that uses hashed IDs.

**Usage:**

```bash
uv run manage.py migrate_telegram_ids
```

**Options:**

*   `--dry-run`: Simulates the migration without making any changes to the database. Use this to preview what would be migrated.

**Examples:**

Preview the migration without making changes:

```bash
uv run manage.py migrate_telegram_ids --dry-run
```

Perform the actual migration:

```bash
uv run manage.py migrate_telegram_ids
```

**Note:** The command automatically skips Telegram IDs that are already hashed (64-character hex strings). It only migrates plaintext IDs that need to be hashed.

## Getting Started

### Prerequisites

*   Python 3.11+
*   Django 4.2+
*   aiogram 3.x

### Installation



1.  Clone the repository:

    ```bash

    git clone https://github.com/your-username/alice-bp.git

    ```

2.  Set up your environment variables. Copy the `.env.dist` file to `.env` and fill in the required values, including the secret tokens as described in the "Security" section. You must set the following required environment variables:

    *   `TELEGRAM_ID_HMAC_KEY`: Secret key for hashing Telegram user IDs
    *   `LINK_SECRET`: Secret key for hashing account linking tokens
    *   `ALICE_WEBHOOK_SECRET`: Secret token for Alice webhook authentication (optional for local development)
    *   `BOT_WEBHOOK_SECRET`: Secret token for Telegram bot webhook authentication (optional for local development)

    ```bash

    cp .env.dist .env

    ```

3.  Install the dependencies:

    ```bash

    uv sync --all-packages

    ```

4.  Set up the database:

    ```bash

    uv run manage.py migrate

    ```

5.  (Optional) If you have existing data with plaintext Telegram user IDs, migrate them to hashed values:

    ```bash

    uv run manage.py migrate_telegram_ids --dry-run  # Preview changes first
    uv run manage.py migrate_telegram_ids             # Perform the migration

    ```

6.  Run the development server:

    ```bash

    uv run manage.py runserver

    ```

## Testing

To run the tests, use the following command:

```bash
uv run manage.py test
```
