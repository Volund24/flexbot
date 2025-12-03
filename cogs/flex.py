import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import random
from shared.database import get_session, FlexPlayer, FlexGuildConfig, FlexNFT
from shared.solana_utils import get_wallet_tokens

HOWRARE_API_BASE = os.getenv("HOWRARE_API_BASE", "https://api.howrare.is/v0.1")
DEFAULT_COLLECTION = os.getenv("HOWRARE_COLLECTION", "the_growerz")

RARITY_CONFIGS = {
    "the_growerz": {
        "tiers": [
            {"max_rank": 1, "name": "1/1", "color": 0xFFD700},
            {"max_rank": 71, "name": "Mythic", "color": 0x9932CC},
            {"max_rank": 361, "name": "Epic", "color": 0xFFA500},
            {"max_rank": 843, "name": "Rare", "color": 0x1E90FF},
            {"max_rank": 1446, "name": "Uncommon", "color": 0x32CD32},
            {"max_rank": 999999, "name": "Common", "color": 0xADFF2F},
        ],
        "special_attributes": [
            {"trait_type": "Signed by haizeel", "value": "true", "name": "Signed", "color": 0xFFD700}
        ]
    },
    "midevils": {
        "tiers": [
            # Total Supply: 5,000
            # 1/1s: Rank 1-27
            {"max_rank": 27, "name": "1/1", "color": 0xFFD700},
            # Mythic (Top 1%): Rank 28-50
            {"max_rank": 50, "name": "Mythic", "color": 0x9932CC},
            # Legendary (Top 4%): Rank 51-200
            {"max_rank": 200, "name": "Legendary", "color": 0xFFA500},
            # Epic (Top 10%): Rank 201-500
            {"max_rank": 500, "name": "Epic", "color": 0xFF4500},
            # Rare (Top 30%): Rank 501-1500
            {"max_rank": 1500, "name": "Rare", "color": 0x1E90FF},
            # Uncommon (Top 60%): Rank 1501-3000
            {"max_rank": 3000, "name": "Uncommon", "color": 0x32CD32},
            # Common: Rank 3001+
            {"max_rank": 999999, "name": "Common", "color": 0xADFF2F},
        ],
        "special_attributes": []
    },
    "gainz": {
        "tiers": [
            {"max_rank": 1, "name": "1/1", "color": 0xFFD700},
            {"max_rank": 71, "name": "Mythic", "color": 0x9932CC},
            {"max_rank": 361, "name": "Epic", "color": 0xFFA500},
            {"max_rank": 843, "name": "Rare", "color": 0x1E90FF},
            {"max_rank": 1446, "name": "Uncommon", "color": 0x32CD32},
            {"max_rank": 999999, "name": "Common", "color": 0xADFF2F},
        ],
        "special_attributes": []
    },
    "giga_buds": {
        "tiers": [
            {"max_rank": 1, "name": "1/1", "color": 0xFFD700},
            {"max_rank": 71, "name": "Mythic", "color": 0x9932CC},
            {"max_rank": 361, "name": "Epic", "color": 0xFFA500},
            {"max_rank": 843, "name": "Rare", "color": 0x1E90FF},
            {"max_rank": 1446, "name": "Uncommon", "color": 0x32CD32},
            {"max_rank": 999999, "name": "Common", "color": 0xADFF2F},
        ],
        "special_attributes": []
    }
}

def get_rarity_info(rank: int, attributes: list, collection_slug: str):
    config = RARITY_CONFIGS.get(collection_slug)
    
    # Default fallback if config doesn't exist
    if not config:
        return "Ranked", 0x808080 # Grey

    # 1. Check Special Attributes
    for special in config.get("special_attributes", []):
        for attr in attributes:
            if attr.get('name') == special['trait_type'] and str(attr.get('value')).lower() == special['value'].lower():
                return special['name'], special['color']

    # 2. Check Rank Tiers
    for tier in config.get("tiers", []):
        if rank <= tier['max_rank']:
            return tier['name'], tier['color']
            
    return "Common", 0xADFF2F

class Flex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_nfts(self, wallet_address: str, collection_slug: str):
        session = get_session()
        try:
            # 1. Fetch Owners via Solana RPC (Direct On-Chain)
            # This replaces the HowRare API call for ownership
            owned_mints = await get_wallet_tokens(wallet_address)
            
            if owned_mints:
                # 2. Update ownership in DB
                # First, clear old ownership for this wallet (optional but cleaner)
                # session.query(FlexNFT).filter_by(owner_wallet=wallet_address).update({"owner_wallet": None})
                
                # Find which of these mints belong to our collection (exist in DB)
                mints_in_db = session.query(FlexNFT).filter(
                    FlexNFT.mint.in_(owned_mints),
                    FlexNFT.collection_slug == collection_slug
                ).all()
                
                # Update ownership
                for nft in mints_in_db:
                    nft.owner_wallet = wallet_address
                
                session.commit()
            
            # 3. Query DB for user's NFTs
            user_nfts = session.query(FlexNFT).filter_by(owner_wallet=wallet_address, collection_slug=collection_slug).all()
            
            # Convert to dict-like structure
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

    async def trait_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        session = get_session()
        try:
            # 1. Get User Wallet
            player = session.query(FlexPlayer).filter_by(discord_id=interaction.user.id).first()
            if not player or not player.wallet_address:
                return []

            # 2. Get Collection Slug
            config = session.query(FlexGuildConfig).filter_by(guild_id=interaction.guild_id).first()
            collection_slug = config.collection_slug if config else DEFAULT_COLLECTION

            # 3. Get User's NFTs (Local DB only for speed)
            user_nfts = session.query(FlexNFT).filter_by(owner_wallet=player.wallet_address, collection_slug=collection_slug).all()

            # 4. Extract Unique Traits
            traits = set()
            for nft in user_nfts:
                if not nft.attributes: continue
                for attr in nft.attributes:
                    name = attr.get('name')
                    value = attr.get('value')
                    if name and value:
                        traits.add(f"{name}: {value}")
            
            # 5. Filter and Return
            choices = [
                app_commands.Choice(name=trait, value=trait)
                for trait in sorted(list(traits))
                if current.lower() in trait.lower()
            ]
            return choices[:25] # Discord limit is 25 choices

        except Exception:
            return []
        finally:
            session.close()

    @app_commands.command(name="flex", description="Flex your NFTs")
    @app_commands.autocomplete(trait_filter=trait_autocomplete)
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
                    await interaction.followup.send(f"Could not find any NFTs from collection `{collection_slug}` in wallet `{player.wallet_address}`.")
                return

            # Filter by trait if requested
            if trait_filter:
                # Check if filter is in "Trait: Value" format from autocomplete
                filter_name = None
                filter_value = trait_filter
                if ": " in trait_filter:
                    parts = trait_filter.split(": ", 1)
                    if len(parts) == 2:
                        filter_name = parts[0]
                        filter_value = parts[1]

                filtered_nfts = []
                for nft in user_nfts:
                    attributes = nft.get('attributes', [])
                    match = False
                    for attr in attributes:
                        attr_name = attr.get('name', '')
                        attr_value = str(attr.get('value', ''))
                        
                        # If we have a specific name from autocomplete, match both
                        if filter_name:
                            if attr_name == filter_name and attr_value == filter_value:
                                match = True
                                break
                        # Fallback to loose matching if user typed manually
                        else:
                            if trait_filter.lower() in attr_value.lower() or trait_filter.lower() in attr_name.lower():
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
            # user_nfts.sort(key=lambda x: int(x.get('rank', 999999)))
            # top_nft = user_nfts[0]
            
            # Randomize selection from the filtered list
            top_nft = random.choice(user_nfts)
            
            # Determine Color based on Rank
            rank = int(top_nft.get('rank', 999999))
            
            rarity_status, color = get_rarity_info(rank, top_nft.get('attributes', []), collection_slug)

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
