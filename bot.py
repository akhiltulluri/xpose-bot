import discord
from discord.ext import commands

import sys,traceback
import aiohttp
import asyncio
from datetime import datetime
import logging
import os

import asyncpg

import config

from cogs.utils.formats import TabularData
from cogs.utils.db import Table

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename=f'bot.log',
                              encoding='utf-8',
                              mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
fmt = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(fmt)
logger.addHandler(handler)

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = [prefix for prefix in config.prefixes]
    if not message.guild:
        return '*'    
    return commands.when_mentioned_or(*prefixes)(bot, message)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, description=config.bot_description)
        self.owner_id = config.owner
        self._task = self.loop.create_task(self.initialize())
        self.loop.run_until_complete(self.create_db_pool())        
        self.activity = config.activity
        for extension in config.extensions:
            try:
                self.load_extension(extension)
            except:
                print(f'Failed to load extension {extension}.')
                traceback.print_exc()
                
    async def create_db_pool(self):
        '''Creates a postgresql database pool'''
        self.db = Table.create_pool(config.postgres,command_timeout=60)
   
    async def initialize(self):
        '''Initialize the bot with a aiohttp.ClientSession and defining the owner'''        
        self.session = aiohttp.ClientSession(loop=self.loop)
        await self.wait_until_ready()
        self.owner = self.get_user(self.owner_id)
        
    async def process_commands(self, message):
        ctx = await self.get_context(message)
        if ctx.command is None:
            return
        await self.invoke(ctx)
       
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def on_ready(self):
        self.start_time = datetime.utcnow()
        rows = (
            ('Name', self.user.name),
            ('Discord', discord.__version__),
            ('Guilds', len(self.guilds)),
            ('Users', len(self.users))
        )        

        table = TabularData()
        table.set_columns((config.name, '   Bot   '))
        table.add_rows(rows)
        print(table.render())
        print('Successfully logged in and booted...!')
        perms = discord.Permissions.none()
        perms.administrator = True
        self.invite_url = discord.utils.oauth_url(self.user.id, perms)
        print()
        print(f'Invite Me:\n{self.invite_url}')

    @property
    def uptime(self):
        '''Returns how long the bot has been up online'''
        now = datetime.utcnow()
        delta = now - self.start_time
        hours,remainder = divmod(int(delta.total_seconds()),3600)
        minutes,seconds = divmod(remainder,60)
        days,hours = divmod(hours,24)
        fmt = f"{hours}h {minutes}m {seconds}s"
        if days:
            fmt = f"{days}d {fmt}"
        return fmt                        

    async def close(self):
        await super().close()
        await self.session.close()
        self._task.cancel()

    def run(self):
        try:            
            super().run(config.token, bot=True, reconnect=True)
        except Exception as e:
            print(f'Troubles running the bot!\nError: {e}')
            # traceback.print_exc()

def main():
    bot = Bot()
    bot.run()


if __name__ == '__main__':
    main()