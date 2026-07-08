import sys
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from vadox.core.license import check, get_trial_info
from vadox.ui.license_dialog import LicenseDialog
from vadox.ui.main_window import MainWindow

LOG_FILE = Path.home() / ".vadox" / "crash.log"


def _write_crash(exc_type, exc_value, exc_tb):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = _write_crash


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Vadox")
    app.setStyle("Fusion")

    valid, status = check()

    if not valid:
        mode = "trial_expired" if status == "trial_expired" else "no_license"
        dlg  = LicenseDialog(mode=mode)
        dlg.show()
        if not dlg.exec() or not dlg.was_accepted():
            sys.exit(0)

    window = MainWindow()
    window.show()

    # Systemprüfung: fehlende Voraussetzungen (VLC, Wake-Word-Modelle …) freundlich
    # anzeigen und wo moeglich automatisch nachinstallieren. Blockiert die App nicht.
    try:
        from vadox.ui.system_check_dialog import run_system_check
        run_system_check(window)
    except Exception as e:
        print(f"[SystemCheck] {e}")

    # Trial-Countdown im Hauptfenster anzeigen
    _start_trial_timer(window)

    sys.exit(app.exec())


def _start_trial_timer(window):
    """Prüft alle 60s ob Trial läuft und zeigt Countdown / Warnungen."""
    from PyQt6.QtCore import QTimer
    from vadox.core.license import get_trial_info, check

    warned_6h = False
    warned_1h = False

    def _tick():
        nonlocal warned_6h, warned_1h

        valid, status = check()
        if not valid:
            # Trial abgelaufen → Dialog anzeigen
            _show_expired_dialog(window)
            return

        trial = get_trial_info()
        if not trial.get("active"):
            return

        secs = trial.get("seconds_left", 0)
        h    = secs // 3600
        m    = (secs % 3600) // 60

        # Titelleiste updaten
        try:
            window.setWindowTitle(f"VADOX  —  Trial: noch {h}h {m:02d}m")
        except Exception:
            pass

        # Warnungen
        if secs <= 3600 and not warned_1h:
            warned_1h = True
            _show_warning(window, f"⚠  Noch 1 Stunde im Trial!\n\nJetzt upgraden für nur 197 € (Lifetime).")
        elif secs <= 21600 and not warned_6h:
            warned_6h = True
            _show_warning(window, f"⚠  Noch 6 Stunden im Trial.\n\nNach Ablauf ist Vadox PRO für 197 € (Lifetime) verfügbar.")

    timer = QTimer(window)
    timer.timeout.connect(_tick)
    timer.start(60_000)
    _tick()  # Sofort einmal ausführen


def _show_warning(window, msg: str):
    from PyQt6.QtWidgets import QMessageBox
    box = QMessageBox(window)
    box.setWindowTitle("Vadox Trial")
    box.setText(msg)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()


def _show_expired_dialog(window):
    dlg = LicenseDialog(parent=window, mode="trial_expired")
    if dlg.exec() and dlg.was_accepted():
        window.setWindowTitle("VADOX")
    else:
        window.close()


if __name__ == "__main__":
    main()
