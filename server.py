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

from db import DB

from commands import parse_command

class Bot(discord.Client):
    def __init__(self):
        self.RIOT_TOKEN = os.getenv("RIOT_TOKEN")
        self.RIOT_API_URL = "https://eun1.api.riotgames.com"
        self.RIOT_BASE_HDR = {"X-Riot-Token": self.RIOT_TOKEN}
        self.RIOT_QUEUES_FILE_PATH = "data/queues.json"
        self.RIOT_QUEUES_DATA = {}
        self.RIOT_API_REQ_SHORT_MAX_REQ = 20
        self.RIOT_API_REQ_SHORT_CURR_REQ = 0
        self.RIOT_API_SHORT_COOLDOWN = 1
        self.RIOT_API_SHORT_TIMESTAMP = time.time()
        self.RIOT_API_REQ_LONG_MAX_REQ = 100
        self.RIOT_API_REQ_LONG_CURR_REQ = 0
        self.RIOT_API_LONG_COOLDOWN = 120
        self.RIOT_API_LONG_TIMESTAMP = time.time()
        self.DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
        self.DISCORD_GUILD = os.getenv("DISCORD_GUILD")
        self.DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
        self.db = DB()

        super().__init__()

        
    async def on_ready(self):
        print(f"{self.user} has connected")

        await self.change_presence(status=discord.Status.online, activity=discord.Game("Listening to !"))

        for g in self.guilds:
            if g.name == self.DISCORD_GUILD:
                print(f"{self.guilds}")
                break

        # load data
        await self.load_queues()


    async def on_message(self, message):
        if str(message.guild) == self.DISCORD_GUILD:
            if len(message.content) > 0 and message.content[0] == "!" and not message.author.bot:
                await parse_command(message)

        

    # load all queue types into a dict
    async def load_queues(self):
        with open(self.RIOT_QUEUES_FILE_PATH) as json_file:
            queues = json.load(json_file)
            for item in queues:
                self.RIOT_QUEUES_DATA[item["queueId"]] = {"map": item["map"], "description": item["description"]}

        


if __name__ == "__main__":    
    # load env
    load_dotenv()

    bot = Bot()
    bot.run(os.getenv("DISCORD_TOKEN"))
