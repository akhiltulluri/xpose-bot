import discord
from discord.ext import commands,tasks

from dateutil.parser import parse
import json

import config
from .utils.paginator import EmbedPages

class BanCheckUtility:
    def __init__(self,bot):
        self.bot = bot
    
    async def get_clan_member_tags(self,clantag):
        clantag = clantag[1:]
        clan_members = await (await self.bot.session.get(self.bot.cmembers_endpoint+f"{clantag}/members")).json()
        if 'error' in clan_members:
            return []
        player_tags = [x['tag'] for x in clan_members]
        return player_tags

    async def is_clan_banned(self,clantag,league):
        """A coroutine to check if a clan is banned"""
        if league == 'wcl':
            clan_ban_list = self.bot.clan_ban_list_wcl
        elif league == 'cwl':
            clan_ban_list = self.bot.clan_ban_list_cwl
        elif league == 'mlcw':
            clan_ban_list = self.bot.clan_ban_list_mlcw
        banned_clans = [x for x in clan_ban_list['values']]
        if league == 'cwl':
            banned_clan_tags = [z[0] for z in banned_clans if len(z) >0]
        else:
            banned_clan_tags = [y[1] for y in banned_clans if len(y) > 1]
        if not clantag in banned_clan_tags:
            return [],[]
        ind = banned_clan_tags.index(clantag)
        return self.match_length(banned_clans[0],banned_clans[ind])

    async def get_player_clan_history_tags(self,playertag):
        """A coroutine to get player clan history"""
        playertag = playertag[1:]
        player_clan_history = await (await self.bot.session.get(f"{self.bot.chistory_endpoint}{playertag}/history/clans")).json()
        if 'error' in player_clan_history:
            return []
        player_past_clan_tags = list(player_clan_history['clansMap'].keys())
        return player_past_clan_tags

    async def get_history_data(self,playertag,clantag):
        """A coroutine to get complete history of a player in a clan"""
        playertag = playertag[1:]
        player_clan_history = await (await self.bot.session.get(f"{self.bot.chistory_endpoint}{playertag}/history/clans")).json()
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
        resp = await (await self.bot.session.get(self.bot.cmembers_endpoint+clantag)).json()
        return resp['name']

    async def get_player_name(self,playertag):
        playertag = playertag[1:]
        resp = await (await self.bot.session.get(self.bot.chistory_endpoint+playertag)).json()
        return resp['name']

    async def playerscan(self,playertag,league):
        playername = await self.get_player_name(playertag)
        keys,vals = await self.is_player_banned(playertag,league)
        past_clans = await self.get_player_clan_history_tags(playertag)
        visited_banned_clans = []
        embeds = []
        for tag in past_clans:
            clan_keys,clan_values = await self.is_clan_banned(tag,league)
            if clan_keys:
                visited_banned_clans.append([clan_keys,clan_values,tag])
        if not vals and visited_banned_clans is None:
            emb = discord.Embed(title="Ban Check",description=f"Player {playername}[{playertag}] is not banned by {league.upper()} and found no banned clan in player clan history!",colour=config.embed_color)
            return emb,embeds      
        for clan in visited_banned_clans:
            int_keys = clan[0]
            int_vals = clan[1]
            clan_tag = clan[2]
            clan_name = await self.get_clan_name(clan_tag)
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
            current_player_history_explanation = f"Player {playername} visited the clan {clan_name} in the following intervals:\n"
            i = 0
            for explanation in explain_visited:
                i += 1
                if i > 5:
                    break
                if len(explanation) == 5:
                    start = end = parse(explanation[3])
                    start_dt = end_dt = f"{start.day}/{start.month}/{start.year}"
                else:                    
                    start = parse(explanation[3])
                    end = parse(explanation[4])
                    start_dt = f"{start.day}/{start.month}/{start.year}"
                    end_dt = f"{end.day}/{end.month}/{end.year}"                                   
                current_player_history_explanation = current_player_history_explanation + f"**Role:** {explanation[2]} **Between:** {start_dt} and {end_dt}"
                if end.day - start.day > 0:
                    current_player_history_explanation = current_player_history_explanation + f" ({end.day - start.day})\n"
                else:
                    current_player_history_explanation = current_player_history_explanation + "\n"
            description = f"Clan {clan_name} got **banned** by {league.upper()}.\n\n Details from their ban list:\n"
            for i in range(len(int_keys)):
                txt = f"**{int_keys[i]}**: {int_vals[i]}\n"
                description = description + txt
            description = description + f"\n\n**Info From Clash Of Stats:**\n\n{current_player_history_explanation}"
            embed = discord.Embed(colour=config.embed_color,title=f"{clan_name}-{playername}",description=description)
            embeds.append(embed)
        if not vals:
            if embeds:
                desc = f"Player {playername}[{playertag}] is not banned by {league.upper()}. Go through the next message to check the banned clans member has been in."
                embed = discord.Embed(colour=config.embed_color,title='Ban Check',description=desc)            
                return embed,embeds
            emb = discord.Embed(color=config.embed_color,title='Ban Check',description=f"Player {playername}[{playertag}] is not banned by {league.upper()} and didn't visit any banned clans previously!")
            return emb,[]               
        desc = f"Found a Ban Record!\n\n"
        for i in range(len(keys)):
            txt = f"**{keys[i]}**: {vals[i]}\n"
            desc = desc + txt
        embed = discord.Embed(title="Ban Check",colour=config.embed_color,description=desc)
        if embeds:
            desc = desc + f"\nPlayer {playername}[{playertag}] has also visited clans banned by {league.upper()}. Go through the follow up message to know more about it."
            embed = discord.Embed(title="Ban Check",colour=config.embed_color,description=desc)
            return embed,embeds
        return embed,[] 
        
    @staticmethod
    def match_length(list1,list2):
        length1 = len(list1)
        length2 = len(list2)
        diff = length1 - length2
        for _ in range(diff):
            list2.append('None')
        return list1,list2

    async def clanscan(self,clantag,league):
        keys,vals = await self.is_clan_banned(clantag,league)
        clanname = await self.get_clan_name(clantag)
        if not vals:
            return discord.Embed(title=clanname,color=config.embed_color,description=f"Clan {clanname}[{clantag}] is not banned by {league.upper()}")
        desc = f"Clan {clanname} got banned by {league.upper()}.\n\n Info from ban list:\n\n"
        for i in range(len(keys)):
            txt = f"**{keys[i]}**: {vals[i]}\n"
            desc = desc + txt
        embed = discord.Embed(colour=config.embed_color,title=clanname,description=desc)
        return embed


    async def is_player_banned(self,playertag,league):
        """A coroutine to check if a player is banned"""
        if league == 'wcl':
            player_ban_list = self.bot.player_ban_list_wcl
        elif league == 'mlcw':
            player_ban_list = self.bot.player_ban_list_mlcw
        elif league == 'cwl':
            player_ban_list = self.bot.player_ban_list_cwl
        banned_players = [x for x in player_ban_list['values'] if len(x) > 1]
        banned_player_tags = [y[1] for y in banned_players if len(y) > 1]
        if league == 'cwl':
            banned_players = [x for x in player_ban_list['values'] if len(x) > 0]
            print("this happened")
            banned_player_tags = [z[0] for z in banned_players if len(z) > 0]
            print(banned_player_tags[614])
        
        if not playertag in banned_player_tags:
            return [],[]
        ind = banned_player_tags.index(playertag)
        print(ind)
        return self.match_length(banned_players[0],banned_players[ind])      
            

class BanCheck(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.name = 'WCL BanCheck'
        self.position = 1
        self.bot.cbanlist_endpoint_wcl = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/B5:G?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.pbanlist_endpoint_wcl = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/Banned%20Players!B5:H?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.cbanlist_endpoint_cwl = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/banlist2!A1:C?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.pbanlist_endpoint_cwl = 'https://sheets.googleapis.com/v4/spreadsheets/1qckELKFEYecbyGeDqRqItjSKm02ADpKfhkK1FiRbQ-c/values/banlist1!Y1:AA?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.cbanlist_endpoint_mlcw = 'https://sheets.googleapis.com/v4/spreadsheets/1QWEN1i5nDmfeHzpnQLpJDIMU9vUv2c_NT43PN9csF2Q/values/A3:D?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.pbanlist_endpoint_mlcw = 'https://sheets.googleapis.com/v4/spreadsheets/1QWEN1i5nDmfeHzpnQLpJDIMU9vUv2c_NT43PN9csF2Q/values/Banned%20Players!A3:E?key=AIzaSyBs-oGIB9K9HenlLvL54lWurKyD9GokfAU'
        self.bot.chistory_endpoint = 'https://api.clashofstats.com/players/' 
        self.bot.cmembers_endpoint = 'https://api.clashofstats.com/clans/'  
        self.init.start()
        self.inst = BanCheckUtility(bot)      
    
            
    @tasks.loop(minutes=5)
    async def init(self):
        self.bot.clan_ban_list_wcl = await (await self.bot.session.get(self.bot.cbanlist_endpoint_wcl)).json()
        self.bot.player_ban_list_wcl = await (await self.bot.session.get(self.bot.pbanlist_endpoint_wcl)).json()
        self.bot.clan_ban_list_mlcw = await (await self.bot.session.get(self.bot.cbanlist_endpoint_mlcw)).json()
        self.bot.player_ban_list_mlcw = await (await self.bot.session.get(self.bot.pbanlist_endpoint_mlcw)).json()
        self.bot.clan_ban_list_cwl = await (await self.bot.session.get(self.bot.cbanlist_endpoint_cwl)).json()
        self.bot.player_ban_list_cwl = await (await self.bot.session.get(self.bot.pbanlist_endpoint_cwl)).json()

    @init.before_loop
    async def before_init(self):
        await self.bot.wait_until_ready()   
    
    
    @commands.command()
    async def wclcc(self,ctx,clantag):
        embed = await self.inst.clanscan(clantag,'wcl')
        await ctx.send(embed=embed)


    @commands.command()
    async def wclps(self,ctx,playertag):
        embed,embed_list = await self.inst.playerscan(playertag,"wcl")
        await ctx.send(embed=embed)
        for em in embed_list:
            await ctx.send(embed=em)


    @commands.command()
    async def wclcs(self,ctx,clantag):
        await ctx.invoke(self.wclcc,clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)}")
        for player in player_tags:
            await ctx.invoke(self.wclps,playertag=player)
        await ctx.send('Completed!')

class MLCWCheck(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.inst = BanCheckUtility(bot)
        self.name = "MLCW Ban Check"
        self.position = 2

    @commands.command()
    async def mlcwcc(self,ctx,clantag):
        embed = await self.inst.clanscan(clantag,'mlcw')
        await ctx.send(embed=embed)

    @commands.command()
    async def mlcwps(self,ctx,playertag):
        embed,embed_list = await self.inst.playerscan(playertag,"mlcw")
        await ctx.send(embed=embed)
        for em in embed_list:
            await ctx.send(embed=em)


    @commands.command()
    async def mlcwcs(self,ctx,clantag):
        await ctx.invoke(self.mlcwcc,clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)}")
        for player in player_tags:
            await ctx.invoke(self.mlcwps,playertag=player)
        await ctx.send('Completed!')

class CWLCheck(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.inst = BanCheckUtility(bot)
        self.name = "CWL Ban Check"
        self.position = 3

    @commands.command()
    async def cwlcc(self,ctx,clantag):
        embed = await self.inst.clanscan(clantag,'cwl')
        await ctx.send(embed=embed)

    @commands.command()
    async def cwlps(self,ctx,playertag):
        embed,embed_list = await self.inst.playerscan(playertag,"cwl")
        await ctx.send(embed=embed)
        for em in embed_list:
            await ctx.send(embed=em)


    @commands.command()
    async def cwlcs(self,ctx,clantag):
        await ctx.invoke(self.cwlcc,clantag=clantag)
        player_tags = await self.inst.get_clan_member_tags(clantag)
        await ctx.send(f"Processing..... {len(player_tags)}")
        for player in player_tags:
            await ctx.invoke(self.cwlps,playertag=player)
        await ctx.send('Completed!')
    
    
def setup(bot):
    bot.add_cog(BanCheck(bot))
    bot.add_cog(MLCWCheck(bot))
    bot.add_cog(CWLCheck(bot))