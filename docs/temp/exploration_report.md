# Exploration Report

## 1. Overview

This report details the exploration of the `alice_bp` and `tgbot_bp` services to understand how Telegram identifiers are stored and handled. The primary goal is to identify the current storage mechanism and data flow to inform the design of a more secure solution.

## 2. Discovered Services and Components

The repository contains two main services:

*   **`alice_bp`**: A Django project that serves as the main backend. It exposes a REST API for managing users, measurements, and other data.
    *   **Framework**: Django, Django Rest Framework
    *   **Database**: SQLite (default, based on `settings.py`), but configurable via `dj-database-url`.
    *   **Key Components**:
        *   `alice_skill/models.py`: Defines the database schema, including the `AliceUser` model.
        *   `alice_skill/views.py`: Contains the API endpoints, including a view to fetch users by Telegram ID.
        *   `alice_skill/services.py`: Implements the business logic for account linking.
        *   `config/settings.py`: Django settings.

*   **`tgbot_bp`**: An `aiogram`-based Telegram bot that interacts with users and communicates with the `alice_bp` backend.
    *   **Framework**: `aiogram`
    *   **Key Components**:
        *   `tgbot/handlers/user.py`: Handles incoming messages and user commands.
        *   `infrastructure/bp_api/api.py`: A client to interact with the `alice_bp` REST API.
        *   `main.py`: The main entry point for the bot.

## 3. Data Flow and Storage of Telegram Identifiers

The exploration revealed the following data flow for Telegram identifiers:

1.  A user interacts with the Telegram bot (`tgbot_bp`).
2.  The `aiogram` library captures the user's Telegram ID (e.g., from `message.from_user.id`).
3.  The bot's handlers in `tgbot/handlers/user.py` receive the Telegram ID.
4.  The bot's API client (`infrastructure/bp_api/api.py`) sends the Telegram ID to the `alice_bp` backend API.
5.  The `alice_bp` backend receives the Telegram ID in its views (`alice_skill/views.py`).
6.  The `AliceUser` model in `alice_skill/models.py` has a field `telegram_user_id` of type `models.CharField`. This field stores the user's Telegram ID in **plaintext**.
7.  The backend uses this plaintext `telegram_user_id` to look up users and perform other operations.

**Key file confirming plaintext storage:**

*   `alice_skill/models.py`:
    ```python
    class AliceUser(models.Model):
        user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
        alice_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
        telegram_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
        # ...
    ```

## 4. Threat Model

*   **Attacker Capabilities**: An attacker is assumed to have gained read access to the `alice_bp` application's database (e.g., through SQL injection, a compromised server, or a leaked database backup).
*   **Primary Threat**: With access to the database, the attacker can read the `alice_skill_aliceuser` table and directly link the application's internal user records to their corresponding Telegram accounts via the plaintext `telegram_user_id`. This compromises user privacy.
*   **Impact**: A data breach would allow the attacker to deanonymize users and associate their activities within the application with their public Telegram profiles.

## 5. Conclusion

The current implementation stores Telegram user IDs in plaintext, which poses a significant security risk. A new design is required to protect this sensitive information. The next step is to create a design document for a secure storage mechanism.
