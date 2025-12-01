import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
from shared.database import get_session, FlexPlayer, FlexGuildConfig, FlexNFT

HOWRARE_API_BASE = os.getenv("HOWRARE_API_BASE", "https://api.howrare.is/v0.1")
DEFAULT_COLLECTION = os.getenv("HOWRARE_COLLECTION", "the_growerz")

class Flex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_nfts(self, wallet_address: str, collection_slug: str):
        session = get_session()
        try:
            # 1. Fetch Owners (Lightweight)
            owners_url = f"{HOWRARE_API_BASE}/collections/{collection_slug}/owners"
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(owners_url) as response:
                    if response.status == 200:
                        owners_data = await response.json()
                        owners_map = owners_data.get('result', {}).get('data', {}).get('owners', {})
                        
                        # Update ownership in DB for this user's mints (and clear old ones if needed)
                        # For efficiency, we only update mints that match the wallet or were previously owned by it
                        # But simpler approach: Find all mints in DB that *should* be owned by this wallet
                        
                        owned_mints = {mint for mint, owner in owners_map.items() if owner == wallet_address}
                        
                        # Bulk update is complex in ORM, let's do simple iteration for now or raw SQL
                        # Reset previous ownership for this wallet (optional, but good for correctness)
                        # session.query(FlexNFT).filter_by(owner_wallet=wallet_address).update({"owner_wallet": None})
                        
                        # Update new ownership
                        if owned_mints:
                            # We only update mints that exist in our DB (synced via admin command)
                            # This avoids inserting partial data
                            mints_in_db = session.query(FlexNFT).filter(FlexNFT.mint.in_(owned_mints)).all()
                            for nft in mints_in_db:
                                nft.owner_wallet = wallet_address
                            
                            session.commit()
            
            # 2. Query DB for user's NFTs
            user_nfts = session.query(FlexNFT).filter_by(owner_wallet=wallet_address, collection_slug=collection_slug).all()
            
            # Convert to dict-like structure to match previous logic
            results = []
            for nft in user_nfts:
                results.append({
                    'name': nft.name,
                    'rank': nft.rank,
                    'image': nft.image_url,
                    'attributes': nft.attributes,
                    'mint': nft.mint
                })
            
            return results

        except Exception as e:
            print(f"Error in fetch_nfts: {e}")
            return []
        finally:
            session.close()

    @app_commands.command(name="flex", description="Flex your NFTs")
    async def flex(self, interaction: discord.Interaction, trait_filter: str = None):
        await interaction.response.defer()
        
        session = get_session()
        try:
            player = session.query(FlexPlayer).filter_by(discord_id=interaction.user.id).first()
            if not player or not player.wallet_address:
                await interaction.followup.send("You need to link your wallet first using `/link_wallet`.")
                return

            # Get Guild Config or default
            config = session.query(FlexGuildConfig).filter_by(guild_id=interaction.guild_id).first()
            collection_slug = config.collection_slug if config else DEFAULT_COLLECTION
            
            # Fetch NFTs
            user_nfts = await self.fetch_nfts(player.wallet_address, collection_slug)
            
            if not user_nfts:
                # Fallback message since we can't actually hit the API without a real key/endpoint
                # Check if DB has any items for this collection at all
                item_count = session.query(FlexNFT).filter_by(collection_slug=collection_slug).count()
                if item_count == 0:
                     await interaction.followup.send(f"Database is empty for collection `{collection_slug}`. Please ask an admin to run `/admin_sync_collection` first.")
                else:
                    await interaction.followup.send(f"Could not find any NFTs from collection `{collection_slug}` in wallet `{player.wallet_address}`. (Database has {item_count} items).")
                return

            # Filter by trait if requested
            if trait_filter:
                # trait_filter format "trait:value" or just "value"
                filtered_nfts = []
                for nft in user_nfts:
                    attributes = nft.get('attributes', [])
                    # Check if any attribute matches the filter
                    # Simple check: value contains filter or name contains filter
                    match = False
                    for attr in attributes:
                        if trait_filter.lower() in attr.get('value', '').lower() or trait_filter.lower() in attr.get('name', '').lower():
                            match = True
                            break
                    if match:
                        filtered_nfts.append(nft)
                
                if not filtered_nfts:
                    await interaction.followup.send(f"Found {len(user_nfts)} NFTs, but none matched filter `{trait_filter}`.")
                    return
                user_nfts = filtered_nfts

            # Select the best NFT to flex (e.g., highest rank - lower is better usually)
            # Assuming 'rank' is an integer where 1 is best
            user_nfts.sort(key=lambda x: int(x.get('rank', 999999)))
            top_nft = user_nfts[0]
            
            # Determine Color based on Rank
            rank = int(top_nft.get('rank', 999999))
            
            # Check for "Signed by haizeel" attribute
            is_signed = False
            for attr in top_nft.get('attributes', []):
                if attr.get('name') == "Signed by haizeel" and str(attr.get('value')).lower() == "true":
                    is_signed = True
                    break
            
            if is_signed or rank == 1:
                color = 0xFFD700 # Gold (for 1/1 or Signed)
                rarity_status = "1/1" if rank == 1 else "Signed"
            elif 1 <= rank <= 71:
                color = 0x9932CC # Mythic (Purple)
                rarity_status = "Mythic"
            elif 72 <= rank <= 361:
                color = 0xFFA500 # Epic (Orange)
                rarity_status = "Epic"
            elif 362 <= rank <= 843:
                color = 0x1E90FF # Rare (Blue)
                rarity_status = "Rare"
            elif 844 <= rank <= 1446:
                color = 0x32CD32 # Uncommon (Green)
                rarity_status = "Uncommon"
            else:
                color = 0xADFF2F # Common (Yellow-Green)
                rarity_status = "Common"

            # Build Embed
            embed = discord.Embed(title=f"{top_nft['name']}", color=color)
            embed.set_author(name=interaction.user.display_name)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Field 1: Rank
            embed.add_field(name="Rank", value=f"#{rank}", inline=True)
            
            # Field 2: Rarity Status
            embed.add_field(name="Rarity", value=rarity_status, inline=True)

            # Field 3: Owned Count
            embed.add_field(name="Owned", value=str(len(user_nfts)), inline=True)
            
            embed.set_image(url=top_nft['image'])
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")
        finally:
            session.close()

async def setup(bot):
    await bot.add_cog(Flex(bot))
