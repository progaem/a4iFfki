# Development Guide for a4iFfki Bot

## Overview
This document provides developers with the necessary information to contribute to the a4iFfki Achievements Bot effectively. It covers the application's architecture, setup, and guidelines for contributing.

## High-level Architecture
The bot is structured around several key components:
- **Telegram Bot Interface:** Manages interactions with users through commands and messages.
- **Sticker Generation:** Employs the DeepAI API to generate stickers from textual descriptions and uses the Google Translate API to facilitate sticker creation in languages other than English.
- **Data Storage:** Uses PostgreSQL for storing user data and MinIO for managing sticker assets.

## Setup and Installation

### Prerequisites
Ensure you have the following installed:
- Docker
- Docker Compose

### Configuration
Fill in the `devo.conf` file with the necessary credentials:
- **PostgreSQL and MinIO:** Credentials and connection details are required to start these services locally.
- **Telegram Bot:** Credentials obtained from @BotFather to configure your instance of the bot.
- **(Optional) API Keys:** Google Translate and DeepAI API keys are _optional_ and can be substituted with a manual sticker generation algorithm as detailed in the comments within [sticker/artist.py](sticker/artist.py#L65).

### Running the Bot
To launch the bot within Docker, execute:
```bash
docker compose up --build -d
```

To stop the bot, run:
```bash
docker compose down
```

For restarting the bot without affecting the database services, use:
```bash
docker-compose build --no-cache app && docker-compose up -d --no-deps --force-recreate app
```

## Contributing

### Contribution Guidelines

- **Code Quality:** Ensure your code adheres to Python's PEP standards and passes lint checks.
- **Testing:** Add unit or integration tests for new features or fixes. Ensure all tests pass before submitting a pull request.
- **Documentation:** Update documentation to reflect changes or add new features.

### Submitting Changes

1. Fork the repository.
2. Create a new branch for each feature or fix.
3. Submit a pull request with a clear description of the changes and any relevant issue numbers.

### Feedback

For any suggestions or discussions regarding the architecture or functionality, please open an issue or pull request on GitHub.