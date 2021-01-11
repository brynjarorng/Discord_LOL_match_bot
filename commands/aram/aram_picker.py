import json
import random
import discord

def pick_champ(champion_list, champion_list_length):
    index = random.randrange(0, champion_list_length)
    champion1 = champion_list[index]
    champion_list.remove(champion_list[index])

    index = random.randrange(0, champion_list_length-1)
    champion2 = champion_list[index]
    champion_list.remove(champion_list[index])



    return (champion1, champion2)


def get_json_data(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except:
        print("Failed to get data, file missing?")
        data = None

    return data



async def parse_message(message):
    """
    content : Discord.py message object
        The content of the message is on the form "!aram <a> <b>" where "a" and "b" are two integers from 1-5 (inclusive)
    """
    content = message.content.split(" ")

    # Validate message
    try:
        a = int(content[1])
        b = int(content[2])

        if a < 1 or a > 5:
            raise Exception
        if b < 1 or b > 5:
            raise Exception
    except:
        # TODO: General method to send error messages to client
        await message.channel.send("Incorrect message format")

        raise Exception("Incorrect message format")

    
    return content



async def aram_picker(message):
    data = get_json_data("./data/champions.json")
        
    champion_list = list(data['data'])
    champion_list_length = len(champion_list)

    # Parse message
    message_content = await parse_message(message)

    team_1_champions = []
    team_2_champions = []

    team_1_picked = 0
    team_1_players = int(message_content[1])
    team_2_picked = 0
    team_2_players = int(message_content[2])

    for i in range(max(team_1_players, team_2_players) * 2):
        # Team 1
        if team_1_picked < team_1_players:
            team_1_champions.append(pick_champ(champion_list, champion_list_length))
            team_1_picked += 1
            champion_list_length -= 2

        # Team 2
        if team_2_picked < team_2_players:
            team_2_champions.append(pick_champ(champion_list, champion_list_length))
            team_2_picked += 1
            champion_list_length -= 2

    embed = discord.Embed(
                title = "ARAM picker",
                colour = discord.Colour.green()
            )


    team_1_formatted = "```HTTP\n"
    for i in team_1_champions:
        team_1_formatted += "{:13s} {:13s}\n".format(i[0], i[1])
    team_1_formatted += "```"

    team_2_formatted = "```yaml\n"
    for i in team_2_champions:
        team_2_formatted += "{:13s} {:13s}\n".format(i[0], i[1])
    team_2_formatted += "```"


    embed.add_field(name="Team 1", value=team_1_formatted, inline=False)
    embed.add_field(name="Team 2", value=team_2_formatted, inline=False)


    await message.channel.send(embed=embed)
