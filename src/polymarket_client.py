"""Polymarket API Client - CLOB V2 (Official API)"""
import requests
import json
from typing import Dict, Optional, Tuple

# V2 SDK: py_clob_client_v2 (underscore, bukan hyphen di import)
from py_clob_client_v2 import ClobClient
from py_clob_client_v2.clob_types import MarketOrderArgs, OrderType, BalanceAllowanceParams, AssetType
from py_clob_client_v2.order_builder.constants import BUY, SELL

from config.settings import Config


class PolymarketClient:
    def __init__(self):
        self.gamma_api = Config.GAMMA_API
        self.data_api = Config.DATA_API
        self.session = requests.Session()
        self._clob: Optional[ClobClient] = None
        self._api_creds = None

    def init_clob(self):
        """Inisialisasi CLOB V2 client - 2-step auth (L1 + L2)"""
        if self._clob is not None:
            return

        print("[Polymarket] Initializing CLOB V2 client...")
        try:
            # Step 1: L1 auth - create/derive API key dari private key
            print("[Polymarket] Step 1: L1 authentication (deriving API key)...")
            temp_client = ClobClient(
                host=Config.CLOB_HOST,
                chain_id=Config.CHAIN_ID,  # V2: chain_id (bukan chain)
                key=Config.POLY_PRIVATE_KEY,
                signature_type=Config.POLY_SIGNATURE_TYPE,
                funder=Config.POLY_PROXY_ADDRESS
            )

            # V2: create_or_derive_api_key() (bukan create_or_derive_api_creds())
            self._api_creds = temp_client.create_or_derive_api_key()
            print(f"[Polymarket] API Key derived: {self._api_creds.api_key[:20]}...")

            # Step 2: L2 auth - init client dengan credentials
            print("[Polymarket] Step 2: L2 authentication (full client)...")
            self._clob = ClobClient(
                host=Config.CLOB_HOST,
                chain_id=Config.CHAIN_ID,
                key=Config.POLY_PRIVATE_KEY,
                creds=self._api_creds,  # L2 credentials
                signature_type=Config.POLY_SIGNATURE_TYPE,
                funder=Config.POLY_PROXY_ADDRESS
            )
            print("[Polymarket] CLOB V2 client ready!")

        except Exception as e:
            print(f"[Polymarket] CLOB V2 init error: {e}")
            raise

    def get_balance(self) -> float:
        """Get pUSD (Polymarket USD) balance"""
        if self._clob is None:
            self.init_clob()
        try:
            bal = self._clob.get_balance_allowance(
                BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
            )
            return int(bal["balance"]) / 1e6
        except Exception as e:
            print(f"[Balance Error] {e}")
            return 0.0

    def check_allowance(self) -> bool:
        """Cek token allowance untuk trading V2"""
        if self._clob is None:
            self.init_clob()
        try:
            bal = self._clob.get_balance_allowance(
                BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
            )
            allowance = int(bal.get("allowance", 0)) / 1e6
            balance = int(bal.get("balance", 0)) / 1e6
            print(f"[Allowance] Balance: ${balance:.2f} | Allowance: ${allowance:.2f}")
            return allowance > 0 and balance > 0
        except Exception as e:
            print(f"[Allowance Check Error] {e}")
            return False

    def discover_market(self, epoch: int) -> Optional[Dict]:
        """Discover BTC Up/Down 5m market dari Gamma API"""
        url = f"{self.gamma_api}/events"
        offsets = [0, -300, 300]

        for offset in offsets:
            test_epoch = epoch + offset
            test_slug = f"btc-updown-5m-{test_epoch}"
            try:
                resp = self.session.get(url, params={"slug": test_slug}, timeout=10)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if not data or len(data) == 0:
                    continue

                event = data[0]
                market = event.get("markets", [{}])[0]
                if not market:
                    continue

                token_ids = json.loads(market.get("clobTokenIds", "[]"))
                outcomes = json.loads(market.get("outcomes", "[]"))
                outcome_prices = json.loads(market.get("outcomePrices", "[]"))

                up_idx = outcomes.index("Up") if "Up" in outcomes else -1
                down_idx = outcomes.index("Down") if "Down" in outcomes else -1

                if up_idx == -1 or down_idx == -1 or len(token_ids) < 2:
                    continue

                return {
                    "epoch": test_epoch,
                    "slug": test_slug,
                    "condition_id": market.get("conditionId"),
                    "market_id": market.get("id"),
                    "question": event.get("title", ""),
                    "up_token_id": token_ids[up_idx],
                    "down_token_id": token_ids[down_idx],
                    "up_price": float(outcome_prices[up_idx]) if up_idx < len(outcome_prices) else 0.5,
                    "down_price": float(outcome_prices[down_idx]) if down_idx < len(outcome_prices) else 0.5,
                    "end_time": market.get("endDate"),
                    "url": f"https://polymarket.com/event/{test_slug}",
                }
            except Exception:
                continue

        return None

    def get_market_preview(self, slug: str) -> dict:
        """Fetch preview data for upcoming market"""
        url = f"{self.gamma_api}/events"
        try:
            resp = self.session.get(url, params={"slug": slug}, timeout=5)
            if resp.status_code != 200:
                return {"found": False, "slug": slug}
            data = resp.json()
            if not data or len(data) == 0:
                return {"found": False, "slug": slug}

            event = data[0]
            market = event.get("markets", [{}])[0]
            if not market:
                return {"found": False, "slug": slug}

            outcomes = json.loads(market.get("outcomes", "[]"))
            outcome_prices = json.loads(market.get("outcomePrices", "[]"))

            up_idx = outcomes.index("Up") if "Up" in outcomes else -1
            down_idx = outcomes.index("Down") if "Down" in outcomes else -1

            return {
                "found": True,
                "slug": slug,
                "up_price": float(outcome_prices[up_idx]) if up_idx >= 0 and up_idx < len(outcome_prices) else None,
                "down_price": float(outcome_prices[down_idx]) if down_idx >= 0 and down_idx < len(outcome_prices) else None,
                "volume": market.get("volume", 0),
                "liquidity": market.get("liquidity", 0),
            }
        except Exception:
            return {"found": False, "slug": slug}

    def get_odds(self, token_id: str) -> float:
        """Get midpoint price untuk token"""
        if self._clob is None:
            self.init_clob()
        try:
            mid = self._clob.get_midpoint(token_id)
            return float(mid.get("mid", 0.5))
        except Exception:
            return 0.5

    def place_market_order(self, token_id: str, amount: float, side: str) -> Dict:
        """Place FOK market order ke CLOB V2"""
        if self._clob is None:
            self.init_clob()

        side_const = BUY if side.upper() == "BUY" else SELL

        try:
            # V2: create_and_post_market_order dengan order_args + options + order_type
            from py_clob_client_v2.clob_types import PartialCreateOrderOptions

            resp = self._clob.create_and_post_market_order(
                order_args=MarketOrderArgs(
                    token_id=token_id,
                    amount=amount,
                    side=side_const,
                    order_type=OrderType.FOK
                ),
                options=PartialCreateOrderOptions(tick_size="0.01"),
                order_type=OrderType.FOK
            )
            return {"success": True, "data": resp}

        except Exception as e:
            err_str = str(e)
            if "order_version_mismatch" in err_str.lower():
                return {
                    "success": False,
                    "errorMsg": "CLOB V1/V2 version mismatch. Ensure py-clob-client-v2 is installed.",
                    "raw_error": err_str
                }
            return {"success": False, "errorMsg": err_str}

    def check_market_resolved(self, slug: str) -> Tuple[bool, Optional[str]]:
        """Check apakah market sudah resolved"""
        url = f"{self.gamma_api}/events"
        try:
            resp = self.session.get(url, params={"slug": slug}, timeout=10)
            if resp.status_code != 200:
                return False, None
            data = resp.json()
            if not data:
                return False, None

            event = data[0]
            market = event.get("markets", [{}])[0]

            if market.get("closed", False) or market.get("resolved", False):
                winner = None
                outcome_prices = json.loads(market.get("outcomePrices", "[]"))
                outcomes = json.loads(market.get("outcomes", "[]"))
                for i, price in enumerate(outcome_prices):
                    if float(price) >= 0.99:
                        winner = outcomes[i] if i < len(outcomes) else None
                        break
                return True, winner

            return False, None
        except Exception:
            return False, None
