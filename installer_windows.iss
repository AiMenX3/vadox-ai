; Vadox Windows Installer — Inno Setup Script
; Erstellt einen professionellen Setup.exe Installer

#define AppName "Vadox"
#define AppVersion "1.0.0"
#define AppPublisher "Vadox AI"
#define AppURL "https://vadox.ai"
#define AppExeName "Vadox.exe"

[Setup]
AppId={{8F3A2B1C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=Vadox_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Symbole:"
Name: "startupicon";    Description: "Beim Windows-Start automatisch starten"; GroupDescription: "Autostart:"; Flags: unchecked

[Files]
; Gesamten dist/Vadox Ordner einbinden
Source: "dist\Vadox\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}";          Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}";            Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";            Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Vadox jetzt starten"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Zeigt Willkommensnachricht
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Willkommen bei Vadox — Ihrem KI-Assistenten für den Desktop.' + #13#10 + #13#10 +
    'Vadox wird auf Ihrem Computer installiert und ist danach sofort einsatzbereit.' + #13#10 + #13#10 +
    'Sie benötigen einen API-Key (Claude, OpenAI oder OpenRouter) um Vadox zu nutzen.';
end;
