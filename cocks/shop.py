# pyright: reportMissingImports=false
import datetime
import discord
import time
import random
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import (megaload , megasave, autocomplete_page_names,is_debtor_blocked,send_split_embeds, autocomplete_profile_names )
from THECORE import (PAGE_PATH ,PROFILE_PATH, INV_PATH, SHOP_PATH,symbol,lock_command)

PAPERBACK_COSTS_PAGE = (5000, 10000)
HARDCOVER_COSTS_PAGE = (15000, 25000)
LIMITED_COSTS_PAGE = (30000, 40000)
UNIQUE_COSTS_PAGE = (40000, 60000)

PAPERBACK_COSTS_PASSIVES = (100, 200)
HARDCOVER_COSTS_PASSIVES = (300, 500)
LIMITED_COSTS_PASSIVES = (600, 900)
UNIQUE_COSTS_PASSIVES = (900, 1500)

def GetItemPriceGetter(tier, stage, passiveOrPage, max = False):
    val = 99999999
    if passiveOrPage == "Page":
        if max:
            match tier:
                case "Paperback":
                    val = PAPERBACK_COSTS_PAGE[1]
                case "Hardcover":
                    val = HARDCOVER_COSTS_PAGE[1]
                case "Limited":
                    val = LIMITED_COSTS_PAGE[1]
                case "Masterwork":
                    val = UNIQUE_COSTS_PAGE[1]
        else:
            match tier:
                case "Paperback":
                    val = random.randint(*PAPERBACK_COSTS_PAGE)
                case "Hardcover":
                    val = random.randint(*HARDCOVER_COSTS_PAGE)
                case "Limited":
                    val = random.randint(*LIMITED_COSTS_PAGE)
                case "Masterwork":
                    val = random.randint(*UNIQUE_COSTS_PAGE)

    elif passiveOrPage == "Passive":
        if max:
            match tier:
                case "Paperback":
                    val = PAPERBACK_COSTS_PASSIVES[1]
                case "Hardcover":
                    val = HARDCOVER_COSTS_PASSIVES[1]
                case "Limited":
                    val = LIMITED_COSTS_PASSIVES[1]
                case "Masterwork":
                    val = UNIQUE_COSTS_PASSIVES[1]
        else:
            match tier:
                case "Paperback":
                    val = random.randint(*PAPERBACK_COSTS_PASSIVES)
                case "Hardcover":
                    val = random.randint(*HARDCOVER_COSTS_PASSIVES)
                case "Limited":
                    val = random.randint(*LIMITED_COSTS_PASSIVES)
                case "Masterwork":
                    val = random.randint(*UNIQUE_COSTS_PASSIVES)

    mult = 100
    match stage:
        case "Canard":
            mult = 1
        case "Urban Myth":
            mult = 1.3
        case "Urban Legend":
            mult = 1.6
        case"Urban Plague":
            mult = 1.9
        case "Urban Nightmare":
            mult = 2.2
        case "Star of the City":
            mult = 2.5
        case "Impuritas":
            mult = 3
    return int(val * mult)

class ShopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def autocomplete_currentlySold_pageNames(self, interaction: discord.Interaction, current: str):
        current = current.lower().strip()  # remove extra spaces
        data = megaload()
        pages = data["shop"]["SHOP"]["currentlyselling"]
        print(pages)

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in pages.keys()
            if current in page_name.lower()
        ]

        return suggestions[:25]  # Discord limits to 25 choices

    async def autocomplete_currentlySold_passiveNames(self, interaction: discord.Interaction, current: str):
        current = current.lower().strip()  # remove extra spaces
        data = megaload()
        pages = data["passhop"]["SHOP"]["currentlyselling"]
        print(pages)

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in pages.keys()
            if current in page_name.lower()
        ]

        return suggestions[:25]  # Discord limits to 25 choices

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="getenemypages")
    @app_commands.describe(owner="The bum they get given to")
    @app_commands.autocomplete(
        owner=autocomplete_profile_names
    )
    @lock_command
    async def getenemypages(self, interaction: discord.Interaction, owner: str):
        data = megaload()
        await interaction.response.defer()
        givenpages = data["shop"]["gainedPages"]
        inventory = data["inventory"][owner]
        length_of_givenPages = len(givenpages)

        gained_pages = []  # store what the user gets

        for _ in range(3):  # exactly 3 pages
            page = random.choice(givenpages)
            inventory["pages"].append(page)
            gained_pages.append(page)

        pageNameList = ", ".join(gained_pages)

        embed = discord.Embed(
            title = f"{owner} has gained the following 3 random pages: {pageNameList}",
            description=" ",
            color=discord.Color.green()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="sell")
    @app_commands.describe(owner="name",page="Page to sell")
    @app_commands.autocomplete(
        page=autocomplete_page_names
    )
    @lock_command
    async def sell(self, interaction: discord.Interaction, owner: str, page: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        shop = data["shop"]

        if page in ["Focused Strikes", "Charge and Cover", "Light Attack", "Light Defense", "Evade"]:
            await interaction.followup.send(f"❌ Nuh Uh.")
            return
        sold_page = shop.get(page)
        if page not in shop or page == "SHOP":
            await interaction.followup.send(f"❌ That page doesn't exist.")
            return

        sellcost = GetItemPriceGetter(sold_page.get("tier","Paperback"), sold_page.get("stage","Canard"), "Page", True) // 2
        if owner not in inventory:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return
        if page not in inventory[owner]["pages"]:
            await interaction.followup.send(f"❌ The profile does not own the page.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        inventory[owner]["ahn"] += sellcost
        inventory[owner]["pages"].remove(page)
        embed = discord.Embed(
            title=f"{owner} has sold {page} for {sellcost} Ahn",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
   
    @app_commands.command(name="buy")
    @app_commands.describe(owner="name",page="Page to buy")
    @app_commands.autocomplete(page=autocomplete_currentlySold_pageNames)
    @lock_command
    async def buy(self, interaction: discord.Interaction, owner: str, page: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        shop = data["shop"]

        theshop = shop["SHOP"]
        if page not in shop:
            await interaction.followup.send(f"❌ That page doesn't exist.")
            return
        if page not in theshop["cansell"]:
            await interaction.followup.send(f"❌ That page is not being Sold.")
            return

        if owner not in inventory:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return

        if page in theshop["currentlyselling"]:
            buycost = theshop["currentlyselling"][page]
        else:
            buycost = GetItemPriceGetter(shop[page].get("tier","Paperback"), shop[page].get("stage","Canard"), "Page", True)


        if buycost > inventory[owner]["ahn"]:
            await interaction.followup.send(f"❌ Too Expensive.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        if is_debtor_blocked(inventory[owner]):
            await interaction.followup.send("❌ You are currently in debt and cannot interact with the economy.")
            return

        inventory[owner]["ahn"] -= buycost
        inventory[owner]["pages"].append(page)
        embed = discord.Embed(
            title=f"{owner} has bought {page} for {buycost} Ahn",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="refresh")
    @lock_command
    async def refresh(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        shop = data["shop"]
        theshop = shop["SHOP"]
        logs = []
        theshop["currentlyselling"] = {}
        cansell = theshop.get("cansell")
        random.shuffle(cansell)
        selling = cansell[:theshop["sellingamount"]]
        for page in selling:
            if page in shop:
                pageprice = GetItemPriceGetter(shop[page].get("tier","Paperback"), shop[page].get("stage","Canard"), "Page")
                theshop["currentlyselling"][page] = pageprice
                logs.append(f"{page} is being sold at a discount of {pageprice} Ahn!")


        embed = discord.Embed(
            title=f"The shop has been refreshed!",
            description=f"🕒 Refreshed <t:{int(time.time())}:R>",
            color=discord.Color.gold()
        )
        fields = []
        for section in logs:
            fields.append((f"{symbol['light']} New Shop Item: {symbol['light']}",section,False))
        megasave(data)
        await send_split_embeds(interaction,embed,fields)

    @app_commands.command(name="passivesell")
    @app_commands.describe(owner="name",passive="passive to sell")
    @lock_command
    async def passivesell(self, interaction: discord.Interaction, owner: str, passive: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        shop = data["passhop"]
        
        sold_pas = shop.get(passive)
        if passive not in shop or passive == "SHOP":
            await interaction.followup.send(f"❌ That passive doesn't exist.")
            return
        sellcost = GetItemPriceGetter(sold_pas.get("tier","Paperback"), sold_pas.get("stage","Canard"), "Passive", True) // 2
        if owner not in inventory:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return
        if passive not in inventory[owner]["passives"]:
            await interaction.followup.send(f"❌ The profile does not own the passive.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return

        inventory[owner]["lunacy"] += sellcost
        inventory[owner]["passives"].remove(passive)
        embed = discord.Embed(
            title=f"{owner} has sold {passive} for {sellcost} Lunacy",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
   
    @app_commands.command(name="passivebuy")
    @app_commands.describe(owner="name",passive="Page to buy")
    @app_commands.autocomplete(
        passive=autocomplete_currentlySold_passiveNames
    )
    @lock_command
    async def passivebuy(self, interaction: discord.Interaction, owner: str, passive: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        shop = data["passhop"]

        theshop = shop["SHOP"]
        if passive not in shop:
            await interaction.followup.send(f"❌ That passive doesn't exist.")
            return
        if passive not in theshop["cansell"]:
            await interaction.followup.send(f"❌ That passive is not being Sold.")
            return
        if owner not in inventory:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return

        if passive in theshop["currentlyselling"]:
            buycost = theshop["currentlyselling"][passive]
        else:
            buycost = GetItemPriceGetter(shop[passive].get("tier","Paperback"), shop[passive].get("stage","Canard"), "Passive", True)

        if buycost > inventory[owner]["lunacy"]:
            await interaction.followup.send(f"❌ Too Expensive.")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        if is_debtor_blocked(inventory[owner]):
            await interaction.followup.send("❌ You are currently in debt and cannot interact with the economy.")
            return

        inventory[owner]["lunacy"] -= buycost
        inventory[owner]["passives"].append(passive)
        embed = discord.Embed(
            title=f"{owner} has bought {passive} for {buycost} Lunacy",
            description=" ",
            color=discord.Color.red()
        )
        megasave(data)
        await interaction.followup.send(embed=embed)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="passiverefresh")
    @lock_command
    async def passiverefresh(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        shop = data["passhop"]
        theshop = shop["SHOP"]
        logs = []
        theshop["currentlyselling"] = {}
        cansell = theshop.get("cansell")
        random.shuffle(cansell)
        selling = cansell[:theshop["sellingamount"]]
        for passive in selling:
            if passive in shop:
                pasprice = GetItemPriceGetter(shop[passive].get("tier", "Paperback"), shop[passive].get("stage","Canard"), "Passive")
                theshop["currentlyselling"][passive] = pasprice
                logs.append(f"{passive} is being sold at {pasprice} Lunacy!")


        embed = discord.Embed(
            title=f"The shop has been refreshed!",
            description=f"🕒 Refreshed <t:{int(time.time())}:R>",
            color=discord.Color.gold()
        )
        fields = []
        for section in logs:
            fields.append((f"{symbol['light']} New Shop Item: {symbol['light']}",section,False))
        megasave(data)
        await send_split_embeds(interaction,embed,fields)
   

async def setup(bot):
    cog = ShopCog(bot)
    await bot.add_cog(cog)
