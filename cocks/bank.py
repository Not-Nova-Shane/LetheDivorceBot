# pyright: reportMissingImports=false
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import (megaload , megasave ,is_debtor_blocked )
from THECORE import lock_command, ProfileMan
class BankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="loan")
    @app_commands.describe(ahn="ahn to give", given="who to give to")
    @lock_command
    async def loan(self, interaction: discord.Interaction, ahn: int, given: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        profiles = ProfileMan.all_profiles()
        if given not in inventory or given not in profiles:
            await interaction.followup.send(f"❌ That profile you send to doesn't exist.")
            return

        inventory[given]["ahn"] += ahn
        inventory[given]["debt"] = inventory[given].get("debt", 0) + ahn
        inventory[given]["credit"] = inventory[given].get("credit", 100)

        due_date = (datetime.datetime.utcnow() + datetime.timedelta(weeks=1)).isoformat()
        inventory[given]["loan_due"] = due_date


        timestamp = int(datetime.datetime.fromisoformat(due_date).timestamp())
        embed = discord.Embed(
            title=f"🏦 The Big Bank has loaned {ahn} Ahn to {given}",
            description=f"💸 Due on **<t:{timestamp}:F>**\nDon't be a broke criminal.",
            color=discord.Color.dark_gold()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="payback")
    @app_commands.describe(profile="Your profile name", amount="How much Ahn to pay back")
    @lock_command
    async def payback(self, interaction: discord.Interaction, profile: str, amount: int):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        profiles = ProfileMan.get_profile(profile)

        if profile not in inventory or profiles is None:
            await interaction.followup.send(f"❌ That profile doesn't exist.")
            return

        if interaction.user.id != inventory[profile]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        current_debt = inventory[profile].get("debt", 0)
        if current_debt <= 0:
            await interaction.followup.send("✅ You don’t owe anything. Live your best life.")
            return
        if amount <= 0:
            await interaction.followup.send("❌ No")
            return
        if amount > inventory[profile]["ahn"]:
            await interaction.followup.send("❌ Broke ass")
            return

        payment = min(amount, current_debt)
        inventory[profile]["ahn"] -= payment
        inventory[profile]["debt"] -= payment
        if inventory[profile]["debt"] <= 0:
            inventory[profile]["debt"] = 0
            inventory[profile].pop("loan_due", None)
        embed = discord.Embed(
            title=f"💰 {profile} repaid {payment} Ahn of their loan.",
            description=(
                "Debt cleared completely! 🎉" if inventory[profile]["debt"] == 0 else 
                f"Remaining debt: {inventory[profile]['debt']} Ahn."
            ),
            color=discord.Color.gold()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="applyinterest")
    @lock_command
    async def applyinterest(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        now = datetime.datetime.utcnow()
        affected = []

        for user, data in inventory.items():
            debt = data.get("debt", 0)
            due_str = data.get("loan_due", None)

            if debt > 0 and due_str:
                try:
                    due = datetime.datetime.fromisoformat(due_str)
                    if now > due:
                        free_of_interest = ["Jonathan"]
                        new_debt = round(debt * 1.1) if user not in free_of_interest else debt
                        inventory[user]["debt"] = new_debt
                        affected.append((user, debt, new_debt))
                except ValueError:
                    continue


        if not affected:
            await interaction.followup.send("📈 Nobody was overdue. The debtors live another day...")
            return

        msg_lines = [f"💀 Interest Applied to {len(affected)} user(s):"]
        for user, old, new in affected:
            msg_lines.append(f"• **{user}**: {old} → {new} Ahn")
        megasave(data)

        await interaction.followup.send("\n".join(msg_lines))

    @app_commands.command(name="fund")
    @app_commands.describe(owner="giver",ahn="ahn to give", given="who to give to")
    @lock_command
    async def fund(self, interaction: discord.Interaction, owner: str, ahn: int, given: str):
        data = megaload()
        await interaction.response.defer()
        inventory = data["inventory"]
        profiles = ProfileMan.all_profiles()
        if owner not in inventory or owner not in profiles:
            await interaction.followup.send(f"❌ That giver doesn't exist.")
            return
        if given not in inventory or given not in profiles:
            await interaction.followup.send(f"❌ That profile you send to doesn't exist.")
            return
        if ahn < 0 and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send(f"❌ Scammer")
            return
        if ahn > inventory[owner]["ahn"]:
            await interaction.followup.send(f"❌ The profile is a BROKIE")
            return
        if interaction.user.id != inventory[owner]["owner_id"] and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ That's not your profile.")
            return
        if is_debtor_blocked(inventory[owner]):
            await interaction.followup.send("❌ You are currently in debt and cannot interact with the economy.")
            return

        if 0 <= ahn <= 100 and owner == given:
            title = f" wow. {owner} gave themselves **{ahn}** Ahn. The nation’s economy will never recover, Capitalism is over at this major act of great generosity, truly heartwarming.."
        elif 0 <= ahn <= 100:
            title = f" wow. {owner} gave {given} **{ahn}** Ahn. The nation’s economy will never recover."
        elif owner == given:
            title = " wow, how incredibly incredible, just such a useful, amazing incredible deal, wonderful truly."
        else:
            title = f"{owner} has funded {given} by {ahn} Ahn!"

        inventory[owner]["ahn"] -= ahn
        inventory[given]["ahn"] += ahn
        embed = discord.Embed(
            title=title,
            description=" ",
            color=discord.Color.green()
        )
        megasave(data)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="fundlunacy")
    @app_commands.describe(owner="giver", lunacy="lunacy to give", given="who to give to")
    @lock_command
    async def fundlunacy(self, interaction: discord.Interaction, owner: str, lunacy: int, given: str):
            data = megaload()
            await interaction.response.defer()
            inventory = data["inventory"]
            profiles = ProfileMan.all_profiles()
            if owner not in inventory or owner not in profiles:
                await interaction.followup.send(f"❌ That giver doesn't exist.")
                return
            if given not in inventory or given not in profiles:
                await interaction.followup.send(f"❌ That profile you send to doesn't exist.")
                return
            if lunacy < 0 and not interaction.user.guild_permissions.administrator:
                await interaction.followup.send(f"❌ Scammer")
                return
            if lunacy > inventory[owner]["ahn"]:
                await interaction.followup.send(f"❌ The profile is a BROKIE")
                return
            if interaction.user.id != inventory[owner][
                "owner_id"] and not interaction.user.guild_permissions.administrator:
                await interaction.followup.send("❌ That's not your profile.")
                return
            if is_debtor_blocked(inventory[owner]):
                await interaction.followup.send("❌ You are currently in debt and cannot interact with the economy.")
                return

            if 0 <= lunacy <= 100 and owner == given:
                title = f" wow. {owner} gave themselves **{lunacy}** Lunacy. The nation’s economy will never recover, Capitalism is over at this major act of great generosity, truly heartwarming.."
            elif 0 <= lunacy <= 100:
                title = f" wow. {owner} gave {given} **{lunacy}** Lunacy. The nation’s economy will never recover."
            elif owner == given:
                title = " wow, how incredibly incredible, just such a useful, amazing incredible deal, wonderful truly."
            else:
                title = f"{owner} has funded {given} by {lunacy} Lunacy!"

            inventory[owner]["lunacy"] -= lunacy
            inventory[given]["lunacy"] += lunacy
            embed = discord.Embed(
                title=title,
                description=" ",
                color=discord.Color.green()
            )
            megasave(data)

            await interaction.followup.send(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="payout")
    @lock_command
    async def payout(self,interaction: discord.Interaction, participants: str,ahngained: int, lunacy: int):
        data = megaload()
        participantlist = [participant.strip() for participant in participants.split(",")]
        await interaction.response.defer()
        ahn = ahngained
        lunacy = lunacy
        for participant in participantlist:
            data["inventory"][participant]["ahn"] += ahn
            data["inventory"][participant]["lunacy"] += lunacy
        megasave(data)
        await interaction.followup.send(f"{ahn} Ahn and {lunacy} Lunacy have been added to {participantlist} Inventory", ephemeral=False)


async def setup(bot):
    cog = BankCog(bot)
    await bot.add_cog(cog)
