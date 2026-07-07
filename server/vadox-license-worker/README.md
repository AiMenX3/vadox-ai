# Vadox License Worker

Kleiner Cloudflare Worker, der die Lizenzprüfung übernimmt, damit das
`_MASTER_SECRET` nicht mehr im (öffentlichen) Vadox-Repo liegen muss.

Ersetzt:
- die 4 statischen Stripe-Payment-Links in der Desktop-App durch dynamische
  Stripe-Checkout-Sessions (`POST /checkout`)
- die lokale HMAC-Prüfung (`_verify_local_key`) durch eine Server-Anfrage
  (`POST /verify`)
- das manuelle `generate_key.py`-Ausführen nach jedem Verkauf durch
  automatische Key-Anzeige direkt nach der Zahlung (`GET /success`)

## Einmaliges Setup

Diese Schritte machst du selbst in deinem eigenen Terminal — trag hier nirgends
Zugangsdaten in den Chat mit dem Assistenten ein.

```bash
npm install -g wrangler
wrangler login                      # oeffnet Browser, eigener Cloudflare-Account
cd server/vadox-license-worker

# Geheime Werte setzen (werden NICHT ins Repo geschrieben):
wrangler secret put STRIPE_SECRET_KEY      # erst sk_test_... zum Testen
wrangler secret put VADOX_MASTER_SECRET    # frisch erzeugen, z.B.:  openssl rand -hex 32

# Lokal testen:
wrangler dev

# Deployen:
wrangler deploy
```

Nach dem ersten Deploy zeigt `wrangler` die zugewiesene `*.workers.dev`-URL an —
trag sie in `wrangler.toml` unter `WORKER_BASE_URL` ein und deploye erneut,
damit die Stripe-`success_url` korrekt zurückführt.

## Stripe-Produkte anlegen

Im Stripe-Dashboard (erst im **Test-Modus**):
1. Zwei Preise anlegen: "Vadox PRO Lifetime" (197 €, einmalig), "Vadox 1 Monat"
   (67 €, einmalig)
2. Die jeweiligen Price-IDs (`price_...`) in `wrangler.toml` bei
   `STRIPE_PRICE_PRO` / `STRIPE_PRICE_MONTH` eintragen, erneut deployen

## End-to-End-Test (Stripe Test-Modus)

1. Vadox lokal starten (`python main.py`), auf einen Kauf-Button klicken
2. Es sollte eine Stripe-Checkout-Seite im Browser aufgehen
3. Mit Test-Karte `4242 4242 4242 4242` (beliebiges Datum/CVC) bezahlen
4. Auf der Erfolgsseite erscheint der generierte `VADOX-...`-Key
5. Key in Vadox unter "Lizenzschlüssel eingeben" einfügen — sollte über
   `/verify` akzeptiert werden

## Live schalten

Erst wenn Schritt oben komplett funktioniert:
```bash
wrangler secret put STRIPE_SECRET_KEY   # jetzt sk_live_...
wrangler deploy
```
Und die Price-IDs in `wrangler.toml` auf die Live-Mode-Preise umstellen.

## Wichtig

Es gibt aktuell **keine** Sperrliste für erstattete Zahlungen — ein einmal
ausgegebener Key bleibt gültig, auch wenn die Zahlung später zurückerstattet
wird. Für v1 bewusst so gelassen (identisch zum bisherigen Verhalten lokaler
Keys), spätere Erweiterung möglich (z.B. via Cloudflare KV als Sperrliste).
