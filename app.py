from flask import Flask, render_template_string
import requests
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
BASE_URL = "https://api.etherscan.io/v2/api"

WALLETS = {
    "WLFI Multisig Treasury": "0x5be9a4959308a0d0c7bc0870e319314d8d957dbb",
    "WLFI Token Contract": "0xda5e1988097297dcdc1f90d4dfe7909e847cbef6",
    "World Liberty Deployer": "0x97f1f8003ad0fb1c99361170310c65dc84f921e3"
}

# Known token decimals
TOKEN_DECIMALS = {
    "USDC": 6, "USDT": 6, "WBTC": 8,
    "WLFI": 18, "ETH": 18, "WETH": 18,
    "LINK": 18, "AAVE": 18, "default": 18
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>WLFI Wallet Tracker</title>
    <meta http-equiv="refresh" content="60">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0f0f0f; color: #f0f0f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 2rem; font-size: 14px; }
        h1 { color: #f0b959; font-size: 22px; font-weight: 500; margin-bottom: 4px; }
        .subtitle { color: #555; font-size: 12px; margin-bottom: 2rem; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 2.5rem; }
        .summary-card { background: #1a1a1a; border: 0.5px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 1rem 1.25rem; }
        .card-label { font-size: 11px; color: #555; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 6px; }
        .card-value { font-size: 20px; font-weight: 500; }
        .wallet-section { margin-bottom: 2.5rem; }
        .wallet-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 6px; }
        .wallet-name { font-size: 15px; font-weight: 500; color: #a89ef5; }
        .wallet-address { font-size: 11px; color: #444; }
        .wallet-stats { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
        .stat { font-size: 12px; }
        .stat-label { color: #555; }
        .stat-value { color: #f0f0f0; margin-left: 4px; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 8px 12px; color: #444; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; border-bottom: 0.5px solid #1a1a1a; }
        td { padding: 8px 12px; border-bottom: 0.5px solid #151515; color: #a0a0a0; font-size: 13px; }
        tr:hover td { background: #141414; }
        .buy { color: #7dc97d; font-weight: 500; }
        .sell { color: #f07070; font-weight: 500; }
        .transfer { color: #7ab8f5; font-weight: 500; }
        .token-badge { display: inline-block; background: #1a1a1a; border: 0.5px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 1px 6px; font-size: 11px; color: #f0b959; }
        .tx-link { color: #555; font-size: 11px; text-decoration: none; }
        .tx-link:hover { color: #7ab8f5; }
        .amount-positive { color: #7dc97d; }
        .amount-negative { color: #f07070; }
        .no-data { color: #333; padding: 1rem 12px; font-size: 13px; }
        .updated { color: #333; font-size: 11px; margin-top: 2rem; text-align: center; }
        .divider { border: none; border-top: 0.5px solid #1a1a1a; margin: 2rem 0; }
    </style>
</head>
<body>
    <h1>WLFI Wallet Tracker</h1>
    <p class="subtitle">World Liberty Financial — live on-chain monitor · auto-refreshes every 60s · Deployed via Cloud Build · {{ current_time }}</p>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="card-label">Total Transactions</div>
            <div class="card-value">{{ summary.total_txs }}</div>
        </div>
        <div class="summary-card">
            <div class="card-label">Unique Tokens</div>
            <div class="card-value">{{ summary.unique_tokens }}</div>
        </div>
        <div class="summary-card">
            <div class="card-label">Most Active Wallet</div>
            <div class="card-value" style="font-size:14px">{{ summary.most_active }}</div>
        </div>
        <div class="summary-card">
            <div class="card-label">Last Activity</div>
            <div class="card-value" style="font-size:14px">{{ summary.last_activity }}</div>
        </div>
    </div>

    {% for wallet_name, wallet_data in data.items() %}
    <div class="wallet-section">
        <div class="wallet-header">
            <span class="wallet-name">{{ wallet_name }}</span>
        </div>
        <div class="wallet-address">{{ wallets[wallet_name] }}</div>

        {% if wallet_data.error %}
            <div class="no-data">{{ wallet_data.error }}</div>
        {% else %}
        <div class="wallet-stats" style="margin-top:8px">
            <div class="stat"><span class="stat-label">Transactions:</span><span class="stat-value">{{ wallet_data.count }}</span></div>
            <div class="stat"><span class="stat-label">Tokens moved:</span><span class="stat-value">{{ wallet_data.tokens | join(', ') }}</span></div>
            <div class="stat"><span class="stat-label">Inbound:</span><span class="stat-value amount-positive">{{ wallet_data.inbound }}</span></div>
            <div class="stat"><span class="stat-label">Outbound:</span><span class="stat-value amount-negative">{{ wallet_data.outbound }}</span></div>
        </div>

        {% if wallet_data.transactions %}
        <table>
            <tr>
                <th>Time</th>
                <th>Direction</th>
                <th>Token</th>
                <th>Amount</th>
                <th>Counterparty</th>
                <th>Tx</th>
            </tr>
            {% for tx in wallet_data.transactions %}
            <tr>
                <td>{{ tx.time }}</td>
                <td class="{{ tx.direction_class }}">{{ tx.direction }}</td>
                <td><span class="token-badge">{{ tx.token }}</span></td>
                <td class="{{ 'amount-positive' if tx.direction == 'IN' else 'amount-negative' }}">{{ tx.amount_formatted }}</td>
                <td>{{ tx.counterparty }}</td>
                <td><a href="https://etherscan.io/tx/{{ tx.hash }}" target="_blank" class="tx-link">{{ tx.hash[:10] }}...</a></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <div class="no-data">No recent token transfers found</div>
        {% endif %}
        {% endif %}
    </div>
    <hr class="divider">
    {% endfor %}

    <div class="updated">Data from Etherscan API v2 · Deployed via Cloud Build · Pipeline: GCP DevOps Lab</div>
</body>
</html>
"""

def format_amount(value_raw, symbol):
    decimals = TOKEN_DECIMALS.get(symbol, TOKEN_DECIMALS["default"])
    try:
        amount = float(value_raw) / (10 ** decimals)
        if amount >= 1_000_000:
            return f"{amount/1_000_000:.2f}M {symbol}"
        elif amount >= 1_000:
            return f"{amount/1_000:.2f}K {symbol}"
        elif amount >= 1:
            return f"{amount:.4f} {symbol}"
        else:
            return f"{amount:.8f} {symbol}"
    except:
        return f"{value_raw} {symbol}"

def get_token_transfers(address, wallet_name):
    try:
        url = f"{BASE_URL}?chainid=1&module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&page=1&offset=10&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data["status"] != "1":
            # Fall back to normal transactions
            url2 = f"{BASE_URL}?chainid=1&module=account&action=txlist&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
            response2 = requests.get(url2, timeout=10)
            data2 = response2.json()
            if data2["status"] != "1":
                return {"error": f"No data found: {data.get('message', 'Unknown')}", "count": 0, "tokens": [], "inbound": 0, "outbound": 0, "transactions": []}

        raw_txs = data.get("result", [])[:20]
        address_lower = address.lower()
        transactions = []
        tokens_seen = set()
        inbound = 0
        outbound = 0

        for tx in raw_txs:
            is_in = tx.get("to", "").lower() == address_lower
            direction = "IN" if is_in else "OUT"
            direction_class = "buy" if is_in else "sell"
            symbol = tx.get("tokenSymbol", "ETH")
            tokens_seen.add(symbol)

            if is_in:
                inbound += 1
            else:
                outbound += 1

            counterparty_addr = tx.get("from") if is_in else tx.get("to", "")
            counterparty = f"{counterparty_addr[:8]}...{counterparty_addr[-6:]}" if counterparty_addr else "Unknown"

            try:
                ts = int(tx.get("timeStamp", 0))
                time_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
            except:
                time_str = "Unknown"

            transactions.append({
                "time": time_str,
                "direction": direction,
                "direction_class": direction_class,
                "token": symbol,
                "amount_formatted": format_amount(tx.get("value", "0"), symbol),
                "counterparty": counterparty,
                "hash": tx.get("hash", "")
            })

        return {
            "error": None,
            "count": len(transactions),
            "tokens": list(tokens_seen),
            "inbound": inbound,
            "outbound": outbound,
            "transactions": transactions
        }

    except Exception as e:
        logger.error(f"Error fetching data for {wallet_name}: {e}")
        return {"error": str(e), "count": 0, "tokens": [], "inbound": 0, "outbound": 0, "transactions": []}

@app.route("/")
def home():
    logger.info("Dashboard requested")
    data = {}
    total_txs = 0
    all_tokens = set()
    most_active_count = 0
    most_active_name = ""
    last_activity = "N/A"

    for name, address in WALLETS.items():
        wallet_data = get_token_transfers(address, name)
        data[name] = wallet_data
        total_txs += wallet_data.get("count", 0)
        all_tokens.update(wallet_data.get("tokens", []))
        if wallet_data.get("count", 0) > most_active_count:
            most_active_count = wallet_data["count"]
            most_active_name = name
        if wallet_data.get("transactions"):
            last_activity = wallet_data["transactions"][0]["time"]

    summary = {
        "total_txs": total_txs,
        "unique_tokens": len(all_tokens),
        "most_active": most_active_name,
        "last_activity": last_activity
    }

    return render_template_string(
        HTML_TEMPLATE,
        data=data,
        wallets=WALLETS,
        summary=summary,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    )

@app.route("/health")
def health():
    return {"status": "healthy"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)