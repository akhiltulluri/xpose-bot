import discord
from discord.ext import commands, tasks
import json
import re

import config
from .utils.paginator import EmbedPages
from .utils import emoji
from .utils.bancheck_utils import BanCheckUtility

SPREADSHEET_REGEX = re.compile(
    r"(https?:\/\/)?(www\.)?docs.google\.com\/spreadsheets(\/u\/0)?\/d\/(?P<id>[a-zA-Z0-9_-]+)"
)


class BanCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = "WCL BanCheck"
        self.position = 1
        self.bot.cbanlist_endpoint_wcl = f"https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/B5:G?key={config.sheets_api_key}"
        self.bot.pbanlist_endpoint_wcl = f"https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/Banned%20Players!B5:H?key={config.sheets_api_key}"
        self.bot.cbanlist_endpoint_cwl = f"https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/banlist2!A1:C?key={config.sheets_api_key}"
        self.bot.pbanlist_endpoint_cwl = f"https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/banlist1!Y1:AA?key={config.sheets_api_key}"
        self.bot.cbanlist_endpoint_mlcw = f"https://sheets.googleapis.com/v4/spreadsheets/1QWEN1i5nDmfeHzpnQLpJDIMU9vUv2c_NT43PN9csF2Q/values/A3:D?key={config.sheets_api_key}"
        self.bot.pbanlist_endpoint_mlcw = f"https://sheets.googleapis.com/v4/spreadsheets/1QWEN1i5nDmfeHzpnQLpJDIMU9vUv2c_NT43PN9csF2Q/values/Banned%20Players!A3:E?key={config.sheets_api_key}"
        self.bot.chistory_endpoint = "https://api.clashofstats.com/players/"
        self.bot.cmembers_endpoint = "https://api.clashofstats.com/clans/"
        self.init.start()
        self.inst = BanCheckUtility(bot)

    @tasks.loop(minutes=5)
    async def init(self):
        self.bot.clan_ban_list_wcl = await (
            await self.bot.session.get(self.bot.cbanlist_endpoint_wcl)
        ).json()
        self.bot.player_ban_list_wcl = await (
            await self.bot.session.get(self.bot.pbanlist_endpoint_wcl)
        ).json()
        self.bot.clan_ban_list_mlcw = await (
            await self.bot.session.get(self.bot.cbanlist_endpoint_mlcw)
        ).json()
        self.bot.player_ban_list_mlcw = await (
            await self.bot.session.get(self.bot.pbanlist_endpoint_mlcw)
        ).json()
        self.bot.clan_ban_list_cwl = await (
            await self.bot.session.get(self.bot.cbanlist_endpoint_cwl)
        ).json()
        self.bot.player_ban_list_cwl = await (
            await self.bot.session.get(self.bot.pbanlist_endpoint_cwl)
        ).json()

    @init.before_loop
    async def before_init(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def wclcc(self, ctx, clantag):
        """Check if a clan is banned or not according to WCL Ban List"""
        embed = await self.inst.clanscan(clantag, "wcl")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)

    @commands.command()
    async def wclps(self, ctx, playertag):
        """Check if a player is banned or not according to WCL Ban list. Also gives information about player visits to clans banned by WCL"""
        embed, embed_list = await self.inst.playerscan(playertag, "wcl")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)
        for em in embed_list:
            # em.set_thumbnail(url=config.logo)
            em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=em)

    @commands.command()
    async def wclcs(self, ctx, clantag):
        """Run a complete clan scan. This command lets you know if a clan and it's clan members are banned or not according to WCL Ban list. Includes info about player visits to clans banned by WCL."""
        await ctx.invoke(self.wclcc, clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)} members")
        for player in player_tags:
            embed, embed_list = await self.inst.playerscan(player, "wcl", clantag)
            embed.set_thumbnail(url=config.logo)
            embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=embed)
            for em in embed_list:
                # em.set_thumbnail(url=config.logo)
                em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
                await ctx.send(embed=em)
        await ctx.send("Completed!")


class MLCWCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inst = BanCheckUtility(bot)
        self.name = "MLCW Ban Check"
        self.position = 2

    @commands.command()
    async def mlcwcc(self, ctx, clantag):
        """Check if a clan is banned or not according to MLCW Ban List"""
        embed = await self.inst.clanscan(clantag, "mlcw")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)

    @commands.command()
    async def mlcwps(self, ctx, playertag):
        """Check if a player is banned or not according to MLCW Ban list. Also gives information about player visits to clans banned by MLCW"""
        embed, embed_list = await self.inst.playerscan(playertag, "mlcw")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)
        for em in embed_list:
            # em.set_thumbnail(url=config.logo)
            em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=em)

    @commands.command()
    async def mlcwcs(self, ctx, clantag):
        """Run a complete clan scan. This command lets you know if a clan and it's clan members are banned or not according to MLCW Ban list. Includes info about player visits to clans banned by MLCW."""
        await ctx.invoke(self.mlcwcc, clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)} members")
        for player in player_tags:
            embed, embed_list = await self.inst.playerscan(player, "mlcw", clantag)
            embed.set_thumbnail(url=config.logo)
            embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=embed)
            for em in embed_list:
                # em.set_thumbnail(url=config.logo)
                em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
                await ctx.send(embed=em)

        await ctx.send("Completed!")


class CWLCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inst = BanCheckUtility(bot)
        self.name = "CWL Ban Check"
        self.position = 3

    @commands.command()
    async def cwlcc(self, ctx, clantag):
        """Check if a clan is banned or not according to CWL Ban List"""
        embed = await self.inst.clanscan(clantag, "cwl")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)

    @commands.command()
    async def cwlps(self, ctx, playertag):
        """Check if a player is banned or not according to CWL Ban list. Also gives information about player visits to clans banned by CWL"""
        embed, embed_list = await self.inst.playerscan(playertag, "cwl")
        embed.set_thumbnail(url=config.logo)
        embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
        await ctx.send(embed=embed)
        for em in embed_list:
            # em.set_thumbnail(url=config.logo)
            em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=em)

    @commands.command()
    async def cwlcs(self, ctx, clantag):
        """Run a complete clan scan. This command lets you know if a clan and it's clan members are banned or not according to CWL Ban list. Includes info about player visits to clans banned by CWL."""
        await ctx.invoke(self.cwlcc, clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)} members")
        for player in player_tags:
            embed, embed_list = await self.inst.playerscan(player, "cwl", clantag)
            embed.set_thumbnail(url=config.logo)
            embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=embed)
            for em in embed_list:
                # em.set_thumbnail(url=config.logo)
                em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
                await ctx.send(embed=em)

        await ctx.send("Completed!")


class Spreadsheet:
    @classmethod
    async def convert(cls, ctx, argument):
        match = SPREADSHEET_REGEX.search(argument)
        if match:
            sheet_id = match.groupdict()["id"]
            endpoint = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/E24:E?key={config.sheets_api_key}"
            return endpoint
        raise commands.BadArgument(f"{argument} doesn't look like a valid roster link.")


class RosterCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.position = 4
        self.name = "Roster BanCheck Commands"
        self.inst = BanCheckUtility(bot)

    @commands.command()
    async def wclrs(self, ctx, spreadsheetlink: Spreadsheet):
        """Fetches player tags from the roster spreadsheet url and scans the player. This is simliar to manually running `wclps` command on each playertag from the roster. This command works only for WCL league as of now"""
        data = (await (await self.bot.session.get(spreadsheetlink)).json())["values"]
        playertags = [x for x in data if len(x) > 0]
        await ctx.send(f"Processing... {len(playertags)} members")
        for playertag in playertags:
            embed, embed_list = await self.inst.playerscan(playertag[0], "wcl")
            embed.set_thumbnail(url=config.logo)
            embed.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
            await ctx.send(embed=embed)
            for em in embed_list:
                em.set_thumbnail(url=config.logo)
                em.set_footer(text="Designed by WCL Tech Team", icon_url=config.logo)
                await ctx.send(embed=em)
        await ctx.send("Completed!")


def setup(bot):
    bot.add_cog(BanCheck(bot))
    bot.add_cog(MLCWCheck(bot))
    bot.add_cog(CWLCheck(bot))
    bot.add_cog(RosterCheck(bot))
