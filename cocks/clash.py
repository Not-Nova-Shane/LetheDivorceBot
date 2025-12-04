# pyright: reportMissingImports=false
import copy
import discord
from discord.ext import commands
from discord import app_commands
from everythingexcepthim import (
    megaload ,mehandleclashingoooo,
    resource ,send_split_embeds ,
    autocomplete_page_names ,
    autocomplete_profile_names, unopposedattack,clashhandler,
      megasave)
from THECORE import (PAGE_PATH ,  PROFILE_PATH , lock_command)
class ClashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="clash")
    @app_commands.describe(attacker="Attacker name", attacker_page="Attacker page", defender="Defender name", defender_page="Defender page")
    @app_commands.autocomplete(
        attacker_page=autocomplete_page_names,
        attacker=autocomplete_profile_names,
        defender_page=autocomplete_page_names,
        defender=autocomplete_profile_names
    )
    @lock_command
    async def clash(self,interaction: discord.Interaction, attacker: str, attacker_page: str, defender: str, defender_page: str):
        data = megaload()
        await interaction.response.defer()
        await clashhandler(interaction,data,attacker,attacker_page,defender,defender_page)
        megasave(data)


async def setup(bot):
    cog = ClashCog(bot)
    await bot.add_cog(cog)