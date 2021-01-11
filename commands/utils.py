import random
import discord

async def print_help(message):
    embed = discord.Embed(
                title = "Help menu",
                colour = discord.Colour.red()
            )

    embed.add_field(name="ARAM champion randomizer", value="""```!aram <players in team 1> <players in team 2>```""", inline=False)
    embed.add_field(name="Deaths -WIP", value="""```diff\n !deaths <summoner name>```""", inline=False)
    embed.add_field(name="Calculate ranked winrate -WIP", value="""```!winrate <player 1> <player 2>```""", inline=False)

    await message.channel.send(embed=embed)

