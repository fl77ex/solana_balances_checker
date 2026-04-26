import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
WALLETS_FILE = "wallets.txt"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
SPL_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
REQUEST_TIMEOUT = 20


def rpc_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    response = requests.post(
        SOLANA_RPC_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    body = response.json()
    if "error" in body:
        raise requests.exceptions.RequestException(body["error"])
    return body.get("result", {})


def get_sol_balance(wallet_pubkey):
    """Return native SOL balance for a wallet."""
    result = rpc_request("getBalance", [wallet_pubkey])
    lamports = result.get("value", 0)
    return lamports / 1_000_000_000


def get_all_tokens(wallet_pubkey):
    """Return non-zero SPL token balances for a wallet."""
    result = rpc_request(
        "getTokenAccountsByOwner",
        [
            wallet_pubkey,
            {"programId": SPL_TOKEN_PROGRAM_ID},
            {"encoding": "jsonParsed"},
        ],
    )
    accounts = result.get("value", [])
    tokens = []

    for account in accounts:
        info = account["account"]["data"]["parsed"]["info"]
        token_amount = info["tokenAmount"]
        amount_raw = int(token_amount["amount"])
        if amount_raw == 0:
            continue

        decimals = int(token_amount["decimals"])
        ui_amount = amount_raw / (10 ** decimals) if decimals else amount_raw
        tokens.append(
            {
                "mint": info["mint"],
                "balance": ui_amount,
                "state": info.get("state", "unknown"),
            }
        )

    return tokens


def get_token_metadata(mint):
    """Return token metadata from Moralis when an API key is configured."""
    if not MORALIS_API_KEY:
        return {}

    url = f"https://solana-gateway.moralis.io/token/mainnet/{mint}/metadata"
    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def read_wallets(path):
    with open(path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def main():
    wallets = read_wallets(WALLETS_FILE)
    if not wallets:
        print("No wallet addresses found in wallets.txt.")
        return

    for wallet in wallets:
        print(f"\n=== Wallet: {wallet} ===")
        try:
            sol_balance = get_sol_balance(wallet)
            print(f"SOL balance: {sol_balance} SOL")

            tokens = get_all_tokens(wallet)
            if not tokens:
                print("No non-zero token balances found.")
                continue

            for token in tokens:
                mint = token["mint"]
                balance = token["balance"]
                state = token["state"]

                try:
                    metadata = get_token_metadata(mint)
                except requests.exceptions.RequestException:
                    metadata = {}

                name = metadata.get("name", "Unknown")
                symbol = metadata.get("symbol", "???")
                logo = metadata.get("logo", "No logo")

                print(
                    f"{name} ({symbol}) | Mint: {mint} | "
                    f"Balance: {balance} | State: {state} | Logo: {logo}"
                )

        except requests.exceptions.RequestException as error:
            print(f"Failed to process wallet {wallet}: {error}")


if __name__ == "__main__":
    main()
