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
2.  Install the dependencies:
    ```bash
    uv sync --all-packages
    ```3.  Set up the database:
    ```bash
    uv run manage.py migrate
    ```
4.  Run the development server:
    ```bash
    uv run manage.py runserver
    ```

## Testing

To run the tests, use the following command:

```bash
uv run manage.py test
```
