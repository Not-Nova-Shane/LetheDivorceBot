# pyright: reportMissingImports=false
import copy
import discord
from discord.ext import commands
from discord import app_commands
from THECORE import (ProfileMan, PROFILE_PATH, symbol,lock_command)

class ReloadDataCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="reloadpages")
    @lock_command
    async def reloadpages(self, interaction: discord.Interaction):
        ProfileMan.load_profiles()
        await interaction.response.defer()
        await interaction.followup.send(f"All Profiles reloaded")

    @app_commands.command(name="savepages")
    @lock_command
    async def savepages(self, interaction: discord.Interaction):
        ProfileMan.save_profiles(PROFILE_PATH)
        await interaction.response.defer()
        await interaction.followup.send(f"All Profiles saved")

async def setup(bot):
    cog = ReloadDataCog(bot)
    await bot.add_cog(cog)
