import discord
from discord import app_commands
from discord.ext import commands
import os

ADMIN_ROLE = os.getenv("DISCORD_ADMIN_ROLE", "Admin")

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin_help", description="Show help for admin commands")
    async def admin_help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Flexbot Admin Help", color=0x00ff00)
        
        embed.add_field(
            name="/admin_sync_collection", 
            value="**Description:** Downloads the full collection metadata from HowRare.is to the bot's database.\n**When to use:** Run this once when setting up the bot, or if you change the collection.\n**Note:** This is a heavy operation.", 
            inline=False
        )
        
        embed.add_field(
            name="/admin_set_collection [slug]", 
            value="**Description:** Sets the HowRare.is collection slug for this server.\n**Slug:** The part of the URL after `howrare.is/`. Example: for `howrare.is/the_growerz`, the slug is `the_growerz`.\n**Example:** `/admin_set_collection the_growerz`", 
            inline=False
        )
        
        embed.add_field(
            name="/admin_set_wallet [user] [address]", 
            value="**Description:** Manually links a Solana wallet to a Discord user.\n**Example:** `/admin_set_wallet @User GQt...`", 
            inline=False
        )

        embed.add_field(
            name="/admin_set_role [role_name]", 
            value=f"**Description:** Configures the role name required to use admin commands.\n**Current Config:** `{ADMIN_ROLE}` (via .env)", 
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
