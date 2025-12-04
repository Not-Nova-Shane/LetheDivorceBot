# pyright: reportMissingImports=false
import copy
import discord
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import attackhandler
from everythingexcepthim import (send_split_embeds, unopposedattack,megaload,megasave ,resource ,autocomplete_page_names ,autocomplete_profile_names,globalpowerhandler)
from THECORE import (PAGE_PATH ,PROFILE_PATH, symbol,lock_command, ProfileMan)

class AttackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="attack")
    @app_commands.describe(attacker="Attacker name", target="Target name", page="Page to use")
    @app_commands.autocomplete(
        page=autocomplete_page_names,
        target=autocomplete_profile_names,
        attacker=autocomplete_profile_names
    )
    @lock_command
    async def attack(self, interaction: discord.Interaction, attacker: str, target: str, page: str):
        data = megaload()
        await interaction.response.defer()
        await attackhandler(interaction,attacker,target,page,data)
        megasave(data)

async def setup(bot):
    cog = AttackCog(bot)
    await bot.add_cog(cog)
