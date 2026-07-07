"""
Vadox Phone Link — lokaler Webserver für Handy-Steuerung
"""
import socket
import threading
import json
import queue
from datetime import datetime

_server_thread: threading.Thread | None = None
_running = False
_port = 7432
_message_queue: queue.Queue = queue.Queue()  # Nachrichten vom Handy an Vadox
_response_queue: queue.Queue = queue.Queue() # Antworten von Vadox ans Handy
_on_message_callback = None


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_url() -> str:
    return f"http://{get_local_ip()}:{_port}"


def get_qr_image():
    import qrcode
    from PIL import Image
    url = get_url()
    qr = qrcode.QRCode(version=1, box_size=6, border=3,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00c8ff", back_color="#050d1a")
    return img, url


def send_response(text: str):
    """Vadox sendet Antwort ans Handy."""
    _response_queue.put({"text": text, "time": datetime.now().strftime("%H:%M")})


def _build_html() -> str:
    return """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Vadox</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #050d1a; color: #5ab4d8; font-family: 'Courier New', monospace;
         display: flex; flex-direction: column; height: 100vh; }
  header { background: #071525; border-bottom: 1px solid #0a2540; padding: 12px 16px;
           display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  header .v { color: #00c8ff; font-size: 22px; font-weight: bold; }
  header .title { color: #00c8ff; font-size: 13px; letter-spacing: 2px; }
  header .dot { width: 8px; height: 8px; background: #00ff88; border-radius: 50%;
                margin-left: auto; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  #chat { flex: 1; overflow-y: auto; padding: 12px; display: flex;
          flex-direction: column; gap: 8px; }
  .bubble { max-width: 85%; padding: 10px 14px; border-radius: 12px; font-size: 13px;
            line-height: 1.5; word-break: break-word; }
  .user { background: #0a2a4a; border: 1px solid #1a4a7a; color: #00c8ff;
          align-self: flex-end; border-radius: 12px 12px 2px 12px; }
  .ai   { background: #071525; border: 1px solid #0a3060; color: #5ab4d8;
          align-self: flex-start; border-radius: 2px 12px 12px 12px; }
  .time { font-size: 9px; color: #0a3a5a; margin-top: 4px; }
  footer { background: #071525; border-top: 1px solid #0a2540; padding: 10px 12px;
           display: flex; gap: 8px; flex-shrink: 0; }
  #msg  { flex: 1; background: #050d1a; border: 1px solid #1a3a5a; color: #00c8ff;
          font-family: 'Courier New', monospace; font-size: 13px; border-radius: 8px;
          padding: 10px 12px; outline: none; }
  #msg:focus { border-color: #00c8ff; }
  #send { background: #0a2a4a; border: 1px solid #00c8ff; color: #00c8ff;
          width: 44px; height: 44px; border-radius: 8px; font-size: 18px; cursor: pointer; }
  #send:active { background: #1a4a7a; }
  .quick-bar { display: flex; gap: 6px; padding: 6px 12px; overflow-x: auto;
               flex-shrink: 0; scrollbar-width: none; }
  .quick-bar::-webkit-scrollbar { display: none; }
  .qbtn { background: #071525; border: 1px solid #0a2540; color: #0a4a6a;
          font-family: 'Courier New'; font-size: 10px; padding: 5px 10px;
          border-radius: 6px; white-space: nowrap; cursor: pointer; }
  .qbtn:active { border-color: #00c8ff; color: #00c8ff; }
</style>
</head>
<body>
<header>
  <span class="v">V</span>
  <span class="title">VADOX</span>
  <span class="dot"></span>
</header>
<div class="quick-bar">
  <button class="qbtn" onclick="send('Wetter heute')">Wetter</button>
  <button class="qbtn" onclick="send('Meine E-Mails')">E-Mails</button>
  <button class="qbtn" onclick="send('Heutige Termine')">Termine</button>
  <button class="qbtn" onclick="send('System-Info')">System</button>
  <button class="qbtn" onclick="send('Screenshot')">Screenshot</button>
</div>
<div id="chat">
  <div class="bubble ai">
    Hallo! Ich bin Vadox. Du bist mit deinem PC verbunden.
    <div class="time">Jetzt verbunden</div>
  </div>
</div>
<footer>
  <input id="msg" type="text" placeholder="Nachricht an Vadox..." autocomplete="off">
  <button id="send" onclick="sendMsg()">➤</button>
</footer>
<script>
const chat = document.getElementById('chat');
const msg  = document.getElementById('msg');

function addBubble(text, isUser, time) {
  const d = document.createElement('div');
  d.className = 'bubble ' + (isUser ? 'user' : 'ai');
  d.innerHTML = text.replace(/\\n/g,'<br>') +
    '<div class="time">' + (time || new Date().toLocaleTimeString('de',{hour:'2-digit',minute:'2-digit'})) + '</div>';
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}

function send(text) { msg.value = text; sendMsg(); }

function sendMsg() {
  const text = msg.value.trim();
  if (!text) return;
  addBubble(text, true);
  msg.value = '';
  fetch('/send', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: text})
  }).then(r => r.json()).then(d => {
    if (d.ok) pollResponse();
  });
}

function pollResponse() {
  const maxTries = 60;
  let tries = 0;
  const iv = setInterval(() => {
    tries++;
    fetch('/response').then(r => r.json()).then(d => {
      if (d.text) {
        addBubble(d.text, false, d.time);
        clearInterval(iv);
      } else if (tries >= maxTries) {
        addBubble('Keine Antwort erhalten.', false);
        clearInterval(iv);
      }
    });
  }, 1500);
}

msg.addEventListener('keydown', e => { if (e.key === 'Enter') sendMsg(); });
</script>
</body>
</html>"""


def _run_server():
    from flask import Flask, request, jsonify, Response
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    @app.route("/")
    def index():
        return Response(_build_html(), mimetype="text/html")

    @app.route("/send", methods=["POST"])
    def recv():
        data = request.get_json(silent=True) or {}
        msg = data.get("message", "").strip()
        if msg and _on_message_callback:
            _on_message_callback(msg)
        return jsonify({"ok": True})

    @app.route("/response")
    def response():
        try:
            item = _response_queue.get_nowait()
            return jsonify(item)
        except queue.Empty:
            return jsonify({"text": None})

    app.run(host="0.0.0.0", port=_port, debug=False, use_reloader=False)


def start(on_message=None):
    global _running, _server_thread, _on_message_callback
    if _running:
        return
    _on_message_callback = on_message
    _running = True
    _server_thread = threading.Thread(target=_run_server, daemon=True)
    _server_thread.start()
