; ============================================================
;  PC Optimizer Pro - Inno Setup Installer Script
;  github.com/Londopy/pc-optimizer
;
;  Requirements:
;    - Inno Setup 6.3+ (https://jrsoftware.org/isdl.php)
;    - InnoDependencyInstaller (optional, for VC++ runtime)
;    - Built PyInstaller output in dist\PCOptimizerPro\
;
;  Build: ISCC.exe installer\setup.iss
; ============================================================

#define MyAppName        "PC Optimizer Pro"
#define MyAppVersion     "1.0.0"
#define MyAppPublisher   "Londopy"
#define MyAppURL         "https://github.com/Londopy/pc-optimizer"
#define MyAppExeName     "PCOptimizerPro.exe"
#define MyAppID          "{A7F23B91-4C2D-4E8F-9B1A-3D7E5F29C840}"

[Setup]
AppId={#MyAppID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Install to Program Files
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Require admin
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Output
OutputDir=installer\output
OutputBaseFilename=PCOptimizerPro_Setup_v{#MyAppVersion}

; Visual
WizardStyle=modern
WizardResizable=no
SetupIconFile=assets\icon.ico

; Splash / branding images (BMP format required)
; WizardImageFile=assets\installer_banner.bmp      ; 164x314 px - left panel
; WizardSmallImageFile=assets\installer_small.bmp  ; 55x58 px - top right

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4

; Misc
ShowLanguageDialog=auto
ShowComponentSizes=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Create a &desktop shortcut";      GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunch"; Description: "Create a &Quick Launch shortcut";   GroupDescription: "Additional icons:"; Flags: unchecked
Name: "autostart";   Description: "Launch PC Optimizer Pro on Windows startup"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Main application (PyInstaller --onedir output)
Source: "dist\PCOptimizerPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Icons]
; Start Menu
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"

; Desktop (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch (optional)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunch

; Uninstall entry
Name: "{autoprograms}\{#MyAppName}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
; Autostart (optional task)
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PCOptimizerPro"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: autostart

; App registration for Windows
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

[Run]
; Launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

; Open GitHub page
Filename: "https://github.com/Londopy/pc-optimizer"; Description: "View on GitHub"; Flags: nowait postinstall skipifsilent shellexec unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// ============================================================
// Custom installer UI & logic
// ============================================================

var
  SystemInfoPage: TWizardPage;
  SystemInfoLabel: TLabel;

function GetSystemInfo(): String;
var
  ResultCode: Integer;
  TempFile: String;
  Lines: TStringList;
  Info: String;
begin
  Info := '';
  try
    // Basic Windows version
    Info := 'Windows ' + {#SetupSetting("MinVersion")};
  except
    Info := 'System information unavailable';
  end;
  Result := Info;
end;

procedure InitializeWizard();
begin
  // Custom welcome text
  WizardForm.WelcomeLabel1.Caption := 'PC Optimizer Pro';
  WizardForm.WelcomeLabel2.Caption :=
    'This will install PC Optimizer Pro on your computer.' + #13#10 + #13#10 +
    'PC Optimizer Pro includes:' + #13#10 +
    '  • One-click gaming optimization' + #13#10 +
    '  • Corsair AIO fan control (via liquidctl)' + #13#10 +
    '  • RGB lighting control (via OpenRGB)' + #13#10 +
    '  • Windows debloat tool' + #13#10 +
    '  • Live hardware monitoring' + #13#10 + #13#10 +
    'Click Next to continue.';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
end;

// Show a warning if not running on Windows 10+
function InitializeSetup(): Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.Major < 10 then
  begin
    MsgBox(
      'PC Optimizer Pro requires Windows 10 or later.' + #13#10 +
      'Your system does not meet this requirement.',
      mbError, MB_OK
    );
    Result := False;
  end
  else
    Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Nothing extra needed - PyInstaller bundle is self-contained
  end;
end;
