# Core Flexbot

Core Flexbot is a lightweight, standalone Discord bot designed for Solana NFT communities. It handles user onboarding (wallet linking) and allows users to "flex" their assets in a clean, embed-based format.

## Features

*   **Wallet Management**: Link, unlink, and view Solana wallets.
*   **NFT Flexing**: Display high-quality embeds of your NFTs from a configured collection.
*   **Admin Tools**: Manually link wallets for users.

## Stack

*   **Language**: Python 3.13+
*   **Framework**: `discord.py`
*   **Database**: PostgreSQL (via SQLAlchemy)
*   **APIs**: HowRare.is

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
    ```
4.  **Run the bot**:
    ```bash
    python main.py
    ```
