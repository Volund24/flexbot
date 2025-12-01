import discord
from discord import app_commands
from discord.ext import commands
from shared.database import get_session, FlexPlayer, FlexGuildConfig, FlexNFT
import os
import aiohttp
import time
import sys
import asyncio

ADMIN_ROLE = os.getenv("DISCORD_ADMIN_ROLE", "Admin")
HOWRARE_API_BASE = os.getenv("HOWRARE_API_BASE", "https://api.howrare.is/v0.1")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_syncing = False
        self.stop_sync_flag = False

    def is_admin(self, interaction: discord.Interaction) -> bool:
        # Check if user has the configured Admin role OR is the server owner OR has Administrator permission
        has_role = any(role.name == ADMIN_ROLE for role in interaction.user.roles)
        is_owner = interaction.user.id == interaction.guild.owner_id
        is_admin_perm = interaction.user.guild_permissions.administrator
        return has_role or is_owner or is_admin_perm

    @app_commands.command(name="admin_restart", description="Restart the bot process")
    async def admin_restart(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
        
        await interaction.response.send_message("Restarting bot process... (This may take a few seconds)", ephemeral=True)
        # Exit with status 1 so Docker/Systemd restarts it
        sys.exit(1)

    @app_commands.command(name="admin_stop_sync", description="Stop any active collection sync")
    async def admin_stop_sync(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return
            
        if not self.is_syncing:
            await interaction.response.send_message("No sync is currently in progress.", ephemeral=True)
            return

        self.stop_sync_flag = True
        await interaction.response.send_message("Signal sent to stop sync. It should halt shortly.", ephemeral=True)

    @app_commands.command(name="admin_sync_collection", description="Sync full collection metadata to database (Heavy Operation)")
    async def admin_sync_collection(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        if self.is_syncing:
            await interaction.response.send_message("A sync is already in progress. Use `/admin_stop_sync` to stop it.", ephemeral=True)
            return

        self.is_syncing = True
        self.stop_sync_flag = False
        
        await interaction.response.defer()
        session = get_session()
        try:
            # Get collection slug
            config = session.query(FlexGuildConfig).filter_by(guild_id=interaction.guild_id).first()
            collection_slug = config.collection_slug if config else os.getenv("HOWRARE_COLLECTION", "the_growerz")

            # Fetch full collection data
            url = f"{HOWRARE_API_BASE}/collections/{collection_slug}"
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url) as response:
                    if response.status != 200:
                        await interaction.followup.send(f"Error fetching collection: {response.status}")
                        self.is_syncing = False
                        return
                    data = await response.json()

            items = data.get('result', {}).get('data', {}).get('items', [])
            if not items:
                await interaction.followup.send("No items found in API response.")
                self.is_syncing = False
                return

            # Upsert items into FlexNFT
            count = 0
            total = len(items)
            
            # Initial status update
            status_msg = await interaction.followup.send(f"Starting sync for {total} items...")

            for i, item in enumerate(items):
                # Check for stop signal
                if self.stop_sync_flag:
                    await interaction.followup.send(f"Sync stopped by admin at item {count}/{total}.")
                    break

                mint = item.get('mint')
                if not mint: continue

                nft = session.query(FlexNFT).filter_by(mint=mint).first()
                if not nft:
                    nft = FlexNFT(mint=mint)
                    session.add(nft)
                
                nft.collection_slug = collection_slug
                nft.name = item.get('name')
                nft.rank = item.get('rank')
                nft.image_url = item.get('image')
                nft.attributes = item.get('attributes')
                nft.last_updated = time.time()
                count += 1
                
                # Commit in batches to avoid massive transaction and allow other DB ops
                if count % 50 == 0:
                    session.commit()
                    # Yield control to event loop to prevent bot freezing
                    await asyncio.sleep(0)
                
                # Update status every 500 items
                if count % 500 == 0:
                    try:
                        await status_msg.edit(content=f"Syncing... {count}/{total} items processed.")
                    except:
                        pass

            session.commit()
            if not self.stop_sync_flag:
                await interaction.followup.send(f"Successfully synced {count} NFTs for collection `{collection_slug}`.")

        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"Error syncing collection: {e}")
        finally:
            session.close()
            self.is_syncing = False

    @app_commands.command(name="admin_set_collection", description="Change the target NFT collection")
    async def admin_set_collection(self, interaction: discord.Interaction, collection_slug: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        session = get_session()
        try:
            config = session.query(FlexGuildConfig).filter_by(guild_id=interaction.guild_id).first()
            if not config:
                config = FlexGuildConfig(guild_id=interaction.guild_id, collection_slug=collection_slug)
                session.add(config)
            else:
                config.collection_slug = collection_slug
            
            session.commit()
            await interaction.response.send_message(f"Collection set to `{collection_slug}`.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)
        finally:
            session.close()

    @app_commands.command(name="admin_set_wallet", description="Manually link a wallet for a user")
    async def admin_set_wallet(self, interaction: discord.Interaction, user: discord.User, address: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        session = get_session()
        try:
            player = session.query(FlexPlayer).filter_by(discord_id=user.id).first()
            if not player:
                player = FlexPlayer(discord_id=user.id)
                session.add(player)
            
            player.wallet_address = address
            session.commit()
            await interaction.response.send_message(f"Wallet for {user.mention} set to `{address}`.", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)
        finally:
            session.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
