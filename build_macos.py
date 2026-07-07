"""
Vadox macOS Build-Script
Erzeugt: dist/Vadox.dmg (Installer) + dist/Vadox_macOS.zip (Fallback)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd, **kwargs):
    print(f"\n[BUILD] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"[ERROR] Fehlgeschlagen mit Code {result.returncode}")
        sys.exit(result.returncode)


def main():
    print("=" * 60)
    print("  VADOX macOS Build — .dmg Installer")
    print("=" * 60)

    # Alte Builds löschen
    for d in ["build", "dist"]:
        p = ROOT / d
        if p.exists():
            print(f"[+] Lösche altes {d}/")
            shutil.rmtree(p)

    # macOS Icon-Hinweis
    icon_icns = ROOT / "assets" / "icon.icns"
    if not icon_icns.exists():
        print("[!] Kein icon.icns gefunden. Erstelle placeholder...")
        icon_icns.parent.mkdir(exist_ok=True)

    # PyInstaller
    print("[+] Starte PyInstaller...")
    run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "vadox_macos.spec"], cwd=ROOT)

    app_path = ROOT / "dist" / "Vadox.app"
    if not app_path.exists():
        print("[ERROR] Vadox.app wurde nicht erstellt!")
        sys.exit(1)
    print(f"[+] Vadox.app erstellt")

    # DMG erstellen mit create-dmg
    dmg_path = ROOT / "dist" / "Vadox.dmg"
    create_dmg = shutil.which("create-dmg")

    if create_dmg:
        print("\n[+] Erstelle DMG mit create-dmg...")
        # Altes DMG löschen falls vorhanden
        if dmg_path.exists():
            dmg_path.unlink()

        dmg_cmd = [
            "create-dmg",
            "--volname", "Vadox",
            "--volicon", str(icon_icns) if icon_icns.exists() else "",
            "--window-pos", "200", "120",
            "--window-size", "800", "450",
            "--icon-size", "120",
            "--icon", "Vadox.app", "200", "190",
            "--hide-extension", "Vadox.app",
            "--app-drop-link", "600", "190",
            "--background", str(ROOT / "assets" / "dmg_background.png") if (ROOT / "assets" / "dmg_background.png").exists() else "",
            str(dmg_path),
            str(app_path),
        ]
        # Leere Strings entfernen
        dmg_cmd = [c for c in dmg_cmd if c]

        result = subprocess.run(dmg_cmd)
        if result.returncode == 0 and dmg_path.exists():
            dmg_mb = dmg_path.stat().st_size / 1024 / 1024
            print(f"\n{'=' * 60}")
            print(f"  BUILD ERFOLGREICH!")
            print(f"  DMG: dist/Vadox.dmg ({dmg_mb:.1f} MB)")
            print(f"{'=' * 60}")
        else:
            print("[!] DMG-Erstellung fehlgeschlagen — erstelle nur ZIP")
    else:
        print("[!] create-dmg nicht gefunden.")
        print("    Installieren mit: brew install create-dmg")
        print("    Erstelle stattdessen ZIP...")

    # ZIP als Fallback / für GitHub Actions
    print("\n[+] Erstelle ZIP: Vadox_macOS.zip")
    zip_path = ROOT / "dist" / "Vadox_macOS"
    shutil.make_archive(str(zip_path), "zip", str(ROOT / "dist"), "Vadox.app")
    zip_file = Path(str(zip_path) + ".zip")
    size_mb = zip_file.stat().st_size / 1024 / 1024
    print(f"    ZIP-Größe: {size_mb:.1f} MB")

    print(f"\n[+] Fertig! dist/Vadox.dmg und dist/Vadox_macOS.zip")


if __name__ == "__main__":
    main()
