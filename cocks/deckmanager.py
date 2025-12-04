# pyright: reportMissingImports=false
import datetime
import discord
import time
import random
from functools import partial
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import process_effects
from everythingexcepthim import (megaload , megasave , autocomplete_page_names, UnequipPageCode, is_debtor_blocked, UnequipPassiveCode)
from THECORE import (PAGE_PATH ,PROFILE_PATH, INV_PATH, SHOP_PATH,symbol,lock_command, ProfileMan)
class DeckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def autocomplete_inventory_items(self, interaction: discord.Interaction, current: str, item_key: str):
        # Grab the profile argument if user has filled it in
        profile_name = getattr(interaction.namespace, "owner", None)
        if not profile_name:
            return []  # nothing to suggest if profile isn't selected yet

        current = current.lower().strip()  # remove extra spaces
        data = megaload()
        pages = list(set(data["inventory"][profile_name][item_key]))
        pages.sort(reverse=False)
        print(pages)

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in pages
            if current in page_name.lower()
        ]

        return suggestions[:25]  # Discord limits to 25 choices

    async def autocomplete_playerProfile_items(self, interaction: discord.Interaction, current: str):
        # Grab the profile argument if user has filled it in
        profile_name = getattr(interaction.namespace, "owner", None)
        if not profile_name:
            return []  # nothing to suggest if profile isn't selected yet

        current = current.lower().strip()  # remove extra spaces
        profiles = list(set(ProfileMan.get_all_player_profiles().keys()))
        profiles.sort(reverse=False)
        print(profiles)

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in profiles
            if current in page_name.lower()
        ]

        return suggestions[:25]  # Discord limits to 25 choices

    async def autocomplete_OwnedPage_names(self, interaction, current):
        return await self.autocomplete_inventory_items(interaction, current, "pages")

    async def autocomplete_EquippedPage_names(self, interaction, current):
        return await self.autocomplete_inventory_items(interaction, current, "equipped")

    async def autocomplete_OwnedPassive_names(self, interaction, current):
        return await self.autocomplete_inventory_items(interaction, current, "passives")

    async def autocomplete_EquippedPassive_names(self, interaction, current):
        return await self.autocomplete_inventory_items(interaction, current, "equippedpas")

    @app_commands.command(name="equip")
    @app_commands.describe(owner="name",page="Page to equip")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items,
        page=autocomplete_OwnedPage_names
    )
    @lock_command
    async def equip(self, interaction: discord.Interaction, owner: str, page: str):
        data = megaload()
        await interaction.response.defer()
        profile = ProfileMan.get_profile(owner)
        pages = data["pages"]
        inventory = data["inventory"]

        actualPageDict = pages[page]
        if "requiresTag" in actualPageDict:
            print(f"this page requires the tag {actualPageDict['requiresTag']} yo")
            if actualPageDict["requiresTag"] != inventory[owner]["tag"]:
                await interaction.followup.send(f"❌ That page requires a specific tag you don't have equipped.")
                return

        if page not in pages:
            await interaction.followup.send(f"❌ That page doesn't exist.")
            return
        if owner not in inventory or profile is None:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return
        if page not in inventory[owner]["pages"] and page not in ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"]:
            await interaction.followup.send(f"❌ The profile does not own the page.")
            return

        # deck size check
        total_cards = sum(card["amount"] for card in profile.deck.values())
        page_amount = len([p for p in inventory[owner]["equipped"] if p == page]) + 1

        print(page_amount)
        if page_amount > 3:
            await interaction.followup.send(f"❌ You cannot equip more than 3 copies of {page}")
            return

        if total_cards >= 9:
            await interaction.followup.send("❌ The profile's deck is maxed out.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        if page not in ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"]:
            inventory[owner]["pages"].remove(page)
            inventory[owner]["equipped"].append(page)

        profile.add_page(page, pages)
        embed = discord.Embed(
            title=f"{owner} has equipped {page}!",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="give")
    @app_commands.describe(owner="giver", page="Page to give", given="who to give to")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items,
        page=autocomplete_OwnedPage_names
    )
    @lock_command
    async def give(self, interaction: discord.Interaction, owner: str, page: str, given: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.all_profiles()
        pages = data["pages"]
        inventory = data["inventory"]
        if page not in pages:
            await interaction.followup.send(f"❌ That page doesn't exist.")
            return
        if owner not in inventory or owner not in profiles:
            await interaction.followup.send(f"❌ That giver doesn't exist.")
            return
        if given not in inventory or given not in profiles:
            await interaction.followup.send(f"❌ That profile you send to doesn't exist.")
            return
        if page not in inventory[owner]["pages"] or page in ["Focused Strikes", "Charge and Cover", "Light Attack",
                                                             "Light Defense", "Evade"]:
            await interaction.followup.send(f"❌ The profile does not own the page.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        inventory[owner]["pages"].remove(page)
        inventory[given]["pages"].append(page)
        embed = discord.Embed(
            title=(
                    f"{owner} has given {page} to {given}!" +
                    (
                        " wow, how incredibly incredible, just such a useful, amazing incredible deal, wonderful truly." if owner == given else "")
            ),
            description=" ",
            color=discord.Color.green()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unequip")
    @app_commands.describe(owner="name",page="Page to unequip")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items,
        page=autocomplete_EquippedPage_names
    )
    @lock_command
    async def unequip(self, interaction: discord.Interaction, owner: str, page: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        if interaction.user.id != inventory.get(owner, {}).get("owner_id") and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        success, msg = UnequipPageCode(owner, page, data)
        if not success:
            await interaction.followup.send(msg)
            return

        embed = discord.Embed(
            title=msg,
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="changetag")
    @app_commands.describe(owner="name",tag="Tag to equip")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items
    )
    @lock_command
    async def changetag(self, interaction: discord.Interaction, owner: str, tag: str):
        data = megaload()
        await interaction.response.defer()
        profile = ProfileMan.get_profile(owner)
        inventory = data["inventory"][owner]
        current_tag = inventory.get("tag", "Mainstream Office")
        print(current_tag)

        for page in inventory["equipped"]:
            actualPage = data["pages"][page]
            if actualPage.get("requiresTag", False):
                await interaction.followup.send("❌ One of your equipped pages requires a tag. Unequip page first before changing tag.")
                return

        for passive in inventory["equippedpas"]:
            actualPassive = data["passives"][passive]
            if actualPassive.get("requiresTag", False):
                await interaction.followup.send("❌ One of your equipped passive requires a tag. Unequip passive first before changing tag.")
                return


        if current_tag in profile.faction:
            profile.faction.remove(current_tag)
        inventory["tag"] = tag
        profile.faction.append(tag)

        embed = discord.Embed(
            title=f"{owner} has equipped the {tag} tag and removed their {current_tag} tag!",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="deckreset")
    @app_commands.describe(owner="name")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items
    )
    @lock_command
    async def deckreset(self, interaction: discord.Interaction, owner: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.all_profiles()
        inventory = data["inventory"]
        if interaction.user.id != inventory.get(owner, {}).get("owner_id") and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        equipped = list(inventory[owner]["equipped"])
        removed = []

        for page in equipped + ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"]:
            tagorsomething = page not in profiles[owner].hand
            success, msg = UnequipPageCode(owner, page, data)
            if success and (page not in ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"] and tagorsomething):
                removed.append(page)
        megasave(data)
        profiles[owner].deck = {}

        if removed:
            await interaction.followup.send(
                f"✅ Unequipped {len(removed)} pages from {owner}: {', '.join(removed)}"
            )
        else:
            await interaction.followup.send("❌ Nothing to unequip.")

    @app_commands.command(name="passiveequip")
    @app_commands.describe(owner="name",passive="passive to equip")
    @app_commands.autocomplete(
        owner=autocomplete_playerProfile_items,
        passive=autocomplete_OwnedPassive_names
    )
    @lock_command
    async def passiveequip(self, interaction: discord.Interaction, owner: str, passive: str):
        data = megaload()
        await interaction.response.defer()
        profile = ProfileMan.get_profile(owner)
        passives = data["passives"]
        inventory = data["inventory"]

        if passive not in passives:
            await interaction.followup.send(f"❌ That passive doesn't exist.")
            return

        actualPassiveDict = passives[passive]
        if "requiresTag" in actualPassiveDict:
            print(f"this page requires the tag {actualPassiveDict['requiresTag']} yo")
            if actualPassiveDict["requiresTag"] != inventory[owner]["tag"]:
                await interaction.followup.send(f"❌ That page requires a specific tag you don't have equipped.")
                return

        if owner not in inventory or owner is None:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return
        if passive not in inventory[owner]["passives"]:
            await interaction.followup.send(f"❌ The profile does not own the passive.")
            return
        if (inventory[owner]["currentpascost"] + passives[passive].get("cost", 10)) > profile.maxpascost:
            await interaction.followup.send(f"❌ Too Expensive to Slot In")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        inventory[owner]["passives"].remove(passive)
        inventory[owner]["equippedpas"].append(passive)
        inventory[owner]["currentpascost"] += passives[passive].get("cost", 10)
        profile.passives.append(passive)

        embed = discord.Embed(
            title=f"{owner} has equipped {passive}!",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)


    @app_commands.command(name="passiveunequip")
    @app_commands.describe(owner="name",passive="passive to unequip")
    @app_commands.autocomplete(
        passive=autocomplete_EquippedPassive_names
    )
    @lock_command
    async def passiveunequip(self, interaction: discord.Interaction, owner: str, passive: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        if interaction.user.id != inventory.get(owner, {}).get("owner_id") and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        success, msg = UnequipPassiveCode(owner, passive, data)
        if not success:
            await interaction.followup.send(msg)
            return

        embed = discord.Embed(
            title=msg,
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="linkprofile")
    @app_commands.describe(profile_name="Your profile name")
    @lock_command
    async def linkprofile(self, interaction: discord.Interaction, profile_name: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]

        if profile_name not in inventory:
            await interaction.followup.send("❌ That profile doesn't exist.")
            return

        profile = inventory[profile_name]

        if "owner_id" in profile and profile["owner_id"] != interaction.user.id:
            await interaction.followup.send("❌ This profile is already linked to another user.")
            return

        profile["owner_id"] = interaction.user.id
        megasave(data)

        await interaction.followup.send(f"✅ Profile **{profile_name}** has been linked to you!")

    @app_commands.command(name="unlinkprofile")
    @app_commands.describe(profile_name="Profile to unlink")
    @commands.has_permissions(administrator=True)
    @lock_command
    async def unlinkprofile(self, interaction: discord.Interaction, profile_name: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]

        if profile_name not in inventory:
            await interaction.followup.send("❌ That profile doesn't exist.")
            return

        inventory[profile_name].pop("owner_id", None)
        megasave(data)

        await interaction.followup.send(f"✅ Unlinked **{profile_name}** from its owner.")


async def setup(bot):
    cog = DeckCog(bot)
    await bot.add_cog(cog)
