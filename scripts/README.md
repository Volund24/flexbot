# Utility Scripts

This directory contains scripts for maintaining, debugging, and verifying the FlexBot installation.

## `debug_rpc.py`
**Purpose**: Verifies the connection to the Solana RPC and checks if it supports the Metaplex Digital Asset Standard (DAS) API.
**Usage**:
```bash
python scripts/debug_rpc.py
```
**Env Vars**: Requires `SOLANA_RPC_URL` to be set in your environment or `.env` file.

## `sync_db_manual.py`
**Purpose**: Manually triggers a synchronization of collection metadata (Rank, Rarity) from HowRare.is to the local PostgreSQL database.
**Usage**:
```bash
python scripts/sync_db_manual.py
```
**Env Vars**: Requires `DATABASE_URL`, `HOWRARE_API_BASE`, and `HOWRARE_COLLECTION`.

## `check_images.py`
**Purpose**: Audits the database for broken image URLs. It fetches a sample of NFTs from the DB and checks if their image links return a 200 OK status.
**Usage**:
```bash
python scripts/check_images.py
```
**Env Vars**: Requires `DATABASE_URL`.
