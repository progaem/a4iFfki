# a4iFfki Achievements Bot
[![Docker Image Version](https://img.shields.io/docker/v/rus2m/achievements-bot-app)](https://hub.docker.com/repository/docker/rus2m/achievements-bot-app/general) ![pylint](https://img.shields.io/badge/PyLint-8.14-yellow?logo=python&logoColor=white)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/progaem)

## Introduction
The **a4iFfki Achievements Bot** for Telegram is designed to recognize and celebrate individual and group achievements within chat environments. It allows users to create and assign unique stickers that symbolize specific achievements, enhancing engagement and interaction.

## Features
- **Individual Sticker Sets:** Each Telegram user can have their own set of stickers that represent their personal achievements.
- **Group Sticker Sets:** Chats can maintain collective sticker sets to track of all achievements awarded to the chat members
- **AI-Generated Stickers:** Stickers are dynamically created with AI, based on the descriptions provided during the achievement assignment.

## Getting Started

### Sticker Management
To begin managing stickers, a user with a PREMIUM account must take ownership by sending `/own_stickers` in the chat. This user will manage both individual and group sticker sets.

**Important:** The owner should not alter these stickers outside of the bot commands, as it could interfere with the bot's tracking capabilities.

### Assigning Achievements
- **New Achievements:** Reply to a chat message with the trigger phrase (e.g., `выдаю ачивку за [achievement description]` or `drop an achievement for [achievement description]`, here's[the link for full list of key phrases](https://github.com/progaem/a4iFfki/blob/master/resources/key.txt)). The bot will process the information and add appropriate stickers to both personal and group sets.
- **Existing Achievements:** To assign an already established achievement, reply with its corresponding sticker from the group set. The system automatically updates the achievement count.

## FAQ

**Why did I receive a warning for excessive bot usage?**
- The bot operates with usage limitations to maintain budget constraints: a maximum of two achievements per person per day. Exceeding this may trigger temporary restrictions.

**What should I do if I encounter issues with the bot?**
- If the bot malfunctions or behaves unexpectedly, please report the issue through our [GitHub Issues](https://github.com/progaem/a4iFfki/issues) page. Detail the steps taken to replicate the problem, and any screenshots or logs that might help diagnose the issue.

## Development and Contributions
Interested in contributing? We encourage community contributions! Please check our [Development Guide](src/DEVELOPMENT.md) for details on how to get started.

## License
This project is licensed under the [MIT License](LICENSE). See the LICENSE file for more details.