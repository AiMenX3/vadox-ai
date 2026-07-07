TOOLS = [
    {
        "name": "get_weather",
        "description": "Ruft das aktuelle Wetter und die Wettervorhersage für eine Stadt ab. Nutze dieses Tool immer wenn nach dem Wetter gefragt wird.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Name der Stadt, z.B. Berlin, München, Wien"
                },
                "days": {
                    "type": "integer",
                    "description": "Anzahl der Vorschautage (1 = nur morgen, 7 = Woche). Standard: 1",
                    "default": 1
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "web_search",
        "description": "Sucht im Internet nach aktuellen Informationen. Nutze dieses Tool wenn du aktuelle Daten, Fakten oder Neuigkeiten brauchst.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Die Suchanfrage"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximale Anzahl Ergebnisse (Standard: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "news_search",
        "description": "Sucht nach aktuellen Nachrichten zu einem Thema.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Das Thema für die Nachrichtensuche"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_files",
        "description": "Sucht nach Dateien und Ordnern auf dem Computer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Dateiname oder Teil davon"
                },
                "search_path": {
                    "type": "string",
                    "description": "Startordner für die Suche (optional, Standard: Home-Verzeichnis)"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "list_directory",
        "description": "Listet den Inhalt eines Ordners auf.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Pfad zum Ordner (optional, Standard: Desktop)"
                }
            }
        }
    },
    {
        "name": "read_file",
        "description": "Liest den Inhalt einer Textdatei.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Vollständiger Pfad zur Datei"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "create_file",
        "description": "Erstellt eine neue Datei mit Inhalt und speichert sie. Nutze dieses Tool um HTML-Seiten, Textdateien, Python-Skripte, CSS-Dateien oder andere Dateien zu erstellen. WICHTIG: Wenn kein Pfad angegeben wird oder der Nutzer 'Desktop' sagt, speichere IMMER auf dem Desktop des Nutzers. Desktop-Pfad Windows: C:/Users/User/Desktop/dateiname.html",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Vollständiger absoluter Pfad zur neuen Datei. Standard Desktop: C:/Users/User/Desktop/dateiname.html — NIEMALS nur einen Dateinamen ohne Pfad angeben!"},
                "content": {"type": "string", "description": "Vollständiger Inhalt der Datei — bei HTML die komplette HTML-Seite, bei Python den vollständigen Code usw.", "default": ""}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "delete_file",
        "description": "Löscht eine Datei oder einen leeren Ordner.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Pfad zur Datei oder zum Ordner"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Macht einen Screenshot des Bildschirms und speichert ihn.",
        "input_schema": {
            "type": "object",
            "properties": {
                "save_path": {
                    "type": "string",
                    "description": "Speicherpfad für den Screenshot (optional)"
                }
            }
        }
    },
    {
        "name": "open_application",
        "description": "Öffnet eine Anwendung auf dem Computer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name der Anwendung, z.B. Chrome, Notepad, Rechner, Explorer"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "open_url",
        "description": "Öffnet eine Webseite im Standard-Browser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Die URL, z.B. https://google.de"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "get_system_info",
        "description": "Gibt aktuelle Systeminformationen zurück: CPU, RAM, Festplatte, Laufzeit.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "set_volume",
        "description": "Lautstärke auf einen bestimmten Wert setzen (0–100). Beispiel: 'Lautstärke auf 60' oder 'leiser auf 30'.",
        "input_schema": {
            "type": "object",
            "properties": {"level": {"type": "integer", "description": "Lautstärke 0-100"}},
            "required": ["level"]
        }
    },
    {
        "name": "get_volume",
        "description": "Aktuelle Lautstärke abfragen.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "volume_up",
        "description": "Lautstärke um X Prozent erhöhen. Standard: 10%.",
        "input_schema": {
            "type": "object",
            "properties": {"amount": {"type": "integer", "description": "Prozent erhöhen, Standard 10"}}
        }
    },
    {
        "name": "volume_down",
        "description": "Lautstärke um X Prozent verringern. Standard: 10%.",
        "input_schema": {
            "type": "object",
            "properties": {"amount": {"type": "integer", "description": "Prozent verringern, Standard 10"}}
        }
    },
    {
        "name": "mute_volume",
        "description": "Ton stummschalten.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "unmute_volume",
        "description": "Stummschaltung aufheben.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "empty_recycle_bin",
        "description": "Papierkorb leeren.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_recycle_bin_size",
        "description": "Zeigt wie viele Dateien und wie viel Speicherplatz im Papierkorb sind.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "delete_old_files",
        "description": "Löscht alte Dateien aus einem Ordner. Z.B. 'lösche alte Dateien aus Downloads die älter als 30 Tage sind'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "Ordner: 'Downloads', 'Desktop', 'Dokumente', 'Temp' oder absoluter Pfad"},
                "days":   {"type": "integer", "description": "Dateien älter als X Tage löschen, Standard 30"}
            },
            "required": ["folder"]
        }
    },
    {
        "name": "clean_temp_files",
        "description": "Windows Temp-Ordner bereinigen und Speicherplatz freigeben.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_disk_usage",
        "description": "Festplatten-Belegung aller Laufwerke anzeigen.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_large_files",
        "description": "Große Dateien in einem Ordner finden.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder":      {"type": "string", "description": "Ordner durchsuchen"},
                "min_size_mb": {"type": "integer", "description": "Mindestgröße in MB, Standard 100"}
            },
            "required": ["folder"]
        }
    },
    {
        "name": "list_running_apps",
        "description": "Listet alle laufenden Anwendungen und deren RAM-Nutzung auf.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "kill_application",
        "description": "Eine laufende Anwendung beenden/schließen.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Name der Anwendung"}},
            "required": ["app_name"]
        }
    },
    {
        "name": "shutdown_pc",
        "description": "PC herunterfahren, sofort oder nach X Minuten.",
        "input_schema": {
            "type": "object",
            "properties": {"minutes": {"type": "integer", "description": "Minuten bis zum Herunterfahren, 0 = sofort"}}
        }
    },
    {
        "name": "restart_pc",
        "description": "PC neu starten.",
        "input_schema": {
            "type": "object",
            "properties": {"minutes": {"type": "integer", "description": "Minuten bis zum Neustart, 0 = sofort"}}
        }
    },
    {
        "name": "cancel_shutdown",
        "description": "Geplantes Herunterfahren oder Neustart abbrechen.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "sleep_pc",
        "description": "PC in den Ruhezustand versetzen.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "lock_screen",
        "description": "Bildschirm sperren / PC sperren.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "set_brightness",
        "description": "Bildschirmhelligkeit setzen (0–100). Nur bei Laptops mit internem Display.",
        "input_schema": {
            "type": "object",
            "properties": {"level": {"type": "integer", "description": "Helligkeit 0-100"}},
            "required": ["level"]
        }
    },
    {
        "name": "get_clipboard",
        "description": "Inhalt der Zwischenablage lesen.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "set_clipboard",
        "description": "Text in die Zwischenablage kopieren.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text der kopiert werden soll"}},
            "required": ["text"]
        }
    },
    {
        "name": "browser_navigate",
        "description": "Öffnet eine Webseite im Browser und navigiert dorthin. Für komplexe Browser-Aufgaben nutze dieses Tool.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Die URL, z.B. https://google.de"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "browser_click",
        "description": "Klickt auf ein Element im Browser anhand eines CSS-Selektors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS-Selektor des Elements"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "browser_type",
        "description": "Gibt Text in ein Formularfeld im Browser ein.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS-Selektor des Eingabefelds"},
                "text": {"type": "string", "description": "Der einzugebende Text"}
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "browser_get_text",
        "description": "Liest den sichtbaren Text der aktuellen Browserseite aus.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "browser_search_google",
        "description": "Sucht etwas bei Google im Browser und gibt die Ergebnistitel zurück.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Die Suchanfrage"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "browser_scroll",
        "description": "Scrollt die aktuelle Browserseite nach oben oder unten.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down"]},
                "amount": {"type": "integer", "default": 500}
            }
        }
    },
    {
        "name": "browser_screenshot",
        "description": "Macht einen Screenshot des aktuellen Browser-Fensters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "save_path": {"type": "string", "description": "Speicherpfad (optional)"}
            }
        }
    },
    {
        "name": "browser_close",
        "description": "Schließt den Browser.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "read_emails",
        "description": "Liest E-Mails aus dem Postfach. Nutze dieses Tool wenn der Nutzer nach E-Mails fragt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count":       {"type": "integer", "description": "Anzahl E-Mails (Standard: 5)", "default": 5},
                "unread_only": {"type": "boolean", "description": "Nur ungelesene anzeigen", "default": False},
                "folder":      {"type": "string",  "description": "Ordner (Standard: INBOX)", "default": "INBOX"}
            }
        }
    },
    {
        "name": "send_email",
        "description": "Sendet eine E-Mail an eine Adresse.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Empfänger-E-Mail-Adresse"},
                "subject": {"type": "string", "description": "Betreff der E-Mail"},
                "body":    {"type": "string", "description": "Inhalt der E-Mail"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "search_emails",
        "description": "Sucht nach E-Mails mit einem bestimmten Stichwort im Betreff oder Inhalt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Suchbegriff"},
                "count":   {"type": "integer", "description": "Max. Ergebnisse", "default": 5}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "get_unread_count",
        "description": "Gibt die Anzahl ungelesener E-Mails zurück.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "create_presentation",
        "description": "Erstellt eine professionelle PowerPoint-Präsentation (.pptx) zu einem Thema mit Folien. Erstelle zuerst einen guten Gliederungsplan als JSON und rufe dann dieses Tool auf.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic":     {"type": "string", "description": "Hauptthema / Titel der Präsentation"},
                "outline":   {"type": "string", "description": "JSON-Array mit Folien: [{\"title\":\"...\",\"subtitle\":\"...\",\"bullets\":[\"Punkt 1\",\"Punkt 2\"]}]. Die erste Folie ist die Titelfolie mit subtitle."},
                "save_path": {"type": "string", "description": "Speicherpfad (optional, Standard: Desktop)"}
            },
            "required": ["topic", "outline"]
        }
    },
    {
        "name": "get_calendar_events",
        "description": "Liest bevorstehende Kalender-Termine. Nutze dieses Tool wenn der Nutzer nach Terminen, Kalender oder Meetings fragt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Wie viele Tage in die Zukunft schauen (Standard: 7)", "default": 7}
            }
        }
    },
    {
        "name": "get_todays_events",
        "description": "Zeigt alle Termine von heute. Nutze dieses Tool wenn der Nutzer fragt was heute ansteht.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "create_calendar_event",
        "description": "Erstellt einen neuen Kalender-Termin. Nutze dieses Tool wenn der Nutzer einen Termin anlegen möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Titel des Termins"},
                "start":       {"type": "string", "description": "Startzeit, z.B. 'morgen 15:00', 'Montag 10:30', '25.12.2025 14:00'"},
                "end":         {"type": "string", "description": "Endzeit (optional, Standard: 1 Stunde nach Start)"},
                "location":    {"type": "string", "description": "Ort des Termins (optional)"},
                "description": {"type": "string", "description": "Beschreibung (optional)"}
            },
            "required": ["title", "start"]
        }
    },
    {
        "name": "remember_fact",
        "description": "Merkt sich eine wichtige Information über den Nutzer dauerhaft.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "Die zu merkende Information, z.B. 'Der Nutzer arbeitet als Entwickler'"}
            },
            "required": ["fact"]
        }
    },
    {
        "name": "translate_text",
        "description": "Übersetzt Text in eine andere Sprache. Nutze dieses Tool wenn der Nutzer etwas übersetzen möchte oder fragt wie etwas auf einer anderen Sprache heißt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Der zu übersetzende Text"
                },
                "target_lang": {
                    "type": "string",
                    "description": "Zielsprache auf Deutsch oder als Code: deutsch, englisch, spanisch, franzoesisch, italienisch, japanisch, chinesisch, russisch, etc."
                },
                "source_lang": {
                    "type": "string",
                    "description": "Quellsprache (optional, Standard: auto)"
                }
            },
            "required": ["text", "target_lang"]
        }
    },
    {
        "name": "smarthome_command",
        "description": "Steuert Smart Home Geräte: Lichter, Steckdosen, Szenen. Nutze dieses Tool wenn der Nutzer Lampen, Lichter, Steckdosen oder Smart Home Geräte steuern möchte. Beispiele: 'Licht an', 'Lampen aus', 'Szene Film', 'Küche ausschalten'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Der Smart Home Befehl auf Deutsch, z.B. 'Licht an', 'alles aus', 'Szene Entspannung', 'Küche einschalten'"
                }
            },
            "required": ["command"]
        }
    },
    # ── WhatsApp ──────────────────────────────────────────────────────────────
    {
        "name": "send_whatsapp",
        "description": "Sendet eine WhatsApp-Nachricht an einen Kontakt. Nutze dieses Tool wenn der Nutzer jemanden über WhatsApp anschreiben möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "Telefonnummer mit Ländervorwahl (z.B. +4917612345678) oder Kontaktname"},
                "message": {"type": "string", "description": "Die zu sendende Nachricht"}
            },
            "required": ["contact", "message"]
        }
    },
    # ── Screen AI ─────────────────────────────────────────────────────────────
    {
        "name": "analyze_screen",
        "description": "Macht einen Screenshot und analysiert ihn mit KI. Nutze dieses Tool wenn der Nutzer fragt was auf dem Bildschirm ist, etwas auf dem Bildschirm sucht, oder den Bildschirminhalt beschrieben haben möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Was soll die KI über den Bildschirm beantworten? z.B. 'Was siehst du?' oder 'Welche Fenster sind offen?'", "default": "Was siehst du auf dem Bildschirm?"}
            },
            "required": []
        }
    },
    {
        "name": "read_screen_text",
        "description": "Liest den gesamten sichtbaren Text vom Bildschirm ab. Nützlich um Text zu kopieren der nicht markierbar ist.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    # ── YouTube ───────────────────────────────────────────────────────────────
    {
        "name": "search_youtube",
        "description": "Sucht YouTube-Videos und gibt Ergebnisse zurück. Nutze dieses Tool bei Fragen nach Videos, Tutorials oder YouTube-Inhalten.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Suchbegriff für YouTube"},
                "count": {"type": "integer", "description": "Anzahl Ergebnisse (Standard: 5)", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "open_youtube",
        "description": "Öffnet das passendste YouTube-Video direkt im Browser. Nutze dieses Tool wenn der Nutzer ein Video abspielen oder öffnen möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Was gesucht/geöffnet werden soll, z.B. 'Metallica Master of Puppets' oder 'Python Tutorial'"}
            },
            "required": ["query"]
        }
    },
    # ── Flugsuche ─────────────────────────────────────────────────────────────
    {
        "name": "search_flights",
        "description": "Sucht Flüge zwischen zwei Städten und öffnet die Ergebnisse im Browser. Nutze dieses Tool wenn nach Flügen gefragt wird.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin":      {"type": "string", "description": "Abflugort, z.B. 'Frankfurt', 'München', 'BER'"},
                "destination": {"type": "string", "description": "Zielort, z.B. 'London', 'Dubai', 'JFK'"},
                "date":        {"type": "string", "description": "Abflugdatum z.B. '15.07.2025' oder 'morgen' oder 'nächste woche'", "default": ""},
                "return_date": {"type": "string", "description": "Rückflugdatum (leer = nur Hinflug)", "default": ""},
                "passengers":  {"type": "integer", "description": "Anzahl Passagiere", "default": 1}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "check_flight_status",
        "description": "Prüft den Status eines bestimmten Fluges auf FlightRadar24.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_number": {"type": "string", "description": "Flugnummer z.B. 'LH123', 'FR456'"}
            },
            "required": ["flight_number"]
        }
    },
    # ── Gaming ────────────────────────────────────────────────────────────────
    {
        "name": "launch_game",
        "description": "Startet ein Spiel über Steam oder Epic Games. Nutze dieses Tool wenn der Nutzer ein Spiel starten möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "game_name": {"type": "string", "description": "Name des Spiels, z.B. 'CS2', 'Dota 2', 'Rust'"}
            },
            "required": ["game_name"]
        }
    },
    {
        "name": "list_installed_steam_games",
        "description": "Zeigt alle installierten Steam-Spiele an.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_steam_game_info",
        "description": "Holt Infos zu einem Spiel vom Steam-Store: Preis, Genre, Bewertung.",
        "input_schema": {
            "type": "object",
            "properties": {
                "game_name": {"type": "string", "description": "Name des Spiels"}
            },
            "required": ["game_name"]
        }
    },
    {
        "name": "launch_steam",
        "description": "Startet Steam.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "launch_epic",
        "description": "Startet den Epic Games Launcher.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    # ── Telegram ──────────────────────────────────────────────────────────────
    {
        "name": "send_telegram",
        "description": "Sendet eine Nachricht via Telegram aufs Handy. Nutze dieses Tool wenn der Nutzer eine Benachrichtigung aufs Handy schicken möchte oder Telegram erwähnt.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Die zu sendende Nachricht"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_telegram_updates",
        "description": "Prüft ob neue Nachrichten vom Nutzer an den Telegram-Bot eingegangen sind.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    # ── PDF-Analyse ──────────────────────────────────────────────────────────
    {
        "name": "analyze_pdf",
        "description": "Liest ein PDF-Dokument und analysiert oder fasst es zusammen. Nutze dieses Tool wenn der Nutzer ein PDF analysieren, zusammenfassen oder eine Frage dazu stellen möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Absoluter Pfad zur PDF-Datei"},
                "question": {"type": "string", "description": "Optionale Frage zum Dokument, z.B. 'Was sind die wichtigsten Punkte?' oder 'Was kostet das?'", "default": ""}
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "find_pdfs",
        "description": "Sucht nach PDF-Dateien auf dem Desktop und in Downloads.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    # ── Spotify ───────────────────────────────────────────────────────────────
    {
        "name": "spotify_play",
        "description": "Öffnet Spotify und spielt einen Song, Künstler oder Playlist ab. Nutze dieses Tool wenn der Nutzer Musik abspielen möchte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Was abgespielt werden soll, z.B. 'Rammstein', 'Lo-Fi Playlist', 'Chill Musik'"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "spotify_control",
        "description": "Steuert Spotify: pause, weiter, nächster Song, vorheriger Song, lauter, leiser.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Aktion: pause, play, next, previous, volume_up, volume_down"}
            },
            "required": ["action"]
        }
    },
    # ── Selbstentwicklung ─────────────────────────────────────────────────────
    {
        "name": "create_new_tool",
        "description": "Erstellt ein neues Tool für Vadox — Selbstentwicklung. Nutze dieses Tool wenn der Nutzer eine neue Fähigkeit wünscht die Vadox noch nicht hat. Schreibe Python-Code für die Funktion und registriere sie als neues Tool das sofort nutzbar ist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name":   {"type": "string", "description": "Eindeutiger Name des Tools, z.B. 'set_timer' oder 'translate_file'"},
                "description": {"type": "string", "description": "Beschreibung was das Tool macht — wird von der KI genutzt um das Tool zu finden"},
                "python_code": {"type": "string", "description": "Vollständiger Python-Code mit einer Funktion namens 'run(...)'. Importiere alle benötigten Module innerhalb der Funktion. Die Funktion muss einen String zurückgeben."},
                "parameters":  {"type": "object", "description": "Parameter-Schema als JSON-Objekt, z.B. {\"text\": {\"type\": \"string\", \"description\": \"Der Text\"}}"}
            },
            "required": ["tool_name", "description", "python_code", "parameters"]
        }
    },
    {
        "name": "list_custom_tools",
        "description": "Zeigt alle selbst erstellten Tools an die Vadox im Laufe der Zeit gelernt hat.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "add_user_rule",
        "description": "Speichert eine Wenn-Dann-Regel dauerhaft. 'Wenn ich X sage, mach immer Y'. Nutze dieses Tool wenn der Nutzer Vadox beibringen möchte auf bestimmte Wörter/Phrasen immer gleich zu reagieren.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {"type": "string", "description": "Das Schlüsselwort oder die Phrase die den Trigger auslöst"},
                "action":  {"type": "string", "description": "Was Vadox tun soll wenn der Trigger ausgelöst wird"}
            },
            "required": ["trigger", "action"]
        }
    },
    {
        "name": "add_user_instruction",
        "description": "Speichert eine dauerhafte Verhaltensanweisung für Vadox. Nutze dieses Tool wenn der Nutzer Vadox's generelles Verhalten dauerhaft ändern möchte, z.B. 'Antworte immer kürzer', 'Nenn mich immer Chef', 'Beginne jede Antwort mit einer Zusammenfassung'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instruction": {"type": "string", "description": "Die dauerhafte Verhaltensanweisung"}
            },
            "required": ["instruction"]
        }
    },
    {
        "name": "list_user_rules",
        "description": "Zeigt alle gespeicherten Regeln und Anweisungen des Nutzers.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "remove_user_rule",
        "description": "Löscht eine gespeicherte Wenn-Dann-Regel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trigger": {"type": "string", "description": "Der Trigger der gelöscht werden soll"}
            },
            "required": ["trigger"]
        }
    },
    {
        "name": "get_feedback_stats",
        "description": "Zeigt die Feedback-Statistik: wie viele Antworten gut oder schlecht bewertet wurden.",
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },

    # ── Computer Use — Desktop & Browser vollständig steuern ──────────────────
    {
        "name": "computer_find_and_click",
        "description": "KI sucht ein Element auf dem Bildschirm und klickt es an. Nutze dieses Tool wenn du auf etwas klicken möchtest das du auf dem Bildschirm siehst: Buttons, Felder, Links, Icons. Beschreibe das Element auf Deutsch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "element_description": {"type": "string", "description": "Was soll angeklickt werden? z.B. 'Veröffentlichen Button', 'Benutzername Feld', 'Senden Button oben rechts'"},
                "double_click": {"type": "boolean", "description": "Doppelklick statt einfach Klick", "default": False}
            },
            "required": ["element_description"]
        }
    },
    {
        "name": "computer_click",
        "description": "Klickt auf eine bestimmte Bildschirmposition (x/y Koordinaten). Nutze computer_find_and_click wenn du nur eine Beschreibung hast.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "X-Koordinate in Pixeln"},
                "y": {"type": "integer", "description": "Y-Koordinate in Pixeln"},
                "button": {"type": "string", "description": "left, right oder middle", "default": "left"},
                "double": {"type": "boolean", "description": "Doppelklick", "default": False}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "computer_type",
        "description": "Tippt Text in das aktuell aktive Fenster oder Eingabefeld. Vorher computer_find_and_click auf das Feld nutzen.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Der einzugebende Text"},
                "delay": {"type": "number", "description": "Verzögerung zwischen Tasten in Sekunden (Standard: 0.05)", "default": 0.05}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_key",
        "description": "Drückt eine Taste oder Tastenkombination. Beispiele: 'enter', 'tab', 'ctrl+c', 'ctrl+v', 'ctrl+a', 'alt+f4', 'escape', 'delete'",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Taste oder Kombination, z.B. 'enter', 'ctrl+v', 'alt+tab'"}
            },
            "required": ["key"]
        }
    },
    {
        "name": "computer_scroll",
        "description": "Scrollt auf dem Bildschirm nach oben oder unten.",
        "input_schema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "description": "up oder down", "default": "down"},
                "amount": {"type": "integer", "description": "Wie viel scrollen (1-10)", "default": 3}
            }
        }
    },
    {
        "name": "computer_drag",
        "description": "Drag & Drop: zieht ein Element von einer Position zu einer anderen. Für Elementor-Blöcke, Datei-Verschieben usw.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_x": {"type": "integer", "description": "Start X-Koordinate"},
                "from_y": {"type": "integer", "description": "Start Y-Koordinate"},
                "to_x": {"type": "integer", "description": "Ziel X-Koordinate"},
                "to_y": {"type": "integer", "description": "Ziel Y-Koordinate"},
                "duration": {"type": "number", "description": "Dauer der Bewegung in Sekunden", "default": 0.5}
            },
            "required": ["from_x", "from_y", "to_x", "to_y"]
        }
    },
    {
        "name": "computer_read_screen",
        "description": "Macht einen Screenshot und lässt die KI den Bildschirminhalt beschreiben. Nutze dies um zu sehen was gerade auf dem Bildschirm ist, bevor du klickst.",
        "input_schema": {
            "type": "object",
            "properties": {
                "region_description": {"type": "string", "description": "Was soll die KI beschreiben? z.B. 'Welche Buttons sind sichtbar?', 'Was steht in dem Formular?'", "default": ""}
            }
        }
    },
    {
        "name": "computer_screenshot",
        "description": "Macht einen Screenshot des Bildschirms und speichert ihn.",
        "input_schema": {
            "type": "object",
            "properties": {
                "save_path": {"type": "string", "description": "Speicherpfad (optional)", "default": ""}
            }
        }
    },
    {
        "name": "computer_wait",
        "description": "Wartet eine bestimmte Zeit — nützlich um auf Ladezeiten zu warten.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Wartezeit in Sekunden", "default": 1.0}
            }
        }
    },
    {
        "name": "browser_computer_use",
        "description": "Öffnet den Browser und führt eine komplexe Aufgabe vollautomatisch aus. KI sieht den Bildschirm und klickt/tippt selbst. Nutze dies für: Facebook-Posts, WordPress-Beiträge, Formulare ausfüllen, Webseiten bedienen. Beschreibe die Aufgabe detailliert.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Start-URL, z.B. 'https://facebook.com' oder 'https://meineshop.wordpress.com/wp-admin'"},
                "task": {"type": "string", "description": "Was soll im Browser erledigt werden? Sehr detailliert beschreiben inkl. Texte die eingegeben werden sollen."}
            },
            "required": ["url", "task"]
        }
    },
]
