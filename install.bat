@echo off
echo ============================================
echo   VADOX - Abhängigkeiten werden installiert
echo ============================================
echo.

python -m pip install --upgrade pip
pip install PyQt6 psutil anthropic edge-tts SpeechRecognition pyaudio pygame requests

echo.
echo ============================================
echo   Installation abgeschlossen!
echo   Starte mit: python main.py
echo ============================================
pause
