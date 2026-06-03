# Morning Nifty 50 Web Push (8 AM IST)

Daily browser notification listing **Nifty 50 stocks that moved ≥2%** vs the previous session close (Yahoo/NSE-aligned data). Replaces the old WhatsApp `wa.me` flow.

## Setup (one time)

### 1. Generate VAPID keys

```powershell
cd crypto_levels_bhushan\backend
..\..\..venv\Scripts\python.exe generate_vapid_keys.py
```

Add to environment before starting the backend:

- `VAPID_SUBJECT=mailto:your@email.com`
- `VAPID_PUBLIC_KEY=<base64url from script>`
- `VAPID_PRIVATE_KEY=<PEM block from script>` (or single line with `\n` for newlines)

### 2. Start backend

```powershell
cd crypto_levels_bhushan\backend
python main.py
```

On startup you should see: `[MORNING PUSH] Scheduler active — 8:00 AM IST daily`

If VAPID is missing: `[MORNING PUSH] VAPID_PRIVATE_KEY not set — scheduler disabled`

### 3. Enable on the website

1. Log in to Crypto Levels frontend
2. Open the notification bell menu (navbar)
3. Scroll to **Morning Nifty 50 (8 AM IST)**
4. Click **Enable & test notifications**
5. Allow browser permission → local test notification appears
6. Click **Send test push** to verify server → service worker delivery

### 4. Install as PWA (recommended)

Chrome: menu → **Install Crypto Levels** (or Add to Home Screen on mobile).

Web Push when the app is closed requires HTTPS in production and a subscribed push registration.

## API routes

| Route | Description |
|--------|-------------|
| `GET /api/push/vapid-public-key` | Public key for subscribe |
| `POST /api/push/subscribe` | Save push subscription (Bearer token required) |
| `DELETE /api/push/unsubscribe` | Remove subscription |
| `POST /api/push/test` | Test push to current user |
| `GET /api/market/morning-nifty-preview` | Preview message body |

## Operational notes

- **Backend must be running at 8:00 AM IST** for the scheduled broadcast (same machine as `python main.py`).
- Each user only receives pushes for **their own** subscription (JWT `user_id`).
- Duplicate sends on the same day are skipped if the server restarts at 8:00.
- **iOS:** Web Push needs the installed PWA on iOS 16.4+.

## Troubleshooting

| Issue | Fix |
|--------|-----|
| 503 on subscribe | Set VAPID keys and restart backend |
| Test push 404 | Enable alerts first (subscribe) |
| No 8 AM notification | Check backend was up at 8 AM; check `push_subscriptions` in Mongo |
| Permission denied | Browser site settings → allow notifications |
