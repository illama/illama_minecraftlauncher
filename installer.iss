; Inno Setup Script pour Illama Launcher
; Compile ce fichier avec Inno Setup (https://jrsoftware.org/isinfo.php)

#define MyAppName "Illama Launcher"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Illama Server"
#define MyAppURL "https://illama.duckdns.org"
#define MyAppExeName "IllamaLauncher.exe"

[Setup]
AppId={{8F3B5E7A-1234-5678-ABCD-ILLAMA123456}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Icône de l'installateur (décommente si tu as une icône)
; SetupIconFile=icon.ico
OutputDir=installer_output
OutputBaseFilename=IllamaLauncher_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Supprimer l'ancien contenu si le dossier existe déjà
DirExistsWarning=no
DisableDirPage=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: replacesameversion
; Ajoute d'autres fichiers si nécessaire
; Source: "icon.ico"; DestDir: "{app}"; Flags: replacesameversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Supprimer tous les fichiers du dossier d'installation (y compris le dossier lui-même)
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDir: String;
begin
  // Vérifier juste avant l'installation si le dossier existe déjà
  if CurStep = ssInstall then
  begin
    AppDir := ExpandConstant('{app}');
    
    if DirExists(AppDir) then
    begin
      // Supprimer l'ancien contenu avant l'installation
      if MsgBox('Une installation existante a été détectée dans le dossier :' + #13#10 + 
                AppDir + #13#10 + #13#10 +
                'Voulez-vous supprimer l''ancienne installation et la remplacer ?', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        // Supprimer tous les fichiers et dossiers de l'ancienne installation
        DelTree(AppDir, True, True, True);
      end
      else
      begin
        // Annuler l'installation si l'utilisateur refuse
        Abort;
      end;
    end;
  end;
end;

function GetUserHomeDir: String;
var
  UserName: String;
  AppDataPath: String;
begin
  // Méthode 1: Utiliser AppData et remonter au dossier home
  AppDataPath := ExpandConstant('{userappdata}');
  // AppData est généralement dans C:\Users\Username\AppData\Roaming
  // On remonte de 2 niveaux pour obtenir C:\Users\Username
  Result := AppDataPath;
  StringChangeEx(Result, '\AppData\Roaming', '', True);
  
  // Vérifier si le résultat est valide
  if not DirExists(Result) then
  begin
    // Méthode 2: Utiliser le nom d'utilisateur et construire le chemin
    UserName := GetUserNameString;
    Result := 'C:\Users\' + UserName;
    
    if not DirExists(Result) then
    begin
      // Méthode 3: Utiliser la variable d'environnement USERPROFILE
      Result := GetEnv('USERPROFILE');
      if (Result = '') or (not DirExists(Result)) then
      begin
        // Fallback: utiliser juste AppData
        Result := AppDataPath;
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  PrismInstancesPath: String;
  PrismInstancePath: String;
  ConfigFile: String;
  AuthFile: String;
  UserHomeDir: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    UserHomeDir := GetUserHomeDir;
    
    // Supprimer l'instance Prism IllamaServer
    PrismInstancesPath := ExpandConstant('{userappdata}\PrismLauncher\instances');
    PrismInstancePath := PrismInstancesPath + '\IllamaServer';
    
    if DirExists(PrismInstancePath) then
    begin
      if MsgBox('Supprimer l''instance Prism "IllamaServer" créée par le launcher ?', 
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(PrismInstancePath, True, True, True);
      end;
    end;
    
    // Supprimer les fichiers de configuration (dans le dossier home de l'utilisateur)
    ConfigFile := UserHomeDir + '\.illama_launcher_config.json';
    AuthFile := UserHomeDir + '\.illama_launcher_auth.json';
    
    if FileExists(ConfigFile) then
      DeleteFile(ConfigFile);
    if FileExists(AuthFile) then
      DeleteFile(AuthFile);
    
    // Supprimer aussi dans AppData au cas où
    ConfigFile := ExpandConstant('{userappdata}\.illama_launcher_config.json');
    AuthFile := ExpandConstant('{userappdata}\.illama_launcher_auth.json');
    
    if FileExists(ConfigFile) then
      DeleteFile(ConfigFile);
    if FileExists(AuthFile) then
      DeleteFile(AuthFile);
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    // Supprimer le dossier d'installation s'il est vide
    if DirExists(ExpandConstant('{app}')) then
    begin
      try
        RemoveDir(ExpandConstant('{app}'));
      except
        // Ignorer si le dossier n'est pas vide ou s'il y a une erreur
      end;
    end;
  end;
end;
