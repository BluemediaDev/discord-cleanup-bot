# discord-cleanup-bot
A simple discord bot to clean up messages in a channel after a configured amount of time.

## Limitations / special features
- Only messages not older than 14 days can be deleted
- Threads are not processed by the bot
- Pinned messages are excluded from deletion

## Setup using Docker
Using Docker is the easiest way to use this bot:
1. Copy the `docker-compose.yaml` to your server
2. Create a bot account [using this guide](https://discordpy.readthedocs.io/en/stable/discord.html#creating-a-bot-account) (ignore the "Inviting Your Bot" section - the bot will show you the correct invite link later)
3. Paste your bot token behind `BOT_TOKEN=` in the `docker-compose.yaml`
4. Start the container using `docker compose up -d`
5. Run `docker compose logs` and copy the invite link to your browser

## Manual setup
If you don't want to use Docker, you can set up the bot manually:
1. Clone the Git repo
2. Create and activate a new venv
3. Install the requirements using `requirements.txt`
4. Create a bot account [using this guide](https://discordpy.readthedocs.io/en/stable/discord.html#creating-a-bot-account) (ignore the "Inviting Your Bot" section - the bot will show you the correct invite link later)
5. Set your bot token in the environment variable `BOT_TOKEN` and specify a file path for the SQLite database using `DB_PATH`
6. Start the `bot.py` script
7. Copy the invite link to your browser

## Commands
All commands provide help messages and support auto-completion.
- `/purge (days)` Delete all messages of the last x days now an only once.
- `/retention [get|set|disable] (retention_period)` Manage continous cleanup. The background job runs every 15 minutes.