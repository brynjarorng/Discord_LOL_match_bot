import json
import random
import discord

async def parse_command(message):
    if "!aram" in message.content:
        await aram_picker(message)


def pick_champ(champion_list, champion_list_length):
    index = random.randrange(0, champion_list_length)
    champion1 = champion_list[index]
    champion_list.remove(champion_list[index])

    index = random.randrange(0, champion_list_length-1)
    champion2 = champion_list[index]
    champion_list.remove(champion_list[index])



    return (champion1, champion2)


async def aram_picker(message):
    with open("./data/champions.json") as f:
        data = json.load(f)
        
    champion_list = list(data['data'])
    champion_list_length = len(champion_list)

    message_content = message.content.split(" ")

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
        team_1_formatted += "{:10s} {:10s}\n".format(i[0], i[1])
        #team_1_formatted += i[0] + " - " + i[1] + "\n"
    team_1_formatted += "```"

    team_2_formatted = "```yaml\n"
    for i in team_2_champions:
        team_2_formatted += "{:10s} {:10s}\n".format(i[0], i[1])
        #team_2_formatted += i[0] + " - " + i[1] + "\n"
    team_2_formatted += "```"


    embed.add_field(name="Team 1", value=team_1_formatted, inline=False)
    embed.add_field(name="Team 2", value=team_2_formatted, inline=False)


    await message.channel.send(embed=embed)






# embed = discord.Embed(
#             title = "ARAM picker",
#             colour = discord.Colour.green()
#         )

# embed.add_field(name="ARAM champion randomizer", value="""```!aram <num team 1> <num team 2>```""", inline=False)
