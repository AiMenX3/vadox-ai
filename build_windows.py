#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VADOX Windows Build Script
Erzeugt: dist/Vadox_Setup.exe (Installer) + dist/Vadox_Windows.zip (Fallback)
"""
import subprocess
import sys
import shutil
import os
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd, **kwargs):
    print(f"\n[BUILD] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"[ERROR] Fehlgeschlagen mit Code {result.returncode}")
        sys.exit(result.returncode)
    return result


def main():
    print("=" * 60)
    print("  VADOX BUILD — Windows Installer")
    print("=" * 60)

    # Alten Build löschen
    for d in ['build', 'dist']:
        p = ROOT / d
        if p.exists():
            print(f"[+] Lösche alten Build: {d}/")
            shutil.rmtree(p)

    # PyInstaller
    print("[+] Starte PyInstaller...")
    run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'vadox.spec'], cwd=ROOT)

    exe = ROOT / 'dist' / 'Vadox' / 'Vadox.exe'
    if not exe.exists():
        print("[ERROR] EXE nicht gefunden!")
        sys.exit(1)

    size_mb = exe.stat().st_size / 1024 / 1024
    print(f"\n[+] Vadox.exe: {size_mb:.1f} MB")

    # Inno Setup Installer erstellen
    inno_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    ]
    iscc = next((p for p in inno_paths if p.exists()), None)

    if iscc:
        print("\n[+] Erstelle Installer mit Inno Setup...")
        run([str(iscc), "installer_windows.iss"], cwd=ROOT)
        installer = ROOT / "dist" / "Vadox_Setup.exe"
        if installer.exists():
            inst_mb = installer.stat().st_size / 1024 / 1024
            print(f"\n{'=' * 60}")
            print(f"  BUILD ERFOLGREICH!")
            print(f"  Installer: dist/Vadox_Setup.exe ({inst_mb:.1f} MB)")
            print(f"{'=' * 60}")
        else:
            print("[!] Inno Setup hat keinen Installer erzeugt — nur ZIP wird erstellt")
    else:
        print("[!] Inno Setup nicht gefunden — überspringe Installer-Erstellung")
        print("    Tipp: https://jrsoftware.org/isdl.php")

    # ZIP als Fallback / für GitHub Actions
    dist_folder = ROOT / 'dist' / 'Vadox'
    zip_path = ROOT / 'dist' / 'Vadox_Windows.zip'
    print(f"\n[+] Erstelle ZIP: {zip_path.name}")
    import zipfile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in dist_folder.rglob('*'):
            if f.is_file():
                zf.write(f, f.relative_to(dist_folder.parent))
    zip_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"    ZIP-Größe: {zip_mb:.1f} MB")
    print(f"\n[+] Fertig! dist/Vadox_Setup.exe und dist/Vadox_Windows.zip")


if __name__ == '__main__':
    main()
