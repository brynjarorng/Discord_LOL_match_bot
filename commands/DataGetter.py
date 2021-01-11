import time
import discord
import os
import requests
import json

from commands.DB import DB

class DataGetter:
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

        self.db = DB()

        self.load_queues()


    """Cleanup"""
    def __exit__(self):
        if(self.CONNECTION):
            self.CURSOR.close()
            self.CONNECTION.close()
            print("PostgreSQL connection is closed")


    # load all queue types into a dict
    def load_queues(self):
        with open(self.RIOT_QUEUES_FILE_PATH) as json_file:
            queues = json.load(json_file)
            for item in queues:
                self.RIOT_QUEUES_DATA[item["queueId"]] = {"map": item["map"], "description": item["description"]}


    """Basic getter, follows the rate limit"""
    def get_data(self, query, header, channel, error, param = {}):
        embed = discord.Embed(
            title = "API cooldown",
            colour = discord.Colour.red()
        )

        # Check short rate limit
        short_cd_remaining = time.time() - self.RIOT_API_SHORT_TIMESTAMP
        if short_cd_remaining <= self.RIOT_API_SHORT_COOLDOWN and self.RIOT_API_REQ_SHORT_CURR_REQ >= self.RIOT_API_REQ_SHORT_MAX_REQ:
            time.sleep(short_cd_remaining)
            self.RIOT_API_REQ_SHORT_CURR_REQ = 0
        else:
            self.RIOT_API_REQ_SHORT_CURR_REQ += 1

            # need to check if rate limit needs to be set again
            if short_cd_remaining > self.RIOT_API_SHORT_COOLDOWN:
                self.RIOT_API_SHORT_TIMESTAMP = time.time()

        # Check long rate limit
        long_cd_remaining = time.time() - self.RIOT_API_LONG_TIMESTAMP
        if short_cd_remaining <= self.RIOT_API_LONG_COOLDOWN and self.RIOT_API_REQ_LONG_CURR_REQ >= self.RIOT_API_REQ_LONG_MAX_REQ:
            embed.add_field(name="WOAH, slow down there cowboy", value=f"Rate limit exceeded, waiting for {round(long_cd_remaining, 2)} seconds", inline=False)
            channel.send(embed=embed)

            time.sleep(long_cd_remaining)
            self.RIOT_API_REQ_LONG_CURR_REQ = 0
        else:
            self.RIOT_API_REQ_LONG_CURR_REQ += 1

            # need to check if rate limit needs to be set again
            if long_cd_remaining > self.RIOT_API_SHORT_COOLDOWN:
                self.RIOT_API_SHORT_TIMESTAMP = time.time()

        # print(time.time() - self.RIOT_API_LONG_TIMESTAMP)
        r = requests.get(query, headers=header, params=param)
        
        if r.status_code != 200:
            print(r.__dict__)
            channel.send(error)
            return None
            
        return r.json()

