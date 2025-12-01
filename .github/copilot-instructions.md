# FlexBot Development Instructions

## Architecture Overview
- **Framework**: Python `discord.py` with `app_commands` (Slash Commands).
- **Database**: PostgreSQL via SQLAlchemy (`shared/database.py`).
- **Modular Design**: Features are split into Cogs in `cogs/` directory.
- **External API**: Integrates with HowRare.is for NFT ownership and metadata.

## Core Components
- **`main.py`**: Entry point. Handles bot startup, extension loading, and command syncing.
- **`shared/database.py`**: Database models (`FlexPlayer`, `FlexNFT`, `FlexGuildConfig`) and session management.
- **`cogs/flex.py`**: Main "flex" functionality.
    - **Hybrid Data Fetching**: Fetches *ownership* live from HowRare.is API, but relies on *local DB* for NFT metadata (rank, image).
    - **Rarity Logic**: Contains specific business logic for mapping Rank -> Color/Status (Mythic, Epic, etc.).

## Developer Workflows
- **Database Management**:
    - Always use `get_session()` to create a session.
    - **CRITICAL**: Always close sessions in a `finally` block to prevent connection leaks.
    - Example:
      ```python
      session = get_session()
      try:
          # ... operations ...
          session.commit()
      finally:
          session.close()
      ```
- **Command Syncing**:
    - Commands are synced **globally** to support multi-guild usage.
    - Global sync takes up to 1 hour to propagate to all servers.
    - Guild-specific sync is disabled by default but can be enabled for local debugging.

## Project-Specific Conventions
- **NFT Rarity Tiers**:
    - Gold/1/1: Rank 1 or "Signed" attribute.
    - Mythic: Rank 1-71.
    - Epic: Rank 72-361.
    - Rare: Rank 362-843.
    - Uncommon: Rank 844-1446.
    - Common: Rank > 1446.
- **Embed Formatting**:
    - **Title**: NFT Name (without Rank).
    - **Thumbnail**: User's Discord profile picture.
    - **Fields**:
        1. **Rank**: The NFT Rank (e.g., "#123").
        2. **Rarity**: The Rarity Status (e.g., "Mythic", "Epic").
        3. **Owned**: Number of NFTs owned by the user.
    - **Image**: The NFT image.
    - **Note**: Do NOT show individual attributes in the flex embed.

## Environment Setup
- Ensure `.env` contains:
    - `DISCORD_BOT_TOKEN`
    - `DATABASE_URL`
    - `HOWRARE_API_BASE`
    - `HOWRARE_COLLECTION`
