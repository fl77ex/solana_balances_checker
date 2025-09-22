import os
import json
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
WALLETS_FILE = "wallets.txt"

SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

def get_sol_balance(wallet_pubkey):
    """Получаем баланс SOL для кошелька"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_pubkey]
    }
    resp = requests.post(SOLANA_RPC_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    resp.raise_for_status()
    result = resp.json().get("result", {})
    lamports = result.get("value", 0)
    return lamports / 1_000_000_000  # Конвертируем lamports в SOL

def get_all_tokens(wallet_pubkey):
    """Получаем все токен-аккаунты на кошельке через Solana RPC"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_pubkey,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
    }
    resp = requests.post(SOLANA_RPC_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    resp.raise_for_status()
    accounts = resp.json().get("result", {}).get("value", [])
    tokens = []
    for acc in accounts:
        info = acc["account"]["data"]["parsed"]["info"]
        mint = info["mint"]
        amount_raw = int(info["tokenAmount"]["amount"])
        decimals = int(info["tokenAmount"]["decimals"])
        ui_amount = amount_raw / (10 ** decimals) if decimals else amount_raw
        state = info.get("state", "unknown")
        tokens.append({
            "mint": mint,
            "balance": ui_amount,
            "state": state
        })
    return tokens

def get_token_metadata(mint):
    """Получаем метаданные токена через Moralis API"""
    url = f"https://solana-gateway.moralis.io/token/mainnet/{mint}/metadata"
    headers = {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def main():
    with open(WALLETS_FILE, "r", encoding="utf-8") as f:
        wallets = [line.strip() for line in f if line.strip()]

    for wallet in wallets:
        print(f"\n=== Кошелек: {wallet} ===")
        try:
            sol_balance = get_sol_balance(wallet)
            print(f"SOL баланс: {sol_balance} SOL")

            tokens = get_all_tokens(wallet)
            if not tokens:
                print("Нет токенов на кошельке")
                continue

            for token in tokens:
                mint = token["mint"]
                balance = token["balance"]
                state = token["state"]
                try:
                    metadata = get_token_metadata(mint)
                    name = metadata.get("name", "Unknown")
                    symbol = metadata.get("symbol", "???")
                    logo = metadata.get("logo", "No logo")
                except requests.exceptions.RequestException:
                    name = "Unknown"
                    symbol = "???"
                    logo = "No logo"

                print(f"{name} ({symbol}) | Mint: {mint} | Баланс: {balance} | Состояние: {state} | Логотип: {logo}")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при обработке кошелька {wallet}: {e}")

if __name__ == "__main__":
    main()
