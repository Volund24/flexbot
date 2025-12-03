# Core Flexbot

Core Flexbot is a lightweight, standalone Discord bot designed for Solana NFT communities. It handles user onboarding (wallet linking) and allows users to "flex" their assets in a clean, embed-based format.

## Features

*   **Wallet Management**: Link, unlink, and view Solana wallets.
*   **NFT Flexing**: Display high-quality embeds of your NFTs from a configured collection.
*   **Live Data**: Fetches NFT ownership and images live from the Solana Blockchain via RPC (Metaplex DAS).
*   **Rarity Integration**: Maps ranks to custom rarity tiers and colors using local configuration.
*   **Admin Tools**: Manually link wallets for users and sync collection metadata.

## Stack

*   **Language**: Python 3.11+
*   **Framework**: `discord.py`
*   **Database**: PostgreSQL (via SQLAlchemy)
*   **Blockchain**: Solana RPC (QuickNode / Metaplex DAS API)
*   **External Data**: HowRare.is (for Rank/Rarity metadata)

## Project Structure

```
.
├── cogs/               # Discord Bot Extensions (Features)
│   ├── admin.py        # Admin commands (sync, link)
│   ├── flex.py         # Main /flex command logic
│   ├── help.py         # Help command
│   └── wallet.py       # Wallet management commands
├── scripts/            # Utility scripts for maintenance/debugging
│   ├── check_images.py # Verify image URLs
│   ├── debug_rpc.py    # Test RPC connection
│   └── sync_db_manual.py # Manual DB sync tool
├── shared/             # Shared utilities and models
│   ├── database.py     # SQLAlchemy models and session handling
│   ├── rarity_config.py# Centralized rarity tier configuration
│   └── solana_utils.py # Solana RPC interaction (DAS API)
├── main.py             # Entry point
└── docker-compose.yml  # Multi-container deployment config
```

## Setup

1.  **Clone the repository**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Environment**:
    Create a `.env` file with the following:
    ```dotenv
    DISCORD_BOT_TOKEN=your_token
    DISCORD_GUILD_ID=your_guild_id
    DISCORD_ADMIN_ROLE=Admin
    DATABASE_URL=postgresql://user:pass@host:port/dbname
    HOWRARE_COLLECTION=the_growerz
    HOWRARE_API_BASE=https://api.howrare.is/v0.1
    SOLANA_RPC_URL=https://your-quicknode-rpc-url.com/
    ```
4.  **Run the bot**:
    ```bash
    python main.py
    ```

## Utility Scripts

The `scripts/` directory contains tools for maintaining the bot:

*   `debug_rpc.py`: Verifies that the configured `SOLANA_RPC_URL` is working and supports the Metaplex DAS API.
*   `sync_db_manual.py`: Manually triggers a collection sync from HowRare.is to the local database.
*   `check_images.py`: Checks a sample of NFTs in the database to ensure their image URLs are valid.

