import discord
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import timedelta, datetime
import json
import time

# load env
load_dotenv()

RIOT_TOKEN = os.getenv("RIOT_TOKEN")
RIOT_API_URL = "https://eun1.api.riotgames.com"
RIOT_BASE_HDR = {"X-Riot-Token": RIOT_TOKEN}
RIOT_QUEUES_FILE_PATH = "queues.json"
RIOT_QUEUES_DATA = {}
RIOT_API_REQ_SHORT_MAX = 20
RIOT_API_SHORT_COOLDOWN = 1
RIOT_API_SHORT_TIMESTAMP = time.time()
RIOT_API_REQ_LONG_MAX = 100
RIOT_API_LONG_COOLDOWN = 120
RIOT_API_LONG_TIMESTAMP = time.time()
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


async def get_summoner_by_name(message, user):
    summoner_name = urllib.parse.quote(user)
    r = requests.get(RIOT_API_URL + f"/lol/summoner/v4/summoners/by-name/{summoner_name}", headers=RIOT_BASE_HDR)
    
    if r.status_code != 200:
        await message.channel.send("Error, user not found!")
        return None
        
    return r.json()


async def get_player_match_history(message, encrypted_account_id, week_start, week_end):
    # create request object
    PARAMS = {"beginTime": str(int(week_start.timestamp()) * 1000), "endTime": str(int(week_end.timestamp())* 1000)}

    r = requests.get(RIOT_API_URL + f"/lol/match/v4/matchlists/by-account/{encrypted_account_id}", params=PARAMS, headers=RIOT_BASE_HDR)
    
    if r.status_code != 200:
        await message.channel.send("You have not played any matches this week!")
        return None

    matches_obj = r.json()['matches']
    matches_played_per_queue = {}

    for item in matches_obj:
        matches_played_per_queue.setdefault(item["queue"], []).append(item) 
    
    return matches_played_per_queue


""" Display number of matches played of a specific player """
async def matches(message):
     # Return this weeks match info of the user
    # Need to check out ways to parse strings better

    # Start by getting summoner id
    summoner = await get_summoner_by_name(message, message.content[9:])
    if summoner == None:
        return
    
    encrypted_account_id = summoner["accountId"]

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    matches_played_per_queue = await get_player_match_history(message, encrypted_account_id, week_start, week_end)
    if matches_played_per_queue == None:
        return

    embed = discord.Embed(
        title = "Match history",
        colour = discord.Colour.red()
    )

    for key in matches_played_per_queue.keys():
        embed.add_field(name=RIOT_QUEUES_DATA[key]["description"], value=f"{len(matches_played_per_queue[key])}", inline=False)

    await message.channel.send(embed=embed)


""" Get specific match info """
async def get_match_details(message, match):
    r = requests.get(RIOT_API_URL + f"/lol/match/v4/matches/{match['gameId']}", headers=RIOT_BASE_HDR)

    if r.status_code != 200:
        await message.channel.send("Failed to fetch data, please try again later")
        return None

    return r.json()


""" 
    Display player deaths
    TODO: Make this ASYNC it is veeeery slow right now
"""
async def deaths(message):
    # Get summoner match list
    summoner = await get_summoner_by_name(message, message.content[8:])
    if summoner == None:
        return

    encrypted_account_id = summoner["accountId"]

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    matches_played_per_queue = await get_player_match_history(message, encrypted_account_id, week_start, week_end)
    if matches_played_per_queue == None:
        return

    # Go through match list and count deaths
    deaths_per_queue = {}
    total_games = 0
    total_deaths = 0

    for key in matches_played_per_queue:
        total_games += len(matches_played_per_queue[key])

        for match in matches_played_per_queue[key]:
            game_data = await get_match_details(message, match)

            if game_data == None:
                return None

            # Get participant ID
            participant_id = -1
            for participant in game_data["participantIdentities"]:
                if participant["player"]["accountId"] == encrypted_account_id:
                    participant_id = participant["participantId"]
                    break
                
                # Sometimes players are on the wrong server and have a differend accountId
                if participant["player"]["summonerName"] == summoner["name"]:
                    participant_id = participant["participantId"]
                    break
            
            # Find participant in game and count deaths
            for participant in game_data["participants"]:
                if participant["participantId"] == participant_id:
                    deaths_per_queue.setdefault(key, 0)
                    deaths_per_queue[key] += participant["stats"]["deaths"]
                    total_deaths += participant["stats"]["deaths"]

    embed = discord.Embed(
        title = "Deaths in games this week",
        colour = discord.Colour.red()
    )

    for key in matches_played_per_queue.keys():
        embed.add_field(name=f"Deaths in {RIOT_QUEUES_DATA[key]['description']}:", value=f"{deaths_per_queue[key]}", inline=False)

    embed.set_footer(text=f"Average deaths per game: {round(total_deaths / total_games, 2)}")

    await message.channel.send(embed=embed)

    
""" Print the help message """
async def help_cmd(message):
    embed = discord.Embed(
            title = "Help Menu",
            colour = discord.Colour.green()
        )
    
    embed.add_field(name="Match history", value="""```!matches <summoner name>```""", inline=False)
    embed.add_field(name="Deaths", value="""```!deaths <summoner name>```""", inline=False)
    embed.add_field(name="Calculate avg deaths -WIP", value="""```diff\n- !avgdeaths <summoner name>```""", inline=False)
    embed.add_field(name="Randomize teams -WIP", value="""```diff\n- !teams <voice channel 1> <voice vhannel 2>```""", inline=False)

    await message.channel.send(embed=embed)


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
        await help_cmd(message)

    elif "!matches" in message.content:
        await matches(message)
    
    elif "!deaths" in message.content:
        await deaths(message)

    elif "!avgdeaths" in message.content:
        await avg_deaths(message)

    else:
        # Catch-all
        await help_cmd(message)

@client.event
async def on_message(message):
    if str(message.guild) == DISCORD_GUILD:
        if len(message.content) > 0 and message.content[0] == "!" and not message.author.bot:
            await is_command(message)


client.run(DISCORD_TOKEN)
