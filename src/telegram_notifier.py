"""Telegram Notifier dengan UI Box Style"""
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
        """Notifikasi saat entry position - dengan UI Box"""
        from datetime import datetime

        # Format waktu window (5 menit dari epoch)
        window_start = datetime.fromtimestamp(epoch)
        window_end = datetime.fromtimestamp(epoch + 300)
        time_str = window_start.strftime("%b %d %I:%M-%I:%M %p ET")

        # Emoji dan warna berdasarkan side
        if side == "UP":
            emoji = "🟢"
            signal_text = "BUY UP BTC"
            buy_emoji = "🟩"
            direction = "Buy UP"
        else:
            emoji = "🔴"
            signal_text = "BUY DOWN BTC"
            buy_emoji = "🟥"
            direction = "Buy DOWN"

        msg = f"""{emoji} <b>SIGNAL DETECTED | {signal_text}</b>

<pre>
┌─────────────────────────┐
│  {time_str:<23}│
├─────────────────────────┤
│  BTC          $--,---  │
│  RSI          ---.-    │
│  {direction:<12} {buy_emoji}  │
├─────────────────────────┤
│  Entry        ${odds:.2f}     │
│  Confidence   --%       │
│  Closes in    5 min     │
├─────────────────────────┤
│  Record       0W 0L     │
└─────────────────────────┘
</pre>

<i>Entry executed: ${amount:.2f} USD</i>
<a href="{market_url}">📎 Open Market</a>
"""
        self.send(msg)

    def notify_exit(self, result: str, pnl: float, total_pnl: float, wins: int, losses: int, win_rate: float):
        """Notifikasi saat exit/resolved - dengan UI Box"""
        from datetime import datetime

        if result == "WIN":
            emoji = "🎉"
            result_text = "WIN"
            pnl_display = f"+${pnl:.2f}"
            record_emoji = "🟢"
        else:
            emoji = "💸"
            result_text = "LOSS"
            pnl_display = f"-${abs(pnl):.2f}"
            record_emoji = "🔴"

        msg = f"""{emoji} <b>POSITION CLOSED | {result_text}!</b>

<pre>
┌─────────────────────────┐
│  {datetime.now().strftime("%b %d %I:%M %p ET"):<23}│
├─────────────────────────┤
│  PnL          {pnl_display:<8}│
│  Total PnL    ${total_pnl:+.2f}    │
├─────────────────────────┤
│  Record       {wins}W {losses}L {record_emoji}  │
│  Win Rate     {win_rate:.1f}%      │
└─────────────────────────┘
</pre>

{record_emoji} {'Green trade!' if pnl > 0 else 'Red trade, next one!'} {record_emoji}
"""
        self.send(msg)

    def notify_scanning(self, signal: str, confidence: float, rsi: float, odds_up: float, odds_down: float):
        """Notifikasi saat scan menemukan signal valid - dengan UI Box"""
        from datetime import datetime

        if signal == "BUY":
            emoji = "🟢"
            signal_text = "BUY UP BTC"
            buy_emoji = "🟩"
            direction = "Buy UP"
            entry_odds = odds_up
        else:
            emoji = "🔴"
            signal_text = "BUY DOWN BTC"
            buy_emoji = "🟥"
            direction = "Buy DOWN"
            entry_odds = odds_down

        msg = f"""{emoji} <b>SIGNAL DETECTED | {signal_text}</b>

<pre>
┌─────────────────────────┐
│  {datetime.now().strftime("%b %d %I:%M %p ET"):<23}│
├─────────────────────────┤
│  BTC          $--,---  │
│  RSI          {rsi:.1f}        │
│  {direction:<12} {buy_emoji}  │
├─────────────────────────┤
│  Entry        ${entry_odds:.2f}     │
│  Confidence   {confidence*100:.0f}%       │
│  Closes in    5 min     │
├─────────────────────────┤
│  Record       0W 0L     │
└─────────────────────────┘
</pre>

<i>Analyzing for entry...</i>
"""
        self.send(msg)

    def notify_error(self, error_msg: str):
        """Notifikasi error critical"""
        msg = f"""🔴 <b>BOT ERROR</b>

<pre>
┌─────────────────────────┐
│  {datetime.now().strftime("%b %d %I:%M %p ET"):<23}│
├─────────────────────────┤
│  ERROR                    │
│  {error_msg[:30]:<23}│
└─────────────────────────┘
</pre>

<i>Check logs immediately!</i>
"""
        self.send(msg)

    def notify_startup(self, mode: str, balance: float):
        """Notifikasi saat bot start"""
        emoji = "🚀" if mode == "LIVE" else "🧪"

        msg = f"""{emoji} <b>BOT STARTED</b>

<pre>
┌─────────────────────────┐
│  🤖 BTC 5M Bot           │
├─────────────────────────┤
│  Mode         {mode:<8}│
│  Balance      ${balance:.2f}     │
├─────────────────────────┤
│  Strategy     EMA+RSI    │
│  Odds Filter  0.45-0.55 │
└─────────────────────────┘
</pre>

<i>Continuous scanning activated...</i>
"""
        self.send(msg)

    def notify_balance_low(self, balance: float):
        """Warning kalau balance rendah"""
        msg = f"""⚠️ <b>LOW BALANCE WARNING</b>

<pre>
┌─────────────────────────┐
│  ⚠️  WARNING              │
├─────────────────────────┤
│  Balance      ${balance:.2f}     │
│  Status       LOW       │
└─────────────────────────┘
</pre>

Please deposit pUSD to continue trading.
"""
        self.send(msg)

    def notify_daily_summary(self, stats: dict, balance: float, trades_today: list):
        """Daily summary report jam 7 pagi - dengan UI Box"""
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        total_trades = len(trades_today)

        if total_trades == 0:
            msg = f"""📊 <b>DAILY SUMMARY - {today}</b>

<pre>
┌─────────────────────────┐
│  📊 Daily Summary         │
├─────────────────────────┤
│  Trades       0          │
│  Balance      ${balance:.2f}     │
│  Status       NO TRADES │
└─────────────────────────┘
</pre>

<i>Bot standing by for today...</i>
"""
        else:
            wins_today = sum(1 for t in trades_today if t.get("result") == "WIN")
            losses_today = total_trades - wins_today
            pnl_today = sum(t.get("pnl", 0) for t in trades_today)
            win_rate_today = (wins_today / total_trades * 100) if total_trades > 0 else 0

            pnl_emoji = "🟢" if pnl_today >= 0 else "🔴"

            msg = f"""📊 <b>DAILY SUMMARY - {today}</b>

<pre>
┌─────────────────────────┐
│  📊 Daily Summary         │
├─────────────────────────┤
│  Trades       {total_trades}         │
│  W/L          {wins_today}W/{losses_today}L       │
│  Win Rate     {win_rate_today:.1f}%      │
├─────────────────────────┤
│  PnL          {pnl_emoji} ${pnl_today:+.2f}  │
│  Balance      ${balance:.2f}     │
└─────────────────────────┘
</pre>

<b>Total All Time:</b> {stats.get('wins', 0)}W/{stats.get('losses', 0)}L | PnL: ${stats.get('total_pnl', 0):.2f}

<i>Ready for today! 🚀</i>
"""
        self.send(msg)
