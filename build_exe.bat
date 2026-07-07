@echo off
echo ============================================
echo   VADOX - Build gestartet
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Alte Build-Dateien loeschen...
if exist dist\Vadox rmdir /s /q dist\Vadox
if exist build\Vadox rmdir /s /q build\Vadox

echo [2/3] EXE wird erstellt (dauert 2-5 Minuten)...
pyinstaller vadox.spec --noconfirm --clean

echo.
if exist dist\Vadox\Vadox.exe (
    echo [3/3] ERFOLGREICH!
    echo.
    echo  Vadox.exe liegt in: dist\Vadox\
    echo  Den gesamten Ordner dist\Vadox an Kunden schicken.
    echo.
    explorer dist\Vadox
) else (
    echo [FEHLER] Build fehlgeschlagen. Siehe Ausgabe oben.
)

pause
