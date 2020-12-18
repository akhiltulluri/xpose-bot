import os
import discord

token = os.environ.get("TOKEN", "")

postgres = os.environ.get("DATABASE_URL", "")

bot_description = "XPOSE Bot"

owner = 313943421188308992

prefixes = ["xp "]

extensions = ["cogs.general","cogs.debug","jishaku","cogs.bancheck"]

activity = discord.Activity(type=discord.ActivityType.listening,name="xp help")

name = "   XPOSE   "

embed_color = discord.Colour.blue() 
sheets_api_key = os.environ.get("SHEETS_API_KEY","")
log_channel = 714382330839695410 
logo = "https://media.discordapp.net/attachments/511385199612002304/714411204210327592/Xpose_Bot.png" 
admins = [313943421188308992, 531548281793150987,355820732489531395]
dev_mode = False
