"""
Vadox Linux Build-Script
Erzeugt: dist/Vadox.AppImage + dist/Vadox_Linux.zip
"""
import sys
import shutil
import subprocess
import os
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd, **kwargs):
    print(f"\n[BUILD] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"[ERROR] Fehlgeschlagen mit Code {result.returncode}")
        sys.exit(result.returncode)


def create_appimage():
    """Erstellt eine AppImage-Datei aus dem PyInstaller-Output."""
    dist_dir  = ROOT / "dist" / "Vadox"
    appdir    = ROOT / "dist" / "Vadox.AppDir"

    # AppDir-Struktur aufbauen
    print("\n[+] Erstelle AppDir-Struktur...")
    if appdir.exists():
        shutil.rmtree(appdir)
    appdir.mkdir(parents=True)

    # Vadox-Dateien ins AppDir kopieren
    shutil.copytree(str(dist_dir), str(appdir / "usr" / "bin" / "Vadox"))

    # AppRun Script
    apprun = appdir / "AppRun"
    apprun.write_text(
        '#!/bin/bash\n'
        'SELF=$(readlink -f "$0")\n'
        'HERE=${SELF%/*}\n'
        'export PATH="${HERE}/usr/bin/Vadox:${PATH}"\n'
        'exec "${HERE}/usr/bin/Vadox/Vadox" "$@"\n'
    )
    apprun.chmod(0o755)

    # Desktop-Datei
    desktop = appdir / "Vadox.desktop"
    desktop.write_text(
        "[Desktop Entry]\n"
        "Name=Vadox\n"
        "Comment=KI-Assistent für den Desktop\n"
        "Exec=Vadox\n"
        "Icon=vadox\n"
        "Type=Application\n"
        "Categories=Utility;ArtificialIntelligence;\n"
        "Terminal=false\n"
    )

    # Icon kopieren falls vorhanden
    icon_src = ROOT / "assets" / "icon.png"
    if icon_src.exists():
        shutil.copy(str(icon_src), str(appdir / "vadox.png"))
    else:
        # Leeres Icon erstellen
        (appdir / "vadox.png").touch()

    # appimagetool herunterladen und ausführen
    appimagetool = ROOT / "dist" / "appimagetool"
    if not appimagetool.exists():
        print("[+] Lade appimagetool herunter...")
        result = subprocess.run([
            "wget", "-q",
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
            "-O", str(appimagetool)
        ])
        if result.returncode == 0:
            appimagetool.chmod(0o755)
        else:
            print("[!] appimagetool konnte nicht geladen werden — überspringe AppImage")
            return False

    # FUSE für AppImage aktivieren
    os.environ["APPIMAGE_EXTRACT_AND_RUN"] = "1"

    appimage_out = ROOT / "dist" / "Vadox.AppImage"
    result = subprocess.run([
        str(appimagetool),
        str(appdir),
        str(appimage_out),
    ], env={**os.environ, "ARCH": "x86_64"})

    if result.returncode == 0 and appimage_out.exists():
        appimage_out.chmod(0o755)
        size_mb = appimage_out.stat().st_size / 1024 / 1024
        print(f"[+] AppImage erstellt: dist/Vadox.AppImage ({size_mb:.1f} MB)")
        return True
    return False


def main():
    print("=" * 60)
    print("  VADOX Linux Build — AppImage")
    print("=" * 60)

    for d in ["build", "dist"]:
        p = ROOT / d
        if p.exists():
            print(f"[+] Lösche altes {d}/")
            shutil.rmtree(p)

    # PyInstaller
    print("[+] Starte PyInstaller...")
    run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "vadox_linux.spec"], cwd=ROOT)

    dist_path = ROOT / "dist" / "Vadox"
    if not dist_path.exists():
        print("[ERROR] dist/Vadox wurde nicht erstellt!")
        sys.exit(1)

    # AppImage erstellen
    appimage_ok = create_appimage()

    # ZIP als Fallback
    print("\n[+] Erstelle ZIP: Vadox_Linux.zip")
    zip_path = ROOT / "dist" / "Vadox_Linux"
    shutil.make_archive(str(zip_path), "zip", str(ROOT / "dist"), "Vadox")
    zip_file = Path(str(zip_path) + ".zip")
    size_mb = zip_file.stat().st_size / 1024 / 1024
    print(f"    ZIP-Größe: {size_mb:.1f} MB")

    print("\n" + "=" * 60)
    print("  BUILD ERFOLGREICH!")
    if appimage_ok:
        print("  AppImage: dist/Vadox.AppImage")
    print(f"  ZIP:      dist/Vadox_Linux.zip ({size_mb:.1f} MB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
