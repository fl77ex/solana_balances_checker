# Solana Balances Checker

Small CLI script for checking SOL and SPL token balances for one or more Solana wallets.

The script:
- reads wallet addresses from `wallets.txt`
- fetches the native SOL balance through the public Solana RPC
- fetches SPL token accounts for each wallet
- optionally enriches token data with name, symbol, and logo from Moralis

## Requirements

- Python 3.10+
- packages from `requirements.txt`

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create your environment file:

```bash
copy .env.example .env
```

3. If you want token metadata, put your Moralis API key into `.env`:

```env
MORALIS_API_KEY=your_api_key
```

Without a Moralis API key, the script will still show SOL balances and token mint addresses, but token metadata may be unavailable.

4. Add wallet addresses to `wallets.txt`, one address per line.

## Usage

Run:

```bash
python solana_balances_checker.py
```

## Output

For each wallet, the script prints:
- SOL balance
- token mint address
- token balance
- token account state
- token name, symbol, and logo URL when metadata is available

## Notes

- The script uses the public Solana mainnet RPC endpoint.
- Zero-balance token accounts are skipped to keep the output clean.
- If a metadata request fails, the script continues and prints fallback values.
