# pyright: reportMissingImports=false
import datetime
import discord
import time
import random
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import process_effects
from everythingexcepthim import (
    megaload,
    megasave,
    UnequipPageCode,
    is_debtor_blocked,
    send_split_embeds,
)
from THECORE import (PAGE_PATH, PROFILE_PATH, INV_PATH, SHOP_PATH, symbol, lock_command, ProfileMan)

def _normalize_deck(deck, data):
    if isinstance(deck, list):
        normed = {}
        for page in deck:
            normed[page] = {
                "cost": data["pages"][page]["light_cost"],
                "amount": normed.get(page, {}).get("amount", 0) + 1,
            }
        return normed
    elif isinstance(deck, dict):
        normed = {}
        for page, meta in deck.items():
            normed[page] = {
                "cost": meta.get("cost", data["pages"][page]["light_cost"]),
                "amount": meta.get("amount", 0),
            }
        return normed
    return {}

def _deck_to_list(deck):
    result = []
    for page, meta in deck.items():
        result.extend([page] * meta.get("amount", 0))
    return result

class PresetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loadpreset")
    @app_commands.describe(owner="Your profile name", preset="Name of the preset to load")
    @lock_command
    async def loadpreset(self, interaction: discord.Interaction, owner: str, preset: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.all_profiles()
        inventory = data["inventory"]
        presets = data["presets"]

        if owner not in inventory or owner not in profiles:
            await interaction.followup.send("❌ That profile doesn't exist.")
            return

        if preset not in presets:
            await interaction.followup.send("❌ That preset doesn't exist.")
            return

        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        allowed_freebies = ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"]
        preset_deck_list = presets[preset]["pages"]

        success = []
        failed = []
        equipped = list(inventory[owner]["equipped"])
        removed = []

        current_deck = profiles[owner].deck
        current_deck = _normalize_deck(current_deck, data)
        for page in equipped + allowed_freebies:
            tagorsomething = page not in current_deck
            successful, msg = UnequipPageCode(owner, page, data)
            if successful and (page not in allowed_freebies and tagorsomething):
                removed.append(page)

        pages_owned = inventory[owner]["pages"]
        equipped = inventory[owner]["equipped"]
        deck = {}

        for page in preset_deck_list:
            total_cards = sum(meta.get("amount", 0) for meta in deck.values())
            if total_cards >= 9:
                failed.append(f"{page} (deck full)")
                continue

            if page in allowed_freebies or page in pages_owned:
                if page not in allowed_freebies:
                    pages_owned.remove(page)
                    equipped.append(page)
                entry = deck.setdefault(page, {"cost": data["pages"][page]["light_cost"], "amount": 0})
                entry["amount"] += 1
                success.append(page)
            else:
                failed.append(page)

        profiles[owner].deck = deck

        embed = discord.Embed(
            title=f"{owner} tried to load the preset: {preset}",
            description="✅ Unequipped:\n" + (", ".join(removed) if removed else "None")
            + "\n\n✅ Equipped:\n" + (", ".join(success) if success else "None")
            + "\n\n❌ Failed:\n" + (", ".join(failed) if failed else "None"),
            color=discord.Color.blurple(),
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="savepreset")
    @app_commands.describe(owner="deck holder", name="Preset Name")
    @lock_command
    async def savepreset(self, interaction: discord.Interaction, owner: str, name: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.all_profiles()
        inventory = data["inventory"]
        presets = data["presets"]

        if owner not in inventory or owner not in profiles:
            await interaction.followup.send("❌ That profile doesn't exist.")
            return

        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        original_name = name
        i = 2
        while name in presets:
            name = f"{original_name} {i}"
            i += 1

        deck = profiles[owner].deck
        deck = _normalize_deck(deck, data)
        presets[name] = {
            "pages": _deck_to_list(deck),
            "creator": inventory[owner]["owner_id"],
        }

        embed = discord.Embed(
            title=f"{owner} has saved their deck as '{name}'!",
            description=f"{name}: {', '.join(_deck_to_list(deck))}",
            color=discord.Color.red(),
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="viewpresets")
    async def viewpresets(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        presets = data["presets"]

        if not presets:
            await interaction.followup.send("❌ No presets exist.")
            return

        fields = []
        embed = discord.Embed(
            title="📜 All Saved Deck Presets",
            description=" ",
            color=discord.Color.gold(),
        )

        for name, pdata in presets.items():
            deck_list = pdata.get("pages", [])
            deck_str = ", ".join(deck_list) if deck_list else "Empty"
            if len(deck_str) > 1024:
                deck_str = deck_str[:1021] + "..."
            fields.append((f"📦 {name}", deck_str, False))

        await send_split_embeds(interaction, embed, fields)

    @app_commands.command(name="overwritepreset")
    @app_commands.describe(owner="Profile to grab current deck from", preset="Name of the preset to overwrite")
    @lock_command
    async def overwritepreset(self, interaction: discord.Interaction, owner: str, preset: str):
        data = megaload()
        await interaction.response.defer()
        # profiles = data["profiles"]
        profiles = ProfileMan.get_profile(owner)
        inventory = data["inventory"]
        presets = data["presets"]

        if owner not in inventory or profiles is None:
            await interaction.followup.send("❌ That profile doesn't exist.")
            return

        if preset not in presets:
            await interaction.followup.send("❌ That preset doesn't exist.")
            return

        is_admin = interaction.user.guild_permissions.administrator
        is_creator = presets[preset].get("creator") == interaction.user.id
        if not is_creator and not is_admin:
            await interaction.followup.send("❌ You didn't make this preset.")
            return

        deck = _normalize_deck(profiles.deck, data)
        presets[preset] = {
            "pages": _deck_to_list(deck),
            "creator": inventory[owner]["owner_id"],
        }

        embed = discord.Embed(
            title=f"{owner} has overwritten the preset: '{preset}'",
            description=f"📝 New Deck:\n{', '.join(_deck_to_list(deck)) if deck else 'Empty'}",
            color=discord.Color.orange(),
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="deletepreset")
    @app_commands.describe(preset="Name of the preset to delete")
    @lock_command
    async def deletepreset(self, interaction: discord.Interaction, preset: str):
        data = megaload()
        await interaction.response.defer()
        presets = data["presets"]

        if preset not in presets:
            await interaction.followup.send("❌ That preset doesn't exist.")
            return

        is_admin = interaction.user.guild_permissions.administrator
        is_creator = presets[preset].get("creator") == interaction.user.id
        if not is_creator and not is_admin:
            await interaction.followup.send("❌ You didn't make this preset.")
            return

        del presets[preset]

        embed = discord.Embed(
            title=f"{interaction.user.display_name} has deleted the preset: '{preset}'",
            description="",
            color=discord.Color.orange(),
        )
        megasave(data)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    cog = PresetCog(bot)
    await bot.add_cog(cog)
