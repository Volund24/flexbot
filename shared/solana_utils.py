import os
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID

# Use the provided QuickNode URL as default, but prefer env var
DEFAULT_RPC = "https://sly-young-bird.solana-mainnet.quiknode.pro/d2728f877d595d91908dcb5bbc4f7ec68c491396/"
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", DEFAULT_RPC)

def get_rpc_client():
    return AsyncClient(SOLANA_RPC_URL)

async def get_wallet_tokens(wallet_address: str):
    """
    Fetches all SPL tokens (mints) owned by a wallet using the RPC.
    Returns a set of mint addresses (strings).
    """
    client = get_rpc_client()
    try:
        wallet_pubkey = Pubkey.from_string(wallet_address)
        
        # Fetch all token accounts owned by the user
        # ProgramId: TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
        opts = {"programId": TOKEN_PROGRAM_ID}
        response = await client.get_token_accounts_by_owner(
            wallet_pubkey,
            program_id=TOKEN_PROGRAM_ID,
            encoding="jsonParsed"
        )
        
        mints = set()
        if response.value:
            for account in response.value:
                try:
                    data = account.account.data.parsed['info']
                    mint = data['mint']
                    amount = int(data['tokenAmount']['amount'])
                    decimals = int(data['tokenAmount']['decimals'])
                    
                    # We are interested in NFTs, so amount should be > 0 (usually 1)
                    # and decimals usually 0, but let's just check ownership > 0
                    if amount > 0:
                        mints.add(mint)
                except (KeyError, TypeError):
                    continue
                    
        return mints
    except Exception as e:
        print(f"Error fetching wallet tokens: {e}")
        return set()
    finally:
        await client.close()
