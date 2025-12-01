import discord
from discord import app_commands
from discord.ext import commands
from shared.database import get_session, FlexPlayer
import re

BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def is_valid_solana_address(address: str) -> bool:
    if not (32 <= len(address) <= 44):
        return False
    if not all(c in BASE58_ALPHABET for c in address):
        return False
    return True

class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="link_wallet", description="Link your Solana wallet address")
    async def link_wallet(self, interaction: discord.Interaction, address: str):
        if not is_valid_solana_address(address):
            await interaction.response.send_message("Invalid Solana address format.", ephemeral=True)
            return

        session = get_session()
        try:
            player = session.query(FlexPlayer).filter_by(discord_id=interaction.user.id).first()
            if not player:
                player = FlexPlayer(discord_id=interaction.user.id)
                session.add(player)
            
            player.wallet_address = address
            session.commit()
            await interaction.response.send_message(f"Wallet linked successfully: `{address}`", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"Error linking wallet: {e}", ephemeral=True)
        finally:
            session.close()

    @app_commands.command(name="unlink_wallet", description="Unlink your Solana wallet")
    async def unlink_wallet(self, interaction: discord.Interaction):
        session = get_session()
        try:
            player = session.query(FlexPlayer).filter_by(discord_id=interaction.user.id).first()
            if player and player.wallet_address:
                player.wallet_address = None
                session.commit()
                await interaction.response.send_message("Wallet unlinked successfully.", ephemeral=True)
            else:
                await interaction.response.send_message("No wallet linked.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"Error unlinking wallet: {e}", ephemeral=True)
        finally:
            session.close()

    @app_commands.command(name="view_wallet", description="View your linked wallet")
    async def view_wallet(self, interaction: discord.Interaction):
        session = get_session()
        try:
            player = session.query(FlexPlayer).filter_by(discord_id=interaction.user.id).first()
            if player and player.wallet_address:
                await interaction.response.send_message(f"Linked Wallet: `{player.wallet_address}`", ephemeral=True)
            else:
                await interaction.response.send_message("No wallet linked. Use `/link_wallet` to link one.", ephemeral=True)
        finally:
            session.close()

async def setup(bot):
    await bot.add_cog(Wallet(bot))
