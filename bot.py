import discord
from dotenv import load_dotenv
import os
import requests
import urllib.parse
from datetime import timedelta, datetime
import json
import time


class Bot:
    # load env
    load_dotenv()

    def __init__(self):
        self.RIOT_TOKEN = os.getenv("RIOT_TOKEN")
        self.RIOT_API_URL = "https://eun1.api.riotgames.com"
        self.RIOT_BASE_HDR = {"X-Riot-Token": self.RIOT_TOKEN}
        self.RIOT_QUEUES_FILE_PATH = "queues.json"
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
        client = discord.Client()
        
        @client.event
        async def on_ready():
            print(f"{client.user} has connected")

            await client.change_presence(status=discord.Status.online, activity=discord.Game("Listening to !"))

            for g in client.guilds:
                if g.name == self.DISCORD_GUILD:
                    print(f"{client.guilds}")
                    break

            # load data
            await self.load_queues()


        async def is_command(message):
            if "!help" in message.content:
                await self.help_cmd(message)

            elif "!matches" in message.content:
                await self.matches(message)
            
            elif "!deaths" in message.content:
                await self.deaths(message)

            else:
                # Catch-all
                await self.help_cmd(message)

        @client.event
        async def on_message(message):
            if str(message.guild) == self.DISCORD_GUILD:
                if len(message.content) > 0 and message.content[0] == "!" and not message.author.bot:
                    await is_command(message)

        client.run(self.DISCORD_TOKEN)

    """Basic getter, follows the rate limit"""
    async def get_data(self, query, header, channel, error, param = {}):
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
            await channel.send(embed=embed)

            time.sleep(long_cd_remaining)
            self.RIOT_API_REQ_LONG_CURR_REQ = 0
        else:
            self.RIOT_API_REQ_LONG_CURR_REQ += 1

            # need to check if rate limit needs to be set again
            if long_cd_remaining > self.RIOT_API_SHORT_COOLDOWN:
                self.RIOT_API_SHORT_TIMESTAMP = time.time()

        print(time.time() - self.RIOT_API_LONG_TIMESTAMP)
        r = requests.get(query, headers=header, params=param)
        
        if r.status_code != 200:
            await channel.send(error)
            return None
            
        return r.json()


    # load all queue types into a dict
    async def load_queues(self):
        with open(self.RIOT_QUEUES_FILE_PATH) as json_file:
            queues = json.load(json_file)
            for item in queues:
                self.RIOT_QUEUES_DATA[item["queueId"]] = {"map": item["map"], "description": item["description"]}


    async def get_summoner_by_name(self, message, user):
        summoner_name = urllib.parse.quote(user)
        return await self.get_data(self.RIOT_API_URL + f"/lol/summoner/v4/summoners/by-name/{summoner_name}", self.RIOT_BASE_HDR, message.channel, "Error, user not found!") 


    async def get_player_match_history(self, message, encrypted_account_id, week_start, week_end):
        # create request object
        params = {"beginTime": str(int(week_start.timestamp()) * 1000), "endTime": str(int(week_end.timestamp())* 1000)}

        data = await self.get_data(self.RIOT_API_URL + f"/lol/match/v4/matchlists/by-account/{encrypted_account_id}", self.RIOT_BASE_HDR, message.channel, "You have not played any matches this week!", params)
        
        if data == None:
            return None

        matches_obj = data['matches']
        matches_played_per_queue = {}

        for item in matches_obj:
            matches_played_per_queue.setdefault(item["queue"], []).append(item) 
        
        return matches_played_per_queue


    """ Display number of matches played of a specific player """
    async def matches(self, message):
        # Return this weeks match info of the user
        # Need to check out ways to parse strings better

        # Start by getting summoner id
        summoner = await self.get_summoner_by_name(message, message.content[9:])
        if summoner == None:
            return
        
        encrypted_account_id = summoner["accountId"]

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        matches_played_per_queue = await self.get_player_match_history(message, encrypted_account_id, week_start, week_end)
        if matches_played_per_queue == None:
            return

        embed = discord.Embed(
            title = "Match history",
            colour = discord.Colour.red()
        )

        for key in matches_played_per_queue.keys():
            embed.add_field(name=self.RIOT_QUEUES_DATA[key]["description"], value=f"{len(matches_played_per_queue[key])}", inline=False)

        await message.channel.send(embed=embed)


    """ Get specific match info """
    async def get_match_details(self, message, match):
        data = await self.get_data(self.RIOT_API_URL + f"/lol/match/v4/matches/{match['gameId']}", self.RIOT_BASE_HDR, message.channel, "Failed to fetch data, please try again later")
        # r = requests.get(self.RIOT_API_URL + f"/lol/match/v4/matches/{match['gameId']}", headers=self.RIOT_BASE_HDR)

        # if r.status_code != 200:
        #     await message.channel.send("Failed to fetch data, please try again later")
        #     return None

        return data


    """ 
        Display player deaths
        TODO: Make this ASYNC it is veeeery slow right now
    """
    async def deaths(self, message):
        # Get summoner match list
        summoner = await self.get_summoner_by_name(message, message.content[8:])
        if summoner == None:
            return

        encrypted_account_id = summoner["accountId"]

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        matches_played_per_queue = await self.get_player_match_history(message, encrypted_account_id, week_start, week_end)
        if matches_played_per_queue == None:
            return

        # Go through match list and count deaths
        deaths_per_queue = {}
        total_games = 0
        total_deaths = 0

        for key in matches_played_per_queue:
            total_games += len(matches_played_per_queue[key])

            for match in matches_played_per_queue[key]:
                game_data = await self.get_match_details(message, match)

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
            embed.add_field(name=f"Deaths in {self.RIOT_QUEUES_DATA[key]['description']}:", value=f"{deaths_per_queue[key]}", inline=False)

        embed.set_footer(text=f"Average deaths per game: {round(total_deaths / total_games, 2)}")

        await message.channel.send(embed=embed)

        
    """ Print the help message """
    async def help_cmd(self, message):
        embed = discord.Embed(
                title = "Help Menu",
                colour = discord.Colour.green()
            )
        
        embed.add_field(name="Match history", value="""```!matches <summoner name>```""", inline=False)
        embed.add_field(name="Deaths", value="""```!deaths <summoner name>```""", inline=False)
        embed.add_field(name="Randomize teams -WIP", value="""```diff\n- !teams <voice channel 1> <voice vhannel 2>```""", inline=False)

        await message.channel.send(embed=embed)


if __name__ == "__main__":
    bot = Bot()
