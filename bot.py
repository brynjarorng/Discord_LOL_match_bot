import discord
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import timedelta, datetime
import json

# load env
load_dotenv()

RIOT_TOKEN = os.getenv("RIOT_TOKEN")
RIOT_API_URL = "https://eun1.api.riotgames.com"
RIOT_BASE_HDR = {"X-Riot-Token": RIOT_TOKEN}
RIOT_QUEUES_FILE_PATH = "queues.json"
RIOT_QUEUES_DATA = {}
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD = os.getenv("DISCORD_GUILD")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")

client = discord.Client()

# load all queue types into a dict
async def load_queues():
    with open(RIOT_QUEUES_FILE_PATH) as json_file:
        queues = json.load(json_file)
        for item in queues:
            RIOT_QUEUES_DATA[item["queueId"]] = {"map": item["map"], "description": item["description"]}
  

@client.event
async def on_ready():
    print(f"{client.user} has connected")

    await client.change_presence(status=discord.Status.online, activity=discord.Game("Listening to !"))

    for g in client.guilds:
        if g.name == DISCORD_GUILD:
            print(f"{client.guilds}")
            break

    # load data
    await load_queues()

async def is_command(message):
    if "!help" in message.content:
        # Return help screen
        resp = message.content
        await message.channel.send(resp[1:])

    elif "!matches" in message.content:
        # Return this weeks match info of the user
        # Need to check out ways to parse strings better

        # Start by getting summoner id
        summoner_name = urllib.parse.quote(message.content[9:])
        r = requests.get(RIOT_API_URL + f"/lol/summoner/v4/summoners/by-name/{summoner_name}", headers=RIOT_BASE_HDR)
        
        if r.status_code != 200:
            await message.channel.send("Error, user not found!")
            return
        
        encrypted_account_id = r.json()["accountId"]

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # create request object
        PARAMS = {"beginTime": str(int(week_start.timestamp()) * 1000), "endTime": str(int(week_end.timestamp())* 1000)}

        r = requests.get(RIOT_API_URL + f"/lol/match/v4/matchlists/by-account/{encrypted_account_id}", params=PARAMS, headers=RIOT_BASE_HDR)
        
        if r.status_code != 200:
            await message.channel.send("You have not played any matches this week!")
            return

        embed = discord.Embed(
            title = "Match history",
            colour = discord.Colour.red()
        )

        matches = r.json()['matches']
        matches_played_per_queue = {}

        for item in matches:
            matches_played_per_queue.setdefault(item["queue"], []).append(item) 

        for key in matches_played_per_queue.keys():
            embed.add_field(name=RIOT_QUEUES_DATA[key]["description"], value=f"{len(matches_played_per_queue[key])}", inline=False)

        await message.channel.send(embed=embed)

@client.event
async def on_message(message):
    if str(message.guild) == DISCORD_GUILD:
        if len(message.content) > 0 and message.content[0] == "!" and not message.author.bot:
            await is_command(message)
            
            #resp = message.content
            #await message.channel.send(resp[1:])

client.run(DISCORD_TOKEN)
