import discord
from discord.ext import commands, tasks
import config
import sys, traceback
from .utils.paginator import CannotPaginate, TextPages
from .utils.logging import getLogger

logger = getLogger(__name__)


class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initialize.start()

    @tasks.loop(count=1)
    async def initialize(self):
        await self.bot.wait_until_ready()
        self.log_channel = self.bot.get_channel(config.log_channel)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Debugs when a guild is joined by the bot!"""

        title = "Joined a new server"
        description = f"""{guild.name} [{guild.id}]
Members: {len(guild.members)}
Owner: {guild.owner} [{guild.owner.id}]"""
        embed = discord.Embed(
            title=title, description=description, color=discord.Color.green()
        )
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Debugs when a guild is left by the bot!"""

        title = "Left a server"
        description = f"{guild.name} [{guild.id}]"
        embed = discord.Embed(
            title=title, description=description, color=discord.Color.red()
        )
        await self.log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("That command doesn't exist.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.errors.TooManyArguments):
            await ctx.send(error)
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f"Not enough arguments supplied.")
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.errors.BadArgument):
            await ctx.send(error)
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.errors.NotOwner):
            await ctx.send("This command is Bot Owner only")
        elif isinstance(error, commands.errors.MissingPermissions):
            await ctx.author.send(
                "You don't have enough permissions to use this command!"
            )
        elif isinstance(error, commands.errors.BadUnionArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.NotFound):
                await ctx.send(f"This entity does not exist: {original.text}")
            elif isinstance(original, discord.errors.Forbidden):
                await ctx.send("I don't have enough permissions to do that!")
            elif isinstance(original, discord.HTTPException):
                await ctx.send(
                    "Somehow, an unexpected error occurred. Try again later."
                )
            elif isinstance(original, CannotPaginate):
                await ctx.send(error)
            else:
                log = "".join(
                    traceback.format_exception(
                        type(original), original, original.__traceback__
                    )
                )
                try:
                    invite = await ctx.channel.create_invite(max_uses=1)
                    invite = invite.url
                except:
                    invite = "Couldn't create an invite"
                embed = discord.Embed(
                    title="An error occured", color=discord.Color.red()
                )
                field = f"""Command: `{ctx.message.content}`
Author: {ctx.author}[{ctx.author.id}]
Server: {ctx.guild.name}[{ctx.guild.id}]
Server Invite: {invite}"""
                logger.error(log)
                embed.add_field(name="Error", value=field)
                await self.log_channel.send(embed=embed)
                await ctx.send(
                    "An unexpected error occured! Error report has been sent to Devs"
                )


def setup(bot):
    bot.add_cog(Debug(bot))
