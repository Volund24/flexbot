import os
import aiohttp
import json

# Use the provided QuickNode URL as default, but prefer env var
DEFAULT_RPC = "https://sly-young-bird.solana-mainnet.quiknode.pro/d2728f877d595d91908dcb5bbc4f7ec68c491396/"
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", DEFAULT_RPC)

async def get_assets_by_owner(wallet_address: str):
    """
    Fetches assets (NFTs) owned by a wallet using the Metaplex DAS API (getAssetsByOwner).
    Returns a list of asset dictionaries containing mint, name, image_uri, etc.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAssetsByOwner",
        "params": {
            "ownerAddress": wallet_address,
            "page": 1,
            "limit": 1000,
            "displayOptions": {
                "showFungible": False,
                "showNativeBalance": False
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(SOLANA_RPC_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    print(f"RPC Error: {response.status}")
                    return []
                
                data = await response.json()
                if "error" in data:
                    print(f"RPC Error Body: {data['error']}")
                    return []

                items = data.get("result", {}).get("items", [])
                assets = []
                
                for item in items:
                    # Extract relevant info
                    # DAS structure: item['id'] is the mint
                    # item['content']['links']['image'] is the image
                    # item['content']['metadata']['name'] is the name
                    
                    try:
                        content = item.get("content", {})
                        links = content.get("links", {})
                        metadata = content.get("metadata", {})
                        
                        asset = {
                            "mint": item.get("id"),
                            "name": metadata.get("name", "Unknown"),
                            "image": links.get("image"),
                            "attributes": metadata.get("attributes", [])
                        }
                        assets.append(asset)
                    except Exception as e:
                        continue
                        
                return assets

        except Exception as e:
            print(f"Error in get_assets_by_owner: {e}")
            return []

