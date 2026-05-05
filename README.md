# 🤖 Polymarket BTC Up/Down 5-Minute Bot (CLOB V2)

Bot automation untuk trading market **BTC Up/Down 5 menit** di Polymarket dengan strategy **EMA 9/21 + RSI 14** dan **Odds Filter 0.45-0.55**.

> ⚠️ **IMPORTANT: Polymarket sudah migrate ke CLOB V2 per 28 April 2026.** Bot ini sudah di-update untuk support V2. Kalau masih pakai SDK lama, akan error `order_version_mismatch`.

---

## 📋 Arsitektur

```
[Private Key / EOA]
        ↓ (sign)
[Proxy Wallet / Smart Contract]
        ↓ (execute)
[Polymarket CLOB V2 / Relayer API]
```

---

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
git clone https://github.com/Jametkudasigan/polytele.git
```
```
cd polymarket-btc-bot
```
```
python -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```

### 2. Konfigurasi .env

```bash
cp .env.example .env
nano .env
```

Isi **2 variable wajib**:

```env
POLY_PRIVATE_KEY=0x_your_private_key_here
POLY_PROXY_ADDRESS=0x_your_proxy_wallet_address_here
POLY_SIGNATURE_TYPE=1
```

**Catatan:**
- `POLY_PRIVATE_KEY`: Export dari Polymarket Settings > Private Key
- `POLY_PROXY_ADDRESS`: Alamat proxy wallet tempat dana disimpan (lihat di Polymarket > Deposit)
- `POLY_SIGNATURE_TYPE`: `1` untuk Email/Magic wallet, `2` untuk Browser Proxy

API Key, Secret, dan Passphrase akan **digenerate otomatis** oleh bot dari private key.

### 3. Deposit Dana (WAJIB!)

**Polymarket V2 pakai PolyUSD (bukan USDC.e langsung).**

1. Login ke [polymarket.com](https://polymarket.com)
2. **Deposit** → Transfer USDC ke alamat proxy wallet
3. USDC akan otomatis di-convert ke **PolyUSD** (1:1)
4. Cek balance di Settings → Account

**Tanpa PolyUSD, order akan reject dengan error `not enough balance / allowance`.**

### 4. Jalankan Bot

```bash
python main.py
```

---

## 🔴 Troubleshooting

### Error: `order_version_mismatch`

**Penyebab:** SDK mengirim order format V1, tapi CLOB sekarang V2. [^29^]

**Solusi:**
```bash
pip install -U py-clob-client
# Restart bot
```

### Error: `not enough balance / allowance`

**Penyebab:** Belum deposit atau PolyUSD belum tersedia. [^29^]

**Solusi:**
1. Deposit USDC ke Polymarket (auto-convert ke PolyUSD)
2. Untuk EOA wallet: set token allowances manual di UI Polymarket
3. Untuk email wallet (type=1): allowances auto-set setelah deposit

### Error: `Unauthorized/Invalid api key`

**Penyebab:** API credentials tidak cocok dengan proxy address.

**Solusi:**
- Pastikan `POLY_PROXY_ADDRESS` benar (bukan alamat EOA)
- Pastikan `POLY_SIGNATURE_TYPE` sesuai tipe wallet

### Balance menunjukkan $0 padahal sudah deposit

- Cek apakah `POLY_PROXY_ADDRESS` sudah benar
- Cek apakah `POLY_SIGNATURE_TYPE` sesuai (1 untuk email wallet)
- Pastikan deposit sudah masuk (cek di polygonscan)

---

## 📊 Strategy

### BUY Setup
- Harga di atas EMA 21
- EMA 9 di atas EMA 21
- RSI 14 turun ke 30–55 lalu mantul naik
- Entry pas candle mulai naik lagi

### SELL Setup
- Harga di bawah EMA 21
- EMA 9 di bawah EMA 21
- RSI 14 naik ke 55–75 lalu turun
- Entry pas candle mulai turun lagi

### Odds Filter
- Entry hanya di odds **0.45 – 0.55**
- Risk/reward seimbang, tidak beli mahal / jual murah

---

## 🖥️ UI Features

- **Box layout** dengan Rich terminal UI
- **4-second cycle countdown** dengan progress bar
- **Real-time indicators** (Price, EMA9, EMA21, RSI)
- **Logs panel di bagian bawah** — color-coded dan detail
- **Win/Loss tracking** dengan PnL
- **Balance Polymarket PolyUSD** real-time
- **Market link** saat posisi aktif
- **Single refresh** per 4 detik (no spam)

---

## 🔄 Trade Flow

```
IDLE → SCANNING → ENTERING → POSITION → REDEEMING → IDLE
```

1. **IDLE**: Tunggu window 5 menit baru (30 detik sebelum start)
2. **SCANNING**: Fetch Binance klines, hitung EMA+RSI, cek odds (tiap 4 detik)
3. **ENTERING**: Pre-flight check balance + allowance, eksekusi market order FOK
4. **POSITION**: Monitor sampai market resolved (check tiap 4 detik)
5. **REDEEMING**: Hitung PnL, save history, kembali ke IDLE

---

## ⚙️ Konfigurasi Lanjutan

Edit `.env` untuk mengubah parameter:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `BOT_MODE` | `DRY_RUN` | `LIVE` untuk trading real, `DRY_RUN` untuk simulasi |
| `MAX_ENTRY` | `1.0` | Max entry per trade (USD) |
| `MIN_ODDS` | `0.45` | Batas bawah odds filter |
| `MAX_ODDS` | `0.55` | Batas atas odds filter |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimal confidence (0.0-1.0) |
| `POLYGON_RPC` | `https://polygon-rpc.com` | RPC endpoint Polygon |

---

## 🛡️ Safety Features

- **DRY_RUN mode** default: Bot berjalan tanpa eksekusi order real
- **Balance check** sebelum entry: Kalau $0, bot block entry dan kasih warning
- **Allowance check**: Cek token approval sebelum trading
- **Max entry $1**: Limit exposure per trade
- **Odds filter**: Hindari entry di odds ekstrem
- **FOK orders**: Fill-or-Kill, tidak ada partial fill yang menggantung
- **6-minute safety timeout**: Force check resolution kalau market lama resolve

---

## 📁 Struktur File

```
polymarket-btc-bot/
├── .env                  # Konfigurasi (jangan di-commit!)
├── .env.example          # Template konfigurasi lengkap
├── requirements.txt      # Dependencies
├── main.py               # Entry point
├── README.md
├── config/
│   └── settings.py       # Config loader
├── src/
│   ├── bot.py            # Main bot state machine (V2 support)
│   ├── ui.py             # Rich terminal UI (4s cycle + bottom logs)
│   ├── indicators.py     # EMA & RSI calculations
│   ├── binance_client.py # Binance API wrapper
│   ├── polymarket_client.py # Polymarket API + CLOB V2
│   ├── position_manager.py  # Trade tracking & PNL
│   └── utils.py          # Helpers (4s cycle, time, formatting)
└── data/
    └── trades.json       # Trade history (auto-generated)
```

---

## ⚠️ Disclaimer

Bot ini untuk **educational purposes**. Trading prediction markets memiliki risiko kehilangan dana. Pastikan:
- Sudah paham strategy sebelum pakai mode LIVE
- Sudah deposit PolyUSD ke wallet
- Punya cukup balance untuk trading
- Jangan trade dengan dana yang tidak sanggup hilang

---

## 📚 Referensi

- [Polymarket CLOB Client Python](https://github.com/Polymarket/py-clob-client)
- [Polymarket V2 Migration Guide](https://docs.polymarket.com/resources/v2-migration)
- [Polymarket Gamma API](https://docs.polymarket.com/api-reference)
- [Polymarket Gasless Trading](https://docs.polymarket.com/trading/gasless)
- [Binance Klines API](https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data)
