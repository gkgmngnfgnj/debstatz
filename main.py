import discord
from discord.ext import tasks
import json
import os
import asyncio

CONFIG_FILE = 'config.json'

def setup_config():
    print("--- First Run Setup ---")
    token = input("What is your discord bot token?: ")
    monitor_id = int(input("What discord id do you want to monitor?: "))
    delay = int(input("What delay (in seconds) do you want for the bot to check?: "))
    channel_id = int(input("Channel ID for status?: "))
    
    use_embed = input("Do you want to use a custom embed? (y/n): ").lower() == 'y'
    embed_json = None
    if use_embed:
        print("Go to discohook.org to design your embed, then paste the 'JSON Data' here:")
        embed_json = input("Embed JSON: ")

    config = {
        "token": token,
        "monitor_id": monitor_id,
        "delay": delay,
        "channel_id": channel_id,
        "use_embed": use_embed,
        "embed_json": embed_json
    }

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    return config

if not os.path.exists(CONFIG_FILE):
    config = setup_config()
else:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

class StatusBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_status = None

    async def setup_hook(self):
        self.check_status.start()

    @tasks.loop(seconds=config['delay'])
    async def check_status(self):
        guilds = self.guilds
        if not guilds: return
        
        member = None
        for guild in guilds:
            m = guild.get_member(config['monitor_id'])
            if m:
                member = m
                break
        
        if member:
            current_status = member.status
            if current_status == discord.Status.offline and self.last_status != discord.Status.offline:
                await self.send_alert(member)
            
            self.last_status = current_status

    async def send_alert(self, member):
        channel = self.get_channel(config['channel_id'])
        if not channel: return

        if config['use_embed'] and config['embed_json']:
            try:
                data = json.loads(config['embed_json'])
                embed_data = data['embeds'][0] if 'embeds' in data else data
                embed = discord.Embed.from_dict(embed_data)
                await channel.send(embed=embed)
            except Exception as e:
                await channel.send(f"⚠️ Error parsing embed: {e}")
        else:
            await channel.send(f"🚨 ALERT: {member.name} has gone offline.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

intents = discord.Intents.default()
intents.members = True
intents.presences = True

client = StatusBot(intents=intents)
client.run(config['token'])
