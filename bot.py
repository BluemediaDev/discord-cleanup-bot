import os, logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Guild, Channel, Base

import discord
from discord import app_commands, CustomActivity
from discord.app_commands import Choice
from discord.ext import tasks

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

sqla_engine = create_engine(f'sqlite:///{os.getenv("DB_PATH", "bot.db")}')
Base.metadata.create_all(sqla_engine)

# Yield successive n-sized
# chunks from l.
def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n): 
        yield l[i:i + n]

async def purge_messages(channel, audit_message: str, before: datetime, after: datetime):
    messages = [message async for message in channel.history(before=before, after=after)]
    filtered_messages = [m for m in messages if m.pinned == False]
    message_chunks = divide_chunks(filtered_messages, 100)
    for chunk in message_chunks:
        await channel.delete_messages(chunk, reason=audit_message)

class BotClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        self.background_task.start()

    @tasks.loop(minutes=15)
    async def background_task(self):
        with Session(sqla_engine) as session:
            persisted_channels = session.query(Channel).order_by(Channel.last_pruned.desc()).limit(5).all()
            for persisted_channel in persisted_channels:
                channel = self.get_channel(persisted_channel.channel_id)
                logger.info(f"Cleaning channel {persisted_channel.channel_id} in guild {persisted_channel.guild_id} ({channel.guild.name})")
                now = datetime.now()
                before = now - timedelta(hours=persisted_channel.retention_hours)
                after = now - timedelta(days=14)
                await purge_messages(channel=channel, audit_message='Configured retention period expired.', before=before, after=after)
                persisted_channel.last_pruned=now
            session.commit()

    @background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

intents = discord.Intents.default()
client = BotClient(intents=intents)

@client.event
async def on_guild_join(guild):
    with Session(sqla_engine) as session:
        new_guild = Guild(guild_id=guild.id)
        session.add(new_guild)
        session.commit()

@client.event
async def on_guild_remove(guild):
    with Session(sqla_engine) as session:
        removed_guild = session.get(Guild, guild.id)
        if removed_guild == None:
            return
        session.delete(removed_guild)
        session.commit()

@client.event
async def on_guild_channel_delete(channel):
    with Session(sqla_engine) as session:
        removed_channel = session.get(Channel, channel.id)
        if removed_channel == None:
            return
        session.delete(removed_channel)
        session.commit()

@client.tree.command()
@app_commands.guild_only()
@app_commands.describe(
    action='Action to perform',
    retention_period='Use thogether with the "set" action to define a retention period in days',
)
@app_commands.choices(action=[
    Choice(name='get', value=1),
    Choice(name='set', value=2),
    Choice(name='disable', value=3),
])
async def retention(interaction: discord.Interaction, action: Choice[int], retention_period: Optional[int] = None):
    """Manage retention settings for a channel."""
    match action.value:
        case 1:
            with Session(sqla_engine) as session:
                persisted_channel = session.get(Channel, interaction.channel_id)
                if persisted_channel == None:
                    await interaction.response.send_message(content='ℹ️ There is currently no retention period set for this channel.', delete_after=20)
                    return
                await interaction.response.send_message(content=f'ℹ️ Messages in this channel will currently be deleted after `{persisted_channel.retention_hours / 24}` days.', delete_after=20)
        case 2:
            if retention_period == None:
                await interaction.response.send_message(content='❌ Error: You need to specify a `retention_period` when using the `set` action', delete_after=20)
                return
            if retention_period > 13:
                await interaction.response.send_message(content='❌ Error: Due to technical limitations, 13 days is the maximum after which I can still delete messages. Please use `13` or less as the retention period.', delete_after=20)
                return
            with Session(sqla_engine) as session:
                channel = session.get(Channel, interaction.channel_id)
                if channel == None:
                    channel = Channel(channel_id=interaction.channel_id, guild_id=interaction.guild_id, retention_hours=(retention_period * 24), last_pruned=datetime.min)
                    session.add(channel)
                else:
                    channel.retention_hours = retention_period * 24
                session.commit()
            await interaction.response.send_message(content=f'✅ Messages in this channel will be automatically deleted after `{retention_period}` days.', delete_after=20)
        case 3:
            with Session(sqla_engine) as session:
                channel = session.get(Channel, interaction.channel_id)
                if channel != None:
                    session.delete(channel)
                session.commit()
            await interaction.response.send_message(content='✅ Messages in this channel will no loger be automatically deleted.', delete_after=20)

@client.tree.command()
@app_commands.guild_only()
@app_commands.describe(
    days='Delete messages of the last x days'
)
async def purge(interaction: discord.Interaction, days: int):
    """Clear messages of the last x days in the current channel."""
    if days > 13:
        await interaction.response.send_message(content='❌ Error: Due to technical limitations, 13 days is the maximum after which I can still delete messages. Please use `13` days or less.', delete_after=20)
        return
    await purge_messages(channel=interaction.channel, audit_message=f'Deleted via /purge command from user {interaction.user.name}', before=datetime.now(), after=(datetime.now() - timedelta(days=days)))
    await interaction.response.send_message(content='✅ Messages deleted.', delete_after=20)


client.activity = CustomActivity(name="Cleaning up your sh*t")

client.run(token=os.getenv("BOT_TOKEN"), log_handler=None)