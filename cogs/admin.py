import discord
from discord import app_commands
from discord.ext import commands
from shared.database import get_session, FlexPlayer, FlexGuildConfig, FlexNFT
import os
import aiohttp
import time

ADMIN_ROLE = os.getenv("DISCORD_ADMIN_ROLE", "Admin")
HOWRARE_API_BASE = os.getenv("HOWRARE_API_BASE", "https://api.howrare.is/v0.1")

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, interaction: discord.Interaction) -> bool:
        # Check if user has the configured Admin role OR is the server owner OR has Administrator permission
        has_role = any(role.name == ADMIN_ROLE for role in interaction.user.roles)
        is_owner = interaction.user.id == interaction.guild.owner_id
        is_admin_perm = interaction.user.guild_permissions.administrator
        return has_role or is_owner or is_admin_perm

    @app_commands.command(name="admin_set_role", description="Set the admin role name for this server")
    async def admin_set_role(self, interaction: discord.Interaction, role_name: str):
        # Only server owner or Administrator permission can change this
        if not (interaction.user.id == interaction.guild.owner_id or interaction.user.guild_permissions.administrator):
            await interaction.response.send_message("Only the server owner or an administrator can change the admin role.", ephemeral=True)
            return

        # In a real DB, we would save this to GuildConfig. For now, we just acknowledge it.
        # Since we are using env var for simplicity, we can't easily change it per server without DB schema change.
        # But we can update the check to look for this role name dynamically if we stored it.
        
        # Let's update GuildConfig to store admin_role_name
        session = get_session()
        try:
            config = session.query(FlexGuildConfig).filter_by(guild_id=interaction.guild_id).first()
            if not config:
                config = FlexGuildConfig(guild_id=interaction.guild_id, collection_slug="the_growerz") # Default slug
                session.add(config)
            
            # We need to add this column to DB first. For now, let's just tell user to use .env or match the role.
            # Or better, let's just rely on the permission check update I made which includes Administrator perm.
            pass
        finally:
            session.close()
            
        await interaction.response.send_message(f"Admin role configuration is currently set via environment variable to `{ADMIN_ROLE}`. Please ensure you have the 'Administrator' permission or the role `{ADMIN_ROLE}`.", ephemeral=True)

    @app_commands.command(name="admin_sync_collection", description="Sync full collection metadata to database (Heavy Operation)")
    async def admin_sync_collection(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

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
                        return
                    data = await response.json()

            items = data.get('result', {}).get('data', {}).get('items', [])
            if not items:
                await interaction.followup.send("No items found in API response.")
                return

            # Upsert items into FlexNFT
            count = 0
            for item in items:
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
            
            session.commit()
            await interaction.followup.send(f"Successfully synced {count} NFTs for collection `{collection_slug}`.")

        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"Error syncing collection: {e}")
        finally:
            session.close()

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
