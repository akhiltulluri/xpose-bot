import discord
from discord.ext import commands

from dateutil.parser import parse

import config
from .utils.paginator import EmbedPages

class BanCheck(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.session = bot.session
        self.cbanlist_endpoint = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/B6:G?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.pbanlist_endpoint = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/Banned%20Players!B6:H?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.chistory_endpoint = 'https://api.clashofstats.com/players/' 
        self.cmembers_endpoint = 'https://api.clashofstats.com/clans/'
        self._task = self.bot.loop.create_task(self.initialize())


    async def initialize(self):
        self.clan_ban_list = await (await self.session.get(self.cbanlist_endpoint)).json()
        self.player_ban_list = await (await self.session.get(self.pbanlist_endpoint)).json()


    async def get_clan_member_tags(self,clantag):
        clantag = clantag[1:]
        clan_members = await (await self.session.get(self.cmembers_endpoint+f"{clantag}/members")).json()
        if 'error' in clan_members:
            return []
        player_tags = [x['tag'] for x in clan_members]
        return player_tags

    async def is_clan_banned(self,clantag):
        """A coroutine to check if a clan is banned"""
        clan_ban_list = self.clan_ban_list
        banned_clans = [x for x in clan_ban_list['values']]
        banned_clan_tags = [y[1] for y in banned_clans]
        if not clantag in banned_clan_tags:
            return False
        ind = banned_clan_tags.index(clantag)
        return banned_clans[ind]

    async def get_player_clan_history_tags(self,playertag):
        """A coroutine to get player clan history"""
        playertag = playertag[1:]
        player_clan_history = await (await self.session.get(f"{self.chistory_endpoint}{playertag}/history/clans")).json()
        if 'error' in player_clan_history:
            return []
        player_past_clan_tags = list(player_clan_history['clansMap'].keys())
        return player_past_clan_tags

    async def get_history_data(self,playertag,clantag):
        """A coroutine to get complete history of a player in a clan"""
        playertag = playertag[1:]
        player_clan_history = await (await self.session.get(f"{self.chistory_endpoint}{playertag}/history/clans")).json()
        logs = player_clan_history['log']
        required = []
        for log in logs:
            if 'tag' in log:
                tag = log['tag']
                if tag == clantag:
                    required.append(log)
        return required

    async def get_clan_name(self,clantag):
        clantag = clantag[1:]
        resp = await (await self.session.get(self.cmembers_endpoint+clantag)).json()
        return resp['name']

    async def get_player_name(self,playertag):
        playertag = playertag[1:]
        resp = await (await self.session.get(self.chistory_endpoint+playertag)).json()
        return resp['name']


    async def is_player_banned(self,playertag):
        """A coroutine to check if a player is banned"""
        
        player_ban_list = self.player_ban_list
        banned_players = [x for x in player_ban_list['values']]
        banned_player_tags = [y[1] for y in banned_players]
        if not playertag in banned_player_tags:
            return False
        ind = banned_player_tags.index(playertag)
        return banned_players[ind]

    @commands.command()
    async def cc(self,ctx,clantag):
        val = await self.is_clan_banned(clantag)
        clanname = await self.get_clan_name(clantag)
        if not val:
            return await ctx.send(f"Clan {clanname}[{clantag}] is not banned by WCL")
        clan_name,clan_tag,ban_duration,date_added,ban_type,ban_reason = val
        embed = discord.Embed(colour=config.embed_color,title=clan_name,description=f"Clan {clan_name} got banned by WCL on {date_added}\nReason: {ban_reason}\nBan Type: {ban_type}\nDuration: {ban_duration}")
        await ctx.send(embed=embed)

    @commands.command()
    async def update(self,ctx):
        await self.initialize()
        await ctx.send(f"Successfully fetched latest ban list!")

    @commands.command()
    async def ps(self,ctx,playertag):
        playername = await self.get_player_name(playertag)
        val = await self.is_player_banned(playertag)
        past_clans = await self.get_player_clan_history_tags(playertag)
        visited_banned_clans = []
        for tag in past_clans:
            verify = await self.is_clan_banned(tag)
            if verify:
                visited_banned_clans.append(verify)
        if visited_banned_clans is None:
            return await ctx.send(f"Player {playername}[{playertag}] not Banned and found no banned clan in player clan history!")
        embeds = []
        for clan in visited_banned_clans:
            clan_name,clan_tag,ban_duration,date_added,ban_type,ban_reason = clan
            js = await self.get_history_data(playertag,clan_tag)
            explain_visited = []
            for log in js:
                if not 'role' in log:
                    log['role'] = 'member'
                if 'date' in log:
                    inner_li = [log['type'],log['tag'],log['role'],log['date'],log['duration']]
                else:
                    inner_li = [log['type'],log['tag'],log['role'],log['start'],log['end'],log['duration']]
                explain_visited.append(inner_li)
            current_player_history_explanation = ''
            for explanation in explain_visited:
                if len(explanation) == 5:
                    on = parse(explanation[3])
                    keyword = 'visited'
                    start_dt = end_dt = f"{on.day}/{on.month}/{on.year}"
                else:
                    keyword = 'stayed in'
                    start = parse(explanation[3])
                    end = parse(explanation[4])
                    start_dt = f"{start.day}/{start.month}/{start.year}"
                    end_dt = f"{end.day}/{end.month}/{end.year}"                    
                current_player_history_explanation = current_player_history_explanation + f"Player {playername}[{playertag}] has {keyword} {clan_name}[{explanation[1]}] with role {explanation[2]} between {start_dt} and {end_dt}\n"
            embed = discord.Embed(colour=config.embed_color,title=clan_name,description=f"Clan {clan_name} got banned by WCL on {date_added}\nReason: {ban_reason}\nBan Type: {ban_type}\nDuration: {ban_duration}\n\nInfo From Clash Of Stats:\n{current_player_history_explanation}")
            embeds.append(embed)
        if not val:
            if embeds:
                embed = discord.Embed(colour=config.embed_color,title='Ban Check',description=f"Player {playername}[{playertag}] is not banned directly by WCL but one or more of the clans visited by the player before got banned by WCL. Go through the follow up message to know more about it!")            
                await ctx.send(embed=embed)    
                p = EmbedPages(ctx,embeds=embeds) 
                return await p.paginate() 
            return await ctx.send(f"Player {playername}[{playertag}] is not banned by WCL and didn't visit any banned clans previously!")          
        player_name,player_id,owner,type,duration,date,reason = val
        desc = f"Found a Ban Record!\nPlayer Name:{player_name}\nPlayer ID:{player_id}\nDiscord Owner:{owner}\nBan Type:{type}\nDuration:{duration}\nDate Added:{date}\nReason:{reason}"
        embed = discord.Embed(title="Ban Check",colour=config.embed_color,description=desc)
        if embeds:
            desc = desc + f"\nPlayer {player_name}[{playertag}] has also visited clans banned by WCL. Go through the follow up message to know more about it."
            embed = discord.Embed(title="Ban Check",colour=config.embed_color,description=desc)
            await ctx.send(embed=embed)
            p = EmbedPages(ctx,embeds=embeds)
            return await p.paginate()
        await ctx.send(embed=embed)

    @commands.command()
    async def cs(self,ctx,clantag):
        await ctx.invoke(self.cc,clantag=clantag)
        player_tags = await self.get_clan_member_tags(clantag)
        for player in player_tags:
            await ctx.invoke(self.ps,playertag=player)
        await ctx.send('Completed!')

def setup(bot):
    bot.add_cog(BanCheck(bot))