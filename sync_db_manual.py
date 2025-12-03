import asyncio
import aiohttp
import os
import time
from shared.database import get_session, FlexNFT

# Configuration
COLLECTIONS_TO_SYNC = ["gainz", "giga_buds"]
HOWRARE_API_BASE = os.getenv("HOWRARE_API_BASE", "https://api.howrare.is/v0.1")

async def sync_collection(collection_slug):
    print(f"Starting sync for: {collection_slug}")
    session = get_session()
    try:
        url = f"{HOWRARE_API_BASE}/collections/{collection_slug}"
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(url) as response:
                if response.status != 200:
                    print(f"Error fetching {collection_slug}: {response.status}")
                    return
                data = await response.json()

        items = data.get('result', {}).get('data', {}).get('items', [])
        if not items:
            print(f"No items found for {collection_slug}")
            return

        print(f"Found {len(items)} items. Upserting to database...")
        
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
            
            if count % 100 == 0:
                session.commit()
                print(f"Processed {count} items...")

        session.commit()
        print(f"Successfully synced {count} items for {collection_slug}")

    except Exception as e:
        print(f"Error syncing {collection_slug}: {e}")
        session.rollback()
    finally:
        session.close()

async def main():
    print("Starting manual database sync...")
    for slug in COLLECTIONS_TO_SYNC:
        await sync_collection(slug)
    print("All syncs complete.")

if __name__ == "__main__":
    asyncio.run(main())
