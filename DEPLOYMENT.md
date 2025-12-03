# Multi-Collection Deployment Guide

This bot is designed to run multiple instances simultaneously, one for each NFT collection/Discord server.

## Architecture
- **Single Codebase**: All bots run the same code.
- **Shared Database**: All bots connect to the same PostgreSQL database.
    - `FlexPlayer`: Shared wallet links (User A links wallet once, works everywhere).
    - `FlexNFT`: Shared table, separated by `collection_slug`.
    - `FlexGuildConfig`: Maps Discord Guild IDs to Collection Slugs.
- **Separate Containers**: Each bot runs in its own Docker container with its own `.env` file.
- **Hybrid Data Fetching**:
    - **Images/Ownership**: Fetched live from Solana via QuickNode RPC (Metaplex DAS API).
    - **Rarity/Rank**: Fetched from local DB (synced from HowRare.is).

## Adding a New Collection

### 1. Create Environment File
Create a new `.env.<collection_name>` file (e.g., `.env.gainz`).
```dotenv
DISCORD_BOT_TOKEN=your_new_bot_token
DISCORD_GUILD_ID=your_guild_id
DISCORD_ADMIN_ROLE=MOD
DATABASE_URL=postgresql://... (Same as others)
HOWRARE_COLLECTION=gainz
HOWRARE_API_BASE=https://api.howrare.is/v0.1
SOLANA_RPC_URL=https://your-quicknode-rpc-url.com/
```

### 2. Update Docker Compose
Add a new service to `docker-compose.yml`:
```yaml
  flexbot_gainz:
    build: .
    container_name: flexbot_gainz
    restart: unless-stopped
    network_mode: "host"
    env_file:
      - .env.gainz
    volumes:
      - ./flexbot.db:/app/flexbot.db
```

### 3. Update Deployment Script
Add the new env file to the copy list in `deploy.sh`:
```bash
scp -o StrictHostKeyChecking=no .env.gainz $SERVER_USER@$SERVER_IP:$APP_DIR/.env.gainz
```

### 4. Configure Rarity
Update `shared/rarity_config.py` to include the new collection's rarity logic in the `RARITY_CONFIGS` dictionary:
```python
    "gainz": {
        "tiers": [
            {"max_rank": 100, "name": "Legendary", "color": 0xFFD700},
            # ...
        ],
        "special_attributes": []
    }
```

### 5. Deploy
Run `./deploy.sh`.

### 6. Sync Metadata
In the new Discord server, run:
`/admin_sync_collection`
*Note: This syncs the static Rank/Rarity data from HowRare.is. Images are fetched live and do not need syncing.*
