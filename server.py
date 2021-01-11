import discord
from discord.ext import commands
from discord import channel

from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import timedelta, datetime
import json
import time

from commands.DataGetter import DataGetter

from commands.utils import print_help
from commands.aram.aram_picker import aram_picker

class Bot(discord.Client):
    def __init__(self):
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.DISCORD_GUILD = os.getenv("DISCORD_GUILD")
        self.DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
        self.data_getter = DataGetter()

        super().__init__()

        
    async def on_ready(self):
        print(f"{self.user} has connected")

        await self.change_presence(status=discord.Status.online, activity=discord.Game("Listening to !"))

        for g in self.guilds:
            if g.name == self.DISCORD_GUILD:
                print(f"{self.guilds}")
                break


    async def on_message(self, message):
        if str(message.guild) == self.DISCORD_GUILD:
            if len(message.content) > 0 and message.content[0] == "!" and not message.author.bot:
                await self.parse_command(message)

        
    async def parse_command(self, message):
        try:
            if "!aram" in message.content:
                await aram_picker(message)
            elif "!deaths" in message.content:
                return 1
            elif "!winrate" in message.content:
                return await get_player_winrate(message)
            else:
                await print_help(message)
        except Exception as e:
            print(e)

    

        


if __name__ == "__main__":    
    # load env
    load_dotenv()

    bot = Bot()
    bot.run(os.getenv("DISCORD_TOKEN"))
