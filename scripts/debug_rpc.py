import asyncio
import os
from shared.solana_utils import get_assets_by_owner
from shared.database import get_session, FlexNFT

WALLET = "GQtVDQnNCcpYCbpneEw675ufsGbJQkJzLtSHPWXLQAUP"
COLLECTION_SLUG = "the_growerz"

async def main():
    print(f"--- Debugging Wallet: {WALLET} ---")
    
    # 1. Check RPC
    print("Fetching assets from RPC...")
    assets = await get_assets_by_owner(WALLET)
    print(f"RPC returned {len(assets)} assets.")
    
    if assets:
        print("First 5 assets from RPC:")
        for asset in assets[:5]:
            print(f" - Mint: {asset['mint']} | Name: {asset['name']}")

    # 2. Check DB
    print(f"\nChecking DB for collection: {COLLECTION_SLUG}")
    session = get_session()
    try:
        # Check total items in DB for this collection
        total_db = session.query(FlexNFT).filter_by(collection_slug=COLLECTION_SLUG).count()
        print(f"Total items in DB for '{COLLECTION_SLUG}': {total_db}")

        if assets:
            # Check overlap
            mints = [a['mint'] for a in assets]
            matching = session.query(FlexNFT).filter(
                FlexNFT.mint.in_(mints),
                FlexNFT.collection_slug == COLLECTION_SLUG
            ).all()
            print(f"Found {len(matching)} matching items in DB.")
            
            if not matching and len(assets) > 0:
                print("WARNING: Assets found in wallet but NONE match the DB records for this collection.")
                # Check if they exist in DB under a different collection?
                any_match = session.query(FlexNFT).filter(FlexNFT.mint.in_(mints)).all()
                if any_match:
                    print(f"However, {len(any_match)} of these mints exist in the DB under different slugs:")
                    for m in any_match[:5]:
                        print(f" - {m.mint} -> {m.collection_slug}")
                else:
                    print("None of the wallet's mints exist in the DB at all.")

    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
