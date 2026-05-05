"""Telegram Notifier untuk Polymarket Bot"""
import asyncio
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from config.settings import Config


class TelegramNotifier:
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.chat_id: Optional[str] = None
        self.enabled = False
        self._init_bot()

    def _init_bot(self):
        """Inisialisasi Telegram bot dari .env"""
        token = getattr(Config, 'TELEGRAM_BOT_TOKEN', '')
        chat_id = getattr(Config, 'TELEGRAM_CHAT_ID', '')

        if token and chat_id:
            try:
                self.bot = Bot(token=token)
                self.chat_id = chat_id
                self.enabled = True
                print(f"[Telegram] Notifier initialized | Chat: {chat_id}")
            except Exception as e:
                print(f"[Telegram] Init failed: {e}")
        else:
            print("[Telegram] Not configured - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    async def _send(self, message: str, parse_mode=ParseMode.HTML):
        """Send message async"""
        if not self.enabled or not self.bot or not self.chat_id:
            return
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"[Telegram] Send failed: {e}")

    def send(self, message: str, parse_mode=ParseMode.HTML):
        """Send message (sync wrapper)"""
        try:
            asyncio.run(self._send(message, parse_mode))
        except Exception as e:
            print(f"[Telegram] Error: {e}")

    def notify_entry(self, side: str, amount: float, odds: float, market_url: str, epoch: int):
        """Notifikasi saat entry position"""
        emoji = "🟢" if side == "UP" else "🔴"
        msg = f"""
<b>{emoji} ENTRY EXECUTED</b>

<b>Direction:</b> {side} ({'Buy YES' if side == 'UP' else 'Buy NO'})
<b>Amount:</b> ${amount:.2f}
<b>Odds:</b> ${odds:.3f}
<b>Market:</b> <a href="{market_url}">BTC Up/Down 5m-{epoch}</a>

<i>Monitoring until resolution...</i>
"""
        self.send(msg)

    def notify_exit(self, result: str, pnl: float, total_pnl: float, wins: int, losses: int, win_rate: float):
        """Notifikasi saat exit/resolved"""
        if result == "WIN":
            emoji = "🎉"
            color = "🟢"
            pnl_str = f"+${pnl:.2f}"
        else:
            emoji = "💸"
            color = "🔴"
            pnl_str = f"${pnl:.2f}"

        msg = f"""
<b>{emoji} POSITION CLOSED - {result}!</b>

<b>PnL This Trade:</b> <code>{pnl_str}</code>
<b>Total PnL:</b> <code>${total_pnl:.2f}</code>
<b>Wins:</b> {wins} | <b>Losses:</b> {losses}
<b>Win Rate:</b> {win_rate:.1f}%

{color} {'Green day!' if pnl > 0 else 'Red day, next one!'} {color}
"""
        self.send(msg)

    def notify_error(self, error_msg: str):
        """Notifikasi error critical"""
        msg = f"""
<b>🔴 BOT ERROR</b>

<code>{error_msg[:400]}</code>

<i>Check logs immediately!</i>
"""
        self.send(msg)

    def notify_scanning(self, signal: str, confidence: float, rsi: float, odds_up: float, odds_down: float):
        """Notifikasi saat scan menemukan signal valid"""
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        msg = f"""
<b>{emoji} SIGNAL DETECTED</b>

<b>Signal:</b> {signal}
<b>Confidence:</b> {confidence:.0%}
<b>RSI:</b> {rsi:.1f}
<b>Up Odds:</b> ${odds_up:.3f}
<b>Down Odds:</b> ${odds_down:.3f}

<i>Analyzing for entry...</i>
"""
        self.send(msg)

    def notify_startup(self, mode: str, balance: float):
        """Notifikasi saat bot start"""
        emoji = "🚀" if mode == "LIVE" else "🧪"
        msg = f"""
<b>{emoji} BOT STARTED</b>

<b>Mode:</b> {mode}
<b>Balance:</b> ${balance:.2f}
<b>Strategy:</b> EMA9/21 + RSI14
<b>Odds Filter:</b> 0.45-0.55

<i>Scanning for opportunities...</i>
"""
        self.send(msg)

    def notify_balance_low(self, balance: float):
        """Warning kalau balance rendah"""
        msg = f"""
<b>⚠️ LOW BALANCE WARNING</b>

Current balance: <code>${balance:.2f}</code>

Please deposit PolyUSD to continue trading.
"""
        self.send(msg)

    def notify_daily_summary(self, stats: dict, balance: float, trades_today: list):
        """Daily summary report jam 7 pagi"""
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        total_trades = len(trades_today)

        if total_trades == 0:
            msg = f"""
📊 <b>DAILY SUMMARY - {today}</b>

No trades yesterday.
Current Balance: <code>${balance:.2f}</code>

<i>Bot standing by for today's opportunities...</i>
"""
        else:
            wins_today = sum(1 for t in trades_today if t.get("result") == "WIN")
            losses_today = total_trades - wins_today
            pnl_today = sum(t.get("pnl", 0) for t in trades_today)
            win_rate_today = (wins_today / total_trades * 100) if total_trades > 0 else 0

            # Best trade
            best_trade = max(trades_today, key=lambda x: x.get("pnl", 0))
            worst_trade = min(trades_today, key=lambda x: x.get("pnl", 0))

            pnl_color = "🟢" if pnl_today >= 0 else "🔴"

            msg = f"""
📊 <b>DAILY SUMMARY - {today}</b>

<b>Trades:</b> {total_trades} ({wins_today}W / {losses_today}L)
<b>Win Rate:</b> {win_rate_today:.1f}%
<b>PnL:</b> {pnl_color} <code>${pnl_today:+.2f}</code> {pnl_color}
<b>Balance:</b> <code>${balance:.2f}</code>

<b>Best:</b> +${best_trade.get("pnl", 0):.2f} ({best_trade.get("side", "-")} @ {best_trade.get("entry_odds", 0):.2f})
<b>Worst:</b> ${worst_trade.get("pnl", 0):.2f} ({worst_trade.get("side", "-")} @ {worst_trade.get("entry_odds", 0):.2f})

<b>Total All Time:</b>
W/L: {stats.get("wins", 0)}/{stats.get("losses", 0)} | PnL: ${stats.get("total_pnl", 0):.2f} | WR: {stats.get("win_rate", 0):.1f}%

<i>Ready for today! 🚀</i>
"""
        self.send(msg)
