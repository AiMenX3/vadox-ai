/**
 * Vadox License Worker
 * -------------------
 * Ersetzt die client-seitige HMAC-Lizenzpruefung (frueher in vadox/core/license.py
 * mit einem fest im Code stehenden _MASTER_SECRET). Damit das Vadox-Repo oeffentlich
 * sein kann, lebt das Secret nur noch hier als Worker-Secret, nie im Git-Repo.
 *
 * Routen:
 *   POST /checkout  { plan: "pro" | "month" }        -> { url }
 *   GET  /success?session_id=...                     -> HTML-Seite mit dem Key
 *   POST /verify    { key: "VADOX-..." }              -> { valid, type, expiry, days_left, error }
 *
 * Setup: siehe README.md in diesem Ordner.
 */

const B32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

// ── Base32 (RFC4648, wie Pythons base64.b32encode/-decode) ──────────────────
function base32Encode(bytes) {
  let bits = 0, value = 0, output = "";
  for (let i = 0; i < bytes.length; i++) {
    value = (value << 8) | bytes[i];
    bits += 8;
    while (bits >= 5) {
      output += B32_ALPHABET[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) {
    output += B32_ALPHABET[(value << (5 - bits)) & 31];
  }
  return output; // kein Padding - passt zu Pythons .rstrip("=")
}

function base32Decode(str) {
  str = str.replace(/=+$/, "").toUpperCase();
  let bits = 0, value = 0;
  const bytes = [];
  for (const char of str) {
    const idx = B32_ALPHABET.indexOf(char);
    if (idx === -1) continue;
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 0xff);
      bits -= 8;
    }
  }
  return new Uint8Array(bytes);
}

// ── HMAC-SHA256 via Web Crypto ───────────────────────────────────────────────
async function hmacSha256Hex(secret, message) {
  const enc = new TextEncoder();
  const cryptoKey = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", cryptoKey, enc.encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("").toUpperCase();
}

function constantTimeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// ── Datum-Helfer (UTC, Format YYYYMMDD wie in license.py) ────────────────────
function formatYYYYMMDD(d) {
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

function parseYYYYMMDD(s) {
  if (!/^\d{8}$/.test(s)) return null;
  const y = +s.slice(0, 4), m = +s.slice(4, 6) - 1, d = +s.slice(6, 8);
  return new Date(Date.UTC(y, m, d));
}

// ── HTTP-Helfer ───────────────────────────────────────────────────────────────
function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });
}

function html(body, status = 200) {
  return new Response(body, { status, headers: { "Content-Type": "text/html; charset=utf-8" } });
}

function renderSuccessPage(key) {
  return `<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Vadox — Kauf erfolgreich</title>
<style>
  body { font-family: 'Courier New', monospace; background:#050d1a; color:#5ab4d8; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; }
  .card { background:#071525; border:1px solid #0a2540; border-radius:12px; padding:32px; max-width:520px; text-align:center; }
  h1 { color:#00ff88; font-size:20px; }
  code { display:block; background:#0a1e35; color:#00c8ff; padding:14px; border-radius:8px; margin:16px 0; font-size:14px; word-break:break-all; user-select: all; }
  button { background:#0a2a4a; border:1px solid #00c8ff; color:#00c8ff; padding:10px 20px; border-radius:8px; cursor:pointer; font-family:inherit; }
  button:hover { background:#0f3a60; }
  p { font-size:13px; }
</style>
</head>
<body>
  <div class="card">
    <h1>&#10003; Zahlung erfolgreich</h1>
    <p>Dein Vadox-Lizenzschlüssel:</p>
    <code id="key">${key}</code>
    <button onclick="navigator.clipboard.writeText(document.getElementById('key').textContent)">In Zwischenablage kopieren</button>
    <p>Füge diesen Schlüssel in Vadox unter "Lizenzschlüssel eingeben" ein.</p>
  </div>
</body>
</html>`;
}

function renderErrorPage(message) {
  return `<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Vadox</title></head>
<body style="font-family:'Courier New',monospace;background:#050d1a;color:#ff6b9d;display:flex;align-items:center;justify-content:center;height:100vh;">
<p>${message}</p></body></html>`;
}

// ── Routen ────────────────────────────────────────────────────────────────────

async function handleCheckout(request, env) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ error: "Ungültiger Request-Body" }, 400);
  }
  const plan = body.plan === "month" ? "month" : "pro";
  const priceId = plan === "month" ? env.STRIPE_PRICE_MONTH : env.STRIPE_PRICE_PRO;
  if (!priceId) {
    return json({ error: "Preis für diesen Plan nicht konfiguriert" }, 500);
  }

  const successUrl = `${env.WORKER_BASE_URL}/success?session_id={CHECKOUT_SESSION_ID}&plan=${plan}`;
  const params = new URLSearchParams();
  params.set("mode", "payment");
  params.set("line_items[0][price]", priceId);
  params.set("line_items[0][quantity]", "1");
  params.set("success_url", successUrl);
  params.set("cancel_url", env.CANCEL_URL || "https://vadox.ai");

  const resp = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: params.toString(),
  });
  const data = await resp.json();
  if (!resp.ok) {
    return json({ error: data.error?.message || "Stripe-Fehler" }, 502);
  }
  return json({ url: data.url });
}

async function handleSuccess(url, env) {
  const sessionId = url.searchParams.get("session_id");
  if (!sessionId) return html(renderErrorPage("Fehlende session_id."), 400);

  const resp = await fetch(
    `https://api.stripe.com/v1/checkout/sessions/${sessionId}?expand[]=line_items`,
    { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
  );
  const session = await resp.json();
  if (!resp.ok) return html(renderErrorPage("Zahlungssitzung nicht gefunden."), 404);
  if (session.payment_status !== "paid") {
    return html(renderErrorPage("Zahlung ist noch nicht abgeschlossen."), 402);
  }

  // Nie dem client-kontrollierbaren ?plan=-Parameter vertrauen — den tatsaechlich
  // bezahlten Preis aus den Line-Items lesen.
  const priceId = session.line_items?.data?.[0]?.price?.id;
  let keyType, days;
  if (priceId === env.STRIPE_PRICE_MONTH) {
    keyType = "MONTH"; days = 30;
  } else if (priceId === env.STRIPE_PRICE_PRO) {
    keyType = "PRO"; days = 36500;
  } else {
    return html(renderErrorPage("Unbekanntes Produkt."), 400);
  }

  const email = (session.customer_details?.email || "").toLowerCase();
  // session.created (Stripe-Zeitstempel) statt "jetzt" verwenden, damit ein
  // Neuladen der Seite denselben Key erzeugt statt einen leicht anderen.
  const expiryDate = new Date(session.created * 1000 + days * 86400000);
  const expiryStr = formatYYYYMMDD(expiryDate);
  const payload = `${expiryStr}|${keyType}|${email}`;

  const sigHex = await hmacSha256Hex(env.VADOX_MASTER_SECRET, payload);
  const keyBody = `${sigHex.slice(0, 4)}-${sigHex.slice(4, 8)}-${sigHex.slice(8, 12)}-${sigHex.slice(12, 16)}`;
  const meta = base32Encode(new TextEncoder().encode(payload));
  const key = `VADOX-${keyBody}-${meta}`;

  return html(renderSuccessPage(key));
}

async function handleVerify(request, env) {
  let body;
  try {
    body = await request.json();
  } catch (e) {
    return json({ valid: false, error: "Ungültiger Request-Body" });
  }
  const rawKey = (body.key || "").trim().toUpperCase();
  const parts = rawKey.split("-");
  if (parts.length < 6 || parts[0] !== "VADOX") {
    return json({ valid: false, error: "Ungültiges Format" });
  }

  let payload;
  try {
    payload = new TextDecoder().decode(base32Decode(parts[5]));
  } catch (e) {
    return json({ valid: false, error: "Parse-Fehler" });
  }
  const segs = payload.split("|");
  if (segs.length !== 3) {
    return json({ valid: false, error: "Parse-Fehler" });
  }
  const [expiryStr, keyType, email] = segs;

  const expectedSigFull = await hmacSha256Hex(env.VADOX_MASTER_SECRET, payload);
  const expectedSig = expectedSigFull.slice(0, 16);
  const actualSig = `${parts[1]}${parts[2]}${parts[3]}${parts[4]}`;

  if (!constantTimeEqual(expectedSig, actualSig)) {
    return json({ valid: false, error: "Ungültige Signatur" });
  }

  const expiry = parseYYYYMMDD(expiryStr);
  if (!expiry || Date.now() > expiry.getTime()) {
    return json({ valid: false, error: `Abgelaufen am ${expiryStr}` });
  }

  const daysLeft = Math.floor((expiry.getTime() - Date.now()) / 86400000);
  return json({
    valid: true,
    type: keyType,
    expiry: `${expiry.getUTCFullYear()}-${String(expiry.getUTCMonth() + 1).padStart(2, "0")}-${String(expiry.getUTCDate()).padStart(2, "0")}`,
    days_left: daysLeft,
    email,
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      if (url.pathname === "/checkout" && request.method === "POST") {
        return await handleCheckout(request, env);
      }
      if (url.pathname === "/success" && request.method === "GET") {
        return await handleSuccess(url, env);
      }
      if (url.pathname === "/verify" && request.method === "POST") {
        return await handleVerify(request, env);
      }
      return json({ error: "Not found" }, 404);
    } catch (e) {
      return json({ error: String(e) }, 500);
    }
  },
};
