# pyright: reportMissingImports=false
import json
import discord
from collections import Counter
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import (megaload, autocomplete_profile_names,send_split_embeds)
from THECORE import (PASSIVE_PATH, INV_PATH, PROFILE_PATH, BUFF_PATH, symbol, ProfileMan )
from UnitProfileCode import ProfileData
class ChessCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="statcheck")
    @app_commands.autocomplete(
        name=autocomplete_profile_names
    )
    @app_commands.describe(name="Character name")
    async def statcheck(self,interaction: discord.Interaction, name: str):
        data = megaload()
        await interaction.response.defer()
        profile : ProfileData = ProfileMan.get_profile(name)

        def fmt(d): return json.dumps(d, indent=2) if isinstance(d, dict) else str(d)
        embed = discord.Embed(
            title=f"📜 Stats of {name}",
            color=discord.Color.green()
        )
        hp = (
            f"**HP**: {symbol['stagger']}{profile.current_hp}/{profile._max_hp} (CON: {profile.stats_dict["con"]})"
            if "hp" not in profile.hidden and "hp" not in profile.temphidden
            else "**HP**: ???/???"
        )

        stagger = (
            f"**Stagger**: {symbol['stagger']}{profile.current_stagger}/{profile.max_stagger} (STR: {profile.stats_dict["str"]})"
            if "stagger" not in profile.hidden and "stagger" not in profile.temphidden
            else "**Stagger**: ???/???"
        )
        light = (
            f"**Light**: {symbol['light']}{profile.current_light }/{profile._current_max_light} (INT: {profile.stats_dict["int"]})"
            if "light" not in profile.hidden and "light" not in profile.temphidden
            else "**Light**: ???/???"
        )

        speed = (
            f"**Speed**: {symbol['stagger']} {profile._current_min_speed}-{profile._current_max_speed} (DEX: {profile.stats_dict["dex"]})"
            if "speed" not in profile.hidden and "speed" not in profile.temphidden
            else "**Speed**: ???"
        )

        passives = (
            f"**Passives**: {symbol['buff']}{data["inventory"][name]["currentpascost"]}/{profile.maxpascost} (CHA: {profile.stats_dict["cha"]})"
            if "passive" not in profile.hidden and "passive" not in profile.temphidden
            else "**Passive**: ???"
        )

        level = (
            f"**Level**: {symbol['buff']}{profile.level}"
            if "level" not in profile.hidden and "level" not in profile.temphidden
            else "**Speed**: ???"
        )

        embed.add_field(
            name="🧍 Vital Stats",
            value=f"{hp}\n{stagger}\n{light}\n{speed}\n{passives}\n\n{level}",
            inline=False
        )


        await interaction.followup.send(embed=embed)

    
    @app_commands.command(name="deckcheck")
    @app_commands.autocomplete(
        name=autocomplete_profile_names
    )
    @app_commands.describe(name="Character name")
    async def deckcheck(self,interaction: discord.Interaction, name: str):
        data = megaload()
        await interaction.response.defer()
        buffsreal = data["buffs"]
        profile : ProfileData = ProfileMan.get_profile(name)

        def fmt(d): return json.dumps(d, indent=2) if isinstance(d, dict) else str(d)
        embed = discord.Embed(
            title=f"📜 Profile of {name}",
            color=discord.Color.green()
        )
        hp = (
            f"**HP**: {symbol['buff']}{profile.current_hp}/{profile._max_hp}"
            if "hp" not in profile.hidden and "hp" not in profile.temphidden
            else "**HP**: ???/???"
        )

        stagger = (
            f"**Stagger**: {symbol['stagger']}{profile.current_stagger}/{profile.max_stagger}"
            if "stagger" not in profile.hidden and "stagger" not in profile.temphidden
            else "**Stagger**: ???/???"
        )

        staggered = f"({symbol['stagger']} Staggered: {('Yes' if profile.is_staggered else 'No') if 'staggerstate' not in profile.hidden and 'staggerstate' not in profile.temphidden else '??'})"

        light = (
            f"**Light**: {symbol['light']}{profile.current_light }/{profile._current_max_light}"
            if "light" not in profile.hidden and "light" not in profile.temphidden
            else "**Light**: ???/???"
        )

        speed = (
            f"**Speed**: {symbol['buff']}{profile.current_speed} ({profile._current_min_speed}-{profile._current_max_speed})"
            if "speed" not in profile.hidden and "speed" not in profile.temphidden
            else "**Speed**: ???"
        )

        level = (
            f"**Level**: {symbol['buff']}{profile.level}"
            if "level" not in profile.hidden and "level" not in profile.temphidden
            else "**Speed**: ???"
        )

        embed.add_field(
            name="🧍 Vital Stats",
            value=f"{hp}\n{stagger} {staggered}\n{light}\n{speed}\n{level}",
            inline=False
        )


        buffs = profile.buffs
        buffs_fmt = ", ".join(
            [
                f"`{k} x{v.get('stack', 1)} stack{', x' + str(v.get('count')) + ' Count' if buffsreal[k].get('countable', False) else ''}`"
                for k, v in buffs.items()
            ]
        ) if buffs else "*None*"

        embed.add_field(
            name=f"{symbol['buff']} Buffs",
            value=buffs_fmt,
            inline=False
        )

        passives = profile.passives
        embed.add_field(
            name=f"{symbol['sanity']} Passives",
            value=", ".join(
                "`Hidden`" if data["passives"].get(p, {}).get("hidden", False) else f"`{p}`"
                for p in passives
            ) if passives else "*None*",
            inline=False
        )
        deck = ""
        hand = ""

        deck = "\n".join(f"{name}: x{page['amount']}" for name, page in profile.deck.items())

        hand = "\n".join(
            f"{name}: x{page['amount']}" 
            for name, page in profile.hand.items()
        )

        # for name, page in profile.deck.items():
        #     deck += f"{name}: x{page["amount"]}\n"
        # for name, page in profile.hand.items():
        #     hand += f"{name}: x{page["amount"]}\n"
        if not profile.deck:
            deck = "*None*"
        if not profile.hand:
            hand = "*None*"
        if "deck" in profile.hidden and "deck" in profile.temphidden:
            deck = "???"
            hand = "???"

        embed.add_field(
            name="📘 Deck / 🤲 Hand",
            value=(
                f"**Deck**: {deck}\n"
                f"**Hand**: {hand}"
            ),
            inline=False
        )


        await interaction.followup.send(embed=embed)

    @app_commands.command(name="inventorycheck")
    @app_commands.autocomplete(
        name=autocomplete_profile_names
    )
    @app_commands.describe(name="Character name")
    async def inventorycheck(self,interaction: discord.Interaction, name: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        profile = ProfileMan.get_profile(name)
        p_inv = inventory.get(name)

        if not profile:
            await interaction.followup.send("Profile not found.")
            return
        if not p_inv:
            await interaction.followup.send("Profile has no Inventory")
            return

        deck = profile.deck
        equipped = p_inv.get("equipped", [])
        pages = p_inv.get("pages", [])
        passives = profile.passives
        pasequipped = p_inv.get("equippedpas", [])
        passivesowned = p_inv.get("passives", [])
        ahn = p_inv.get("ahn", 0)
        lunacy = p_inv.get("lunacy", 0)
        cost = p_inv.get("currentpascost", 0)

        maxcost = profile.maxpascost

        embed = discord.Embed(
            title=f"🃏 Inventory Check: {name}",
            color=discord.Color.gold()
        )
        fields = []
        fields.append((
            f"{symbol['light']} Ahn {symbol['light']}",
            f"{name} has {ahn} Ahn",
            False
        ))
        fields.append((
            f"{symbol['light']} Lunacy {symbol['light']}",
            f"{name} has {lunacy} Lunacy",
            False
        )) 
        fields.append((
            f"{symbol['light']} Passive Cost {symbol['light']}",
            f"{symbol['light']} {cost}/{maxcost} Passive Cost {symbol['light']}",
            False
        ))

        if pages:
            sortedpages = sorted(pages)
            page_counts = Counter(sortedpages)  # count duplicates
            pages_display = "".join(f"`- {name} x{count}`\n" for name, count in page_counts.items())
        else:
            pages_display = "*Empty*"

        fields.append((
            "📥 Unequipped Pages",
            pages_display,
            False
        ))

        if profile.deck:
            deck = ""
            for name, page in profile.deck.items():
                deck += f"{name}: x{page['amount']}\n"
        else:
            deck = "???"
        if not profile.deck:
            deck = "*None*"
        if "deck" in profile.hidden or 'deck' in profile.temphidden:
            deck = "???"
        fields.append((
            "📦 Deck",
            deck,
            False
        ))
        fields.append((
            "📥 Unequipped Passives",
            ", ".join(f"`{card}`" for card in passivesowned) if passivesowned else "*Empty*",
            False
        ))
        fields.append((
            "📥 Equipped Passives",
            ", ".join(f"`{card}`" for card in pasequipped) if pasequipped else "*Empty*",
            False
        ))

        fields.append((
            "📦 Passives",
            ", ".join(f"`{card}`" for card in passives) if passives else "*Empty deck*",
            False
        ))

        await send_split_embeds(interaction,embed,fields)


    @app_commands.command(name="rescheck")
    @app_commands.autocomplete(
        name=autocomplete_profile_names
    )
    @app_commands.describe(name="Character name")
    async def rescheck(self,interaction: discord.Interaction, name: str):
        data = megaload()
        await interaction.response.defer()
        buffsreal = data["buffs"]
        profile = ProfileMan.get_profile(name)
        if not profile:
            await interaction.followup.send("Profile not found.")
            return
        def fmt(d): return json.dumps(d, indent=2) if isinstance(d, dict) else str(d)
        embed = discord.Embed(
            title=f"📜 Resistances of {name}",
            color=discord.Color.yellow()
        )

        general = (
            f"**General**: `{json.dumps(profile.resistances, indent=0)}`"
            if "res" not in profile.hidden and "res" not in profile.temphidden
            else "**General**: ???"
        )

        stagger = (
            f"**Stagger**: `{json.dumps(profile.stagger_resistances, indent=0)}`"
            if "staggerres" not in profile.hidden and "staggerres" not in profile.temphidden
            else "**Stagger**: ???"
        )

        sin = (
            f"**Sin**: `{json.dumps(profile.sin_resistances, indent=0)}`"
            if "sinres" not in profile.hidden and "sinres" not in profile.temphidden
            else "**Sin**: ???"
        )
        embed.add_field(
            name="🛡️ Resistances",
            value=f"{general}\n{stagger}\n{sin}",
            inline=False
        )

        factions = profile.faction
        faction_text = ", ".join(f"`{f}`" for f in factions) if factions else "*None*"
        embed.add_field(name="🎭 Factions", value=faction_text, inline=False)

        embed.set_footer(text=f"{'🟢 Active' if profile.is_active else '🔴 Inactive'}")

        await interaction.followup.send(embed=embed)

    
    @app_commands.command(name="passivecheck")
    @app_commands.autocomplete(
        name=autocomplete_profile_names
    )
    @app_commands.describe(name="Character name")
    async def passivecheck(self,interaction: discord.Interaction, name: str):
        data = megaload()
        await interaction.response.defer()
        passives = data["passives"]
        profile = ProfileMan.get_profile(name)

        if not profile:
            await interaction.followup.send("Profile not found.")
            return

        passive_list = profile.passives
        if not passive_list:
            await interaction.followup.send(f"{name} has no passives.")
            return

        embed = discord.Embed(
            title=f"{symbol['sanity']} Passive Check: {name} {symbol['sanity']}",
            description="Known passives and their effects.",
            color=discord.Color.blue()
        )

        for passive_name in passive_list:
            data = passives.get(passive_name, {})

            if not data.get("hidden", False):
                desc = data.get("description", "*No description provided.*")
            else:
                desc = "You can not view this passive Yet"

            if data.get("hidden", False):
                name = "Hidden"
            else:
                name = passive_name
            embed.add_field(
                name=f"📘 {name}",
                value=desc,
                inline=False
            )

        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="mdstats")
    async def mdstats(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()

        fields = []
        embed = discord.Embed(
            title="📜 MD Stats",
            description=" ",
            color=discord.Color.green()
        )
        embed.add_field(
                name=f"{symbol['light']} Cost",
                value=f"Cost: {data['MD']['currency']['cost']}",
                inline=False
            )
        for sin, amount in data["res"]["Player"].items():
            embed.add_field(
                name=f"🔥 {sin}",
                value=f"{sin}: {amount}",
                inline=False
            )

        await interaction.followup.send(embed=embed)
async def setup(bot):
    cog = ChessCog(bot)
    await bot.add_cog(cog)

