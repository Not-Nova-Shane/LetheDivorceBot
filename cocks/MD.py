# pyright: reportMissingImports=false
import datetime
import discord
import time
import random
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import process_effects
from everythingexcepthim import (megaload , megasave, UnequipPageCode, is_debtor_blocked, send_split_embeds)
from THECORE import (PAGE_PATH ,PROFILE_PATH, INV_PATH, SHOP_PATH,symbol,lock_command, ProfileMan)
class MDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdsell")
    @app_commands.describe(gift="Gift to sell")
    @lock_command
    async def mdsell(self, interaction: discord.Interaction, gift: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        gifts = data["gifts"]

        if gift not in gifts or gifts[gift].get("hidden"):
            await interaction.followup.send(f"❌ That Gift doesn't exist.")
            return
        sellcost = (gifts[gift].get("cost",0) *.5) * (((gifts[gift].get("level",1) - 1) * 0.5) + 1)
        if not gifts[gift].get("acquired",False):
            await interaction.followup.send(f"❌ That Gift Isn't Acquired")
            return
        data["MD"]["currency"]["cost"] += sellcost
        gifts[gift]["acquired"] = False
        embed = discord.Embed(
            title=f"{gift} has been sold for {sellcost} Cost",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
   
    # @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdbuy")
    @app_commands.describe(gift="Gift to buy")
    @lock_command
    async def mdbuy(self, interaction: discord.Interaction, gift: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        gifts = data["gifts"]

        if gift not in gifts or gifts[gift].get("hidden"):
            await interaction.followup.send(f"❌ That Gift doesn't exist.")
            return
        theshop = data["MD"]["MDshop"]
        if gifts[gift].get("acquired",False):
            await interaction.followup.send(f"❌ That Gift is Already Acquired")
            return
        if gift not in theshop["currentlyselling"]:
            await interaction.followup.send(f"❌ That Gift is not being Sold.")
            return
        buycost = gifts[gift].get("cost",0)
        if buycost > data["MD"]["currency"]["cost"]:
            await interaction.followup.send(f"❌ Too Expensive.")
            return
        data["MD"]["currency"]["cost"] -= buycost
        gifts[gift]["acquired"] = True
        embed = discord.Embed(
            title=f"{gift} has been Bought for {buycost} Cost",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdbreak")
    @app_commands.describe(gift="Gift to break")
    @lock_command
    async def mdbreak(self, interaction: discord.Interaction, gift: str):
        data = megaload()
        await interaction.response.defer()
        gifts = data["gifts"]
        resources = data["res"]["Player"]
        if gift not in gifts or gifts[gift].get("hidden"):
            await interaction.followup.send(f"❌ That Gift doesn't exist.")
            return
        if not gifts[gift].get("acquired",False):
            await interaction.followup.send(f"❌ That Gift Isn't Acquired.")
            return
        if gifts[gift].get("hiderecipe",False):
            await interaction.followup.send(f"❌ You don't know that gift's recipe.")
            return
        if not gifts[gift].get("recipe"):
            await interaction.followup.send(f"❌ That gift can not be created or broken down due to lacking a recipe.")
            return
        resourcereturn = ""
        for resource, amount in gifts[gift]["recipe"].items():
            resources[resource] += amount//2
            resourcereturn += f"{resource} x{amount}\n"
        gifts[gift]["acquired"] = False
        embed = discord.Embed(
            title=f"{gift} has been Broken Down!",
            description=f"Returned:\n{resourcereturn}",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)


    async def autocomplete_EquippedPage_names(self, interaction: discord.Interaction, current: str):
        # Grab the profile argument if user has filled it in
        profile_name = getattr(interaction.namespace, "profile", None)
        if not profile_name:
            return []  # nothing to suggest if profile isn't selected yet

        # Load profile data
        profile = ProfileMan.get_profile(profile_name)
        if not profile:
            return []  # invalid profile name

        pages = getattr(profile, "hand", [])

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in pages
            if current in page_name.lower()
        ]

        return suggestions[:25]  # max 25 suggestions


    # @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdcreate")
    @app_commands.describe(gift="Gift to Create")
    @lock_command
    async def mdcreate(self, interaction: discord.Interaction, gift: str):
        data = megaload()
        await interaction.response.defer()
        gifts = data["gifts"]
        resources = data["res"]["Player"]
        if gift not in gifts or gifts[gift].get("hidden"):
            await interaction.followup.send(f"❌ That Gift doesn't exist.")
            return
        if gifts[gift].get("acquired",False):
            await interaction.followup.send(f"❌ That Gift is Already Acquired")
            return
        if gifts[gift].get("hiderecipe",False):
            await interaction.followup.send(f"❌ You don't know that gift's recipe.")
            return
        if not gifts[gift].get("recipe"):
            await interaction.followup.send(f"❌ That gift can not be created or broken down due to lacking a recipe.")
            return
        resourcereturn = ""
        for resource, amount in gifts[gift]["recipe"].items():
            if resources.get(resource, 0) < amount:
                await interaction.followup.send(f"❌ Not enough {resource} to create {gift}.")
                return
            resources[resource] -= amount
            resourcereturn += f"{resource} x{amount}\n"
        gifts[gift]["acquired"] = True
        embed = discord.Embed(
            title=f"{gift} has been Created!",
            description=f"Used:\n{resourcereturn}",
            color=discord.Color.green()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
   

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdrefresh")
    @lock_command
    async def mdrefresh(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        shop = data["MD"]["MDshop"]
        gifts = data["gifts"]
        logs = []
        shop["currentlyselling"] = []

        cansell = shop.get("cansell")
        cansell = [gift for gift in cansell if not data["gifts"][gift].get("acquired", False)]

        random.shuffle(cansell)
        selling = cansell[:shop["sellingamount"]]
        for page in selling:
            shop["currentlyselling"].append(page)
            logs.append(f"{page} is being sold at {data['gifts'][page].get('cost',0)} Cost!")


        embed = discord.Embed(
            title=f"The shop has been refreshed!",
            description=f"🕒 Refreshed <t:{int(time.time())}:R>",
            color=discord.Color.gold()
        )

        for section in logs:
            embed.add_field(
            name=f"{symbol['light']} New Shop Item: {symbol['light']}",
            value=section,
            inline=False
        )
        megasave(data)
        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdheal")
    @app_commands.describe(healed="name")
    @lock_command
    async def MDheal(self, interaction: discord.Interaction, healed: str):
        data = megaload()
        await interaction.response.defer()
        Md = data["MD"]
        if Md["currency"]["cost"] < 100:
            await interaction.followup.send("Broke Ass")
            return
        Md["currency"]["cost"] -= 100
        healed_profile = ProfileMan.get_profile(healed)
        healed_profile.heal_hp(healed_profile._max_hp * 0.75)
        healed_profile.heal_stagger(healed_profile.max_stagger * 0.75)
        healed_profile.current_hp = min(healed_profile._max_hp, healed_profile.current_hp)
        healed_profile.current_stagger = min(healed_profile.max_stagger, healed_profile.current_stagger)
        healed_profile.heal_light(99)
        embed = discord.Embed(
            title=f"{healed} has been healed for {healed_profile._max_hp * .75} HP and {healed_profile.max_stagger * .75} Stagger",
            description=" ",
            color=discord.Color.green()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdhealall")
    @lock_command
    async def MDhealall(self, interaction: discord.Interaction):
        data = megaload()
        profiles = ProfileMan.get_all_active_profiles()
        await interaction.response.defer()
        Md = data["MD"]
        if Md["currency"]["cost"] < 100:
            await interaction.followup.send("Broke Ass")
            return
        Md["currency"]["cost"] -= 100
        for name, profile in profiles.items():
            if profile.PlayerOrEnemy == "Enemy":
                continue
            profile.current_hp += (profile._max_hp * 0.35)
            profile.current_stagger += (profile.max_stagger * 0.35)
            profile.current_hp = min(profile._max_hp, profile.current_hp)
            profile.current_stagger = min(profile.max_stagger, profile.current_stagger)
        embed = discord.Embed(
            title=f"Everyone has been Healed for 35% of their Max Hp and Max Stagger",
            description=" ",
            color=discord.Color.green()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdrevive")
    @lock_command
    async def MDrevive(self, interaction: discord.Interaction, profile: str):
        data = megaload()
        await interaction.response.defer()
        profileTarget = ProfileMan.get_profile(profile)

        if profileTarget is not None:
            if data["MD"]["currency"]["cost"] < 100:
                await interaction.followup.send(f"Broke Ass", ephemeral=False)
                return
            data["MD"]["currency"]["cost"] -= 100
            profileTarget.current_hp = profileTarget.max_hp
            profileTarget.current_stagger = profileTarget.max_stagger
            profileTarget.current_light = profileTarget._current_max_light
            profileTarget.is_staggered = False
            profileTarget.staggeredThisTurn = False
            profileTarget.hand = {}
            for page, pagedata in profileTarget.deck.items():
                pagedata["cost"] = data["pages"][page]["light_cost"]
            profileTarget.nextturn = {"light": 0}
            profileTarget.buffs = {}
            profileTarget.resistances = profileTarget.original_resistances
            profileTarget.is_active = False
            profileTarget.effect_limits_perm = {}
            profileTarget.effect_limits = {}
            profileTarget.temphidden = []
            profileTarget.used = []
        else:
            await interaction.followup.send(f"{profile} doesn't exist", ephemeral=False)
            return
        megasave(data)
        await interaction.followup.send(f"{profile} has been Revived", ephemeral=False)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="convertcost")
    @lock_command
    async def ConvertCost(self,interaction: discord.Interaction, participants: str,tier: int):
        data = megaload()
        participantlist = [participant.strip() for participant in participants.split(",")]
        await interaction.response.defer()
        Md = data["MD"]
        cost = Md["currency"]["cost"]
        ahn = 100000 * (tier)
        lunacy = 250 * tier
        for participant in participantlist:
            data["inventory"][participant]["ahn"] += ahn
            data["inventory"][participant]["lunacy"] += lunacy
        data["MD"]["currency"]["cost"] = 0
        megasave(data)
        await interaction.followup.send(f"{cost} Cost has been Transformed into {ahn} Ahn in {participantlist} Inventory and Gained {lunacy} Lunacy", ephemeral=False)

        
    @app_commands.command(name="viewownedgifts")
    async def viewownedgifts(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        gifts = data["gifts"]
        owned_gifts = {}
        for gift, giftdata in gifts.items():
            if giftdata["acquired"] and not giftdata.get("hidden", False):
                owned_gifts[gift] = giftdata
        if not owned_gifts:
            await interaction.followup.send("❌ No owned gifts exist.")
            return
        fields = []
        embed = discord.Embed(
            title="📜 All Owned E.G.O. Gifts",
            description=" ",
            color=discord.Color.gold()
        )
        for name, data in owned_gifts.items():
            if data["1"].get("description"):
                tier_str = "EX" if data["tier"] >= 6 else str(data["tier"])
                cost_str = f"Cost: {data['cost']}"
                level_str = f"Level: {data['level']}"
                desc_str = data[str(data['level'])]["description"]
                gift_str = f"{desc_str}\nTier: {tier_str}\n{cost_str}\n{level_str}"
            else:
                gift_str = "Unknown"
            finalname = name
            if data['level'] > 1:
                finalname+="+"
            if data['level'] > 2:
                finalname+="++"
            if len(gift_str) > 1024:
                gift_str = gift_str[:1021] + "..."
            fields.append((f"📦 {finalname}", gift_str, False))
        await send_split_embeds(interaction, embed, fields)
    
        
    # @app_commands.command(name="viewallgifts")
    async def viewallgifts(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        gifts = data["gifts"]

        names_list = list(data["gifts"].keys())
        print(names_list)


        fields = []
        embed = discord.Embed(
            title="📜 All E.G.O. Gifts",
            description=" ",
            color=discord.Color.gold()
        )

        for name, data in gifts.items():
            if data.get("hidden") or data["tier"] == 0:
                continue
            tier_str = "EX" if data["tier"] >= 6 else str(data["tier"])
            cost_str = f"Cost: {data['cost']}" if "cost" in data else "Cost Unknown"
            level_str = f"Level: {data['level']}"
            description = data[str(data['level'])]["description"]
            gift_str = f"{description}\nTier: {tier_str}\n{cost_str}\n{level_str}"
            if data.get("hiderecipe"):
                recipe = "Recipe Hidden"
            elif data.get("recipe"):
                recipe_lines = [f"{resource} x{amount}" for resource, amount in data["recipe"].items()]
                recipe = "Recipe:\n" + "\n".join(recipe_lines)
            else:
                recipe = "No Recipe Found"
            gift_str += "\n" + recipe
            finalname = name
            if data['level'] > 1:
                finalname+="+"
            if data['level'] > 2:
                finalname+="++"
            if len(gift_str) > 1024:
                gift_str = gift_str[:1021] + "..."
            fields.append((f"📦 {finalname}", gift_str, False))
        await send_split_embeds(interaction, embed, fields)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="roulette")
    @lock_command
    async def roulette(self, interaction: discord.Interaction, profile: str, bet_type: str):
        
        RED_NUMS = {
            1,3,5,7,9,12,14,16,18,
            19,21,23,25,27,30,32,34,36
        }

        def spin_roulette():
            """Simulate a European roulette spin."""
            result = random.randint(0, 36)
            if result == 0:
                color = "green"
            elif result in RED_NUMS:
                color = "red"
            else:
                color = "black"
            return result, color

        def check_bet_win(result, color, bet):
            """Check if the bet wins given the result."""
            bet = bet.lower()

            # Even / Odd
            if bet == "even":
                return result != 0 and result % 2 == 0
            elif bet == "odd":
                return result % 2 == 1

            # Color bets
            elif bet == "red":
                return color == "red"
            elif bet == "black":
                return color == "black"

            # Range bets (e.g., "1-12")
            elif "-" in bet:
                try:
                    start, end = map(int, bet.split("-"))
                    return start <= result <= end
                except ValueError:
                    return False

            # Single number bet
            elif bet.isdigit():
                return result == int(bet)

            return False
        def get_payout_multiplier(bet):
            bet = bet.lower()

            # Even / Odd
            if bet in ("even", "odd", "red", "black"):
                return 2  # double your life

            # Ranges
            if "-" in bet:
                try:
                    start, end = map(int, bet.split("-"))
                    if start == 1 and end == 12 or start == 13 and end == 24 or start == 25 and end == 36:
                        return 3  # dozen bet
                except ValueError:
                    pass
                return 3  # treat as range = dozen-like payout

            # Single number
            if bet.isdigit():
                return 36  # full board payout

            return 0  # invalid bet

        data = megaload()
        await interaction.response.defer()
        if profile not in data["profiles"]:
            await interaction.followup.send(f"Profile `{profile}` does not exist.")
            return
        if not data["profiles"][profile].get("is_active", True):
            await interaction.followup.send(f"Profile `{profile}` is already inactive.")
            return

        result, color = spin_roulette()

        if check_bet_win(result, color, bet_type):
            base_value = 100
            multiplier = get_payout_multiplier(bet_type)
            reward = base_value * multiplier

            # Add to shared currency balance
            data["MD"]["currency"]["cost"] += reward

            await interaction.followup.send(
                f"🎉 `{profile}` survived! The ball landed on **{result} ({color})**. "
                f"You gain {reward} currency. Total now: {data['MD']['currency']['cost']}"
            )
        else:
            data["profiles"][profile]["is_active"] = False
            await interaction.followup.send(
                f"💀 `{profile}` DIED! The ball landed on **{result} ({color})**."
            )

        megasave(data=data)



async def setup(bot):
    cog = MDCog(bot)
    await bot.add_cog(cog)
