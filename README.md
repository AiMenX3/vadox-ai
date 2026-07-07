# 🤖 Vadox — dein persönlicher KI-Desktop-Assistent

> Inspiriert von JARVIS aus Iron Man 🦾 — Vadox hört zu ("Hey Jarvis"), redet mit dir, steuert deinen PC, schreibt Code, surft für dich im Web und lernt sogar neue Fähigkeiten von selbst.

✨ **Was Vadox kann:**
- 🎙️ Sprachsteuerung per Wake-Word ("Hey Jarvis") — kein Knopfdruck nötig
- 💬 Chat mit Claude, GPT, Gemini, OpenRouter (200+ Modelle) oder lokal mit Ollama
- 🖥️ PC steuern: Lautstärke, Dateien, Apps öffnen, Screenshots, System-Infos
- 👨‍💻 Eingebauter Coding-Assistent für viele Programmiersprachen
- 🌐 Web-Automatisierung & Websuche
- 📧 E-Mail, Kalender, Smart-Home, Übersetzer, Gesichtserkennung u.v.m.
- 🛠️ Selbstlernend: Vadox kann sich bei Bedarf eigene neue Tools schreiben
- 🖥️ Läuft auf **Windows**, **macOS** und **Linux**

---

## 🚀 Installation

Wähle dein Betriebssystem:

<details>
<summary><b>🪟 Windows</b></summary>

```bash
git clone https://github.com/AiMenX3/vadox-ai.git
cd vadox-ai
pip install -r requirements.txt
python main.py
```

Voraussetzung: [Python 3.11+](https://www.python.org/downloads/) (beim Installieren "Add to PATH" anhaken ✅) und [Git](https://git-scm.com/downloads).

</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
# Homebrew installieren, falls noch nicht vorhanden:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Benötigte Systempakete:
brew install portaudio ffmpeg

git clone https://github.com/AiMenX3/vadox-ai.git
cd vadox-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_macos.txt   # Apple Silicon (M1/M2/M3/M4)
# ODER für Intel-Macs:
# pip install -r requirements_macos_intel.txt

python main.py
```

**Wichtig für macOS:** Für Bildschirmzugriff/Computer-Steuerung müssen unter *Systemeinstellungen → Datenschutz & Sicherheit* die Berechtigungen **Bildschirmaufnahme** und **Bedienungshilfen** für dein Terminal (bzw. Python) aktiviert werden.

</details>

<details>
<summary><b>🐧 Linux</b></summary>

```bash
sudo apt install python3-pip portaudio19-dev ffmpeg libgl1 libasound2-dev

git clone https://github.com/AiMenX3/vadox-ai.git
cd vadox-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_linux.txt

python main.py
```

</details>

---

## 🔑 Erste Schritte

1. Beim ersten Start startet automatisch dein **24h-Gratis-Trial** ⏱️
2. Trag im Chat-Fenster einen API-Key ein (Claude, OpenAI, Gemini oder OpenRouter) — Anleitung dazu direkt in der App verlinkt
3. Sag **"Hey Jarvis"** oder klick aufs Mikrofon 🎙️ und leg los!

Nach Ablauf des Trials kannst du Vadox dauerhaft freischalten (PRO Lifetime oder 1-Monats-Lizenz) — der Kauf läuft direkt aus der App heraus.

---

## 🛠️ Tech-Stack

Python 3.11 · PyQt6 · Anthropic/OpenAI/Google-APIs · openWakeWord · Edge-TTS/ElevenLabs · SpeechRecognition

## 🤝 Mitmachen

Issues, Pull Requests und Ideen sind willkommen! Wenn dir Vadox gefällt, gib dem Repo gerne einen ⭐.

## 📄 Lizenz

Trial kostenlos nutzbar, danach kostenpflichtige Freischaltung (PRO Lifetime / 1 Monat) über die App.
