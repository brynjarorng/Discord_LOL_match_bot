import random
import discord

from commands.aram.aram_picker import aram_picker

async def parse_command(message):
    try:
        if "!aram" in message.content:
            return await aram_picker(message)
        
        await print_help(message)
    except Exception as e:
        print(e)


async def print_help(message):
    embed = discord.Embed(
                title = "Help menu",
                colour = discord.Colour.red()
            )

    embed.add_field(name="ARAM champion randomizer", value="""```!aram <players in team 1> <players in team 2>```""", inline=False)
    await message.channel.send(embed=embed)

