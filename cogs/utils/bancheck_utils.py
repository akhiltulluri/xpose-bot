import discord
from discord.ext import commands
from dateutil.parser import parse
import config
from . import emoji


class BanCheckUtility:
    def __init__(self, bot):
        self.bot = bot

    async def get_clan_member_tags(self, clantag):
        clantag = clantag[1:]
        clan_members = await (
            await self.bot.session.get(
                self.bot.cmembers_endpoint + f"{clantag}/members"
            )
        ).json()
        if "error" in clan_members:
            if clan_members["error"] == "Not Found":
                raise commands.BadArgument(
                    f"{clantag} doesn't look like a valid clan tag."
                )
            else:
                return []
        player_tags = [x["tag"] for x in clan_members]
        return player_tags

    async def is_clan_banned(self, clantag, league):
        """A coroutine to check if a clan is banned"""
        if league == "wcl":
            clan_ban_list = self.bot.clan_ban_list_wcl
        elif league == "cwl":
            clan_ban_list = self.bot.clan_ban_list_cwl
        elif league == "mlcw":
            clan_ban_list = self.bot.clan_ban_list_mlcw
        if league == "cwl":
            banned_clans = [x for x in clan_ban_list["values"] if len(x) > 0]
            banned_clan_tags = [z[0] for z in banned_clans if len(z) > 0]
        else:
            banned_clans = [x for x in clan_ban_list["values"] if len(x) > 1]
            banned_clan_tags = [y[1] for y in banned_clans if len(y) > 1]
        if not clantag in banned_clan_tags:
            return [], []
        ind = banned_clan_tags.index(clantag)
        return self.match_length(banned_clans[0], banned_clans[ind])

    async def get_player_clan_history_tags(self, playertag):
        """A coroutine to get player clan history"""
        playertag = playertag[1:]
        player_clan_history = await (
            await self.bot.session.get(
                f"{self.bot.chistory_endpoint}{playertag}/history/clans"
            )
        ).json()
        if "error" in player_clan_history:
            if player_clan_history["error"] == "Not Found":
                raise commands.BadArgument(
                    f"{playertag} doesn't look like a valid player tag."
                )
            else:
                return []
        player_past_clan_tags = list(player_clan_history["clansMap"].keys())
        return player_past_clan_tags

    async def get_history_data(self, playertag, clantag):
        """A coroutine to get complete history of a player in a clan"""
        playertag = playertag[1:]
        player_clan_history = await (
            await self.bot.session.get(
                f"{self.bot.chistory_endpoint}{playertag}/history/clans"
            )
        ).json()
        logs = player_clan_history["log"]
        required = []
        for log in logs:
            if "tag" in log:
                tag = log["tag"]
                if tag == clantag:
                    required.append(log)
        return required

    async def get_clan_name(self, clantag):
        clantag = clantag[1:]
        resp = await (
            await self.bot.session.get(self.bot.cmembers_endpoint + clantag)
        ).json()
        if "error" in resp:
            if resp["error"] == "Not Found":
                raise commands.BadArgument(
                    f"{clantag} doesn't look like a valid clan tag."
                )
            else:
                return ""
        return resp["name"]

    async def get_player_name(self, playertag):
        playertag = playertag[1:]
        resp = await (
            await self.bot.session.get(self.bot.chistory_endpoint + playertag)
        ).json()
        if "error" in resp:
            if resp["error"] == "Not Found":
                raise commands.BadArgument(
                    f"{playertag} doesn't look like a valid player tag."
                )
            else:
                return ""
        return resp["name"]

    async def playerscan(self, playertag, league, clantag=None):
        playername = await self.get_player_name(playertag)
        keys, vals = await self.is_player_banned(playertag, league)
        past_clans = await self.get_player_clan_history_tags(playertag)
        visited_banned_clans = []
        embeds = []
        for tag in past_clans:
            if tag == clantag:
                continue
            clan_keys, clan_values = await self.is_clan_banned(tag, league)
            if clan_keys:
                visited_banned_clans.append([clan_keys, clan_values, tag])
        if not vals and visited_banned_clans is None:
            emb = discord.Embed(
                title="Ban Check",
                description=f"Player {playername}[{playertag}] is not banned by {league.upper()} {emoji.Checkmark} and found no banned clan in player clan history!",
                colour=discord.Colour.green(),
            )
            return emb, embeds
        for clan in visited_banned_clans:
            int_keys = clan[0]
            int_vals = clan[1]
            clan_tag = clan[2]
            clan_name = await self.get_clan_name(clan_tag)
            js = await self.get_history_data(playertag, clan_tag)
            explain_visited = []
            for log in js:
                if not "role" in log:
                    log["role"] = "member"
                if log["role"] == "admin":
                    log["role"] = "coLeader"
                if "date" in log:
                    inner_li = [
                        log["type"],
                        log["tag"],
                        log["role"],
                        log["date"],
                        log["duration"],
                    ]
                else:
                    inner_li = [
                        log["type"],
                        log["tag"],
                        log["role"],
                        log["start"],
                        log["end"],
                        log["duration"],
                    ]
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
                current_player_history_explanation = (
                    current_player_history_explanation
                    + f"**Role:** {explanation[2].capitalize()} "
                )
                if (end - start).days > 0:
                    current_player_history_explanation = (
                        current_player_history_explanation
                        + f"**Between:** {start_dt} and {end_dt} ({(end - start).days})\n"
                    )
                else:
                    current_player_history_explanation = (
                        current_player_history_explanation + f"**On:** {start_dt}\n"
                    )
            description = f"**Visited Banned Clan**: {clan_name}\n\nClan {clan_name} got banned by {league.upper()}.\n\nDetails from their ban list:\n"
            for i in range(len(int_keys)):
                txt = f"**{int_keys[i]}**: {int_vals[i]}\n"
                description = description + txt
            description = (
                description
                + f"\n\n**Info From Clash Of Stats:**\n\n{current_player_history_explanation}"
            )
            embed = discord.Embed(
                colour=config.embed_color, title=f"{clan_name}", description=description
            )
            embed.set_author(name="Player Clan History")
            embeds.append(embed)
        if not vals:
            if embeds:
                desc = f"Player {playername}[{playertag}] is not banned by {league.upper()} {emoji.Caution}. Go through the next message to check the banned clans member has been in."
                embed = discord.Embed(
                    colour=discord.Colour.gold(), title="Ban Check", description=desc
                )
                return embed, embeds
            emb = discord.Embed(
                color=discord.Colour.green(),
                title="Ban Check",
                description=f"Player {playername}[{playertag}] is not banned by {league.upper()} {emoji.Checkmark} and didn't visit any banned clans previously!",
            )
            return emb, []
        desc = f"Found a Ban Record! {emoji.Exclamation}\n\n"
        for i in range(len(keys)):
            txt = f"**{keys[i]}**: {vals[i]}\n"
            desc = desc + txt
        embed = discord.Embed(
            title="Ban Check", colour=discord.Colour.red(), description=desc
        )
        if embeds:
            desc = (
                desc
                + f"\nPlayer {playername}[{playertag}] has also visited clans banned by {league.upper()}. Go through the follow up message to know more about it."
            )
            embed = discord.Embed(
                title="Ban Check", colour=discord.Colour.red(), description=desc
            )
            return embed, embeds
        return embed, []

    @staticmethod
    def match_length(list1, list2):
        length1 = len(list1)
        length2 = len(list2)
        diff = length1 - length2
        for _ in range(diff):
            list2.append("None")
        return list1, list2

    async def clanscan(self, clantag, league):
        keys, vals = await self.is_clan_banned(clantag, league)
        clanname = await self.get_clan_name(clantag)
        if not vals:
            return discord.Embed(
                title=clanname,
                color=discord.Colour.green(),
                description=f"Clan {clanname}[{clantag}] is not banned by {league.upper()} {emoji.Checkmark}",
            )
        desc = f"Clan {clanname} got banned by {league.upper()} {emoji.Exclamation}.\n\nInfo from ban list:\n\n"
        for i in range(len(keys)):
            txt = f"**{keys[i]}**: {vals[i]}\n"
            desc = desc + txt
        embed = discord.Embed(
            colour=discord.Colour.red(), title=clanname, description=desc
        )
        return embed

    async def is_player_banned(self, playertag, league):
        """A coroutine to check if a player is banned"""
        if league == "wcl":
            player_ban_list = self.bot.player_ban_list_wcl
        elif league == "mlcw":
            player_ban_list = self.bot.player_ban_list_mlcw
        elif league == "cwl":
            player_ban_list = self.bot.player_ban_list_cwl
        if league == "cwl":
            banned_players = [x for x in player_ban_list["values"] if len(x) > 0]
            banned_player_tags = [z[0] for z in banned_players if len(z) > 0]
        else:
            banned_players = [x for x in player_ban_list["values"] if len(x) > 1]
            banned_player_tags = [y[1] for y in banned_players if len(y) > 1]
        if not playertag in banned_player_tags:
            return [], []
        ind = banned_player_tags.index(playertag)
        return self.match_length(banned_players[0], banned_players[ind])
