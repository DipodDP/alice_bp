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

*   **"Свяжи аккаунт"** - Complete the account linking process using the code from Telegram.
*   **"Запомни давление 120 на 80"** - Record a new blood pressure measurement.
*   **"Покажи последнее давление"** - View your last recorded measurement.
*   **"Отвяжи аккаунт"** - Unlink your Alice and Telegram accounts.

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
    pip install -r requirements.txt
    ```
3.  Set up the database:
    ```bash
    python manage.py migrate
    ```
4.  Run the development server:
    ```bash
    python manage.py runserver
    ```

## Testing

To run the tests, use the following command:

```bash
python manage.py test
```
