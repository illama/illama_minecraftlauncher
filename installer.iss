; Script d'installation Inno Setup pour Illama Launcher
; Version corrigée sans erreurs de syntaxe

[Setup]
AppName=Illama Launcher
AppVersion=2.0.3
AppPublisher=Illama Server
AppPublisherURL=https://illama.duckdns.org
DefaultDirName={autopf}\Illama Launcher
DefaultGroupName=Illama Launcher
OutputDir=installer_output
OutputBaseFilename=IllamaLauncher_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\IllamaLauncher.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\IllamaLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Illama Launcher"; Filename: "{app}\IllamaLauncher.exe"
Name: "{autodesktop}\Illama Launcher"; Filename: "{app}\IllamaLauncher.exe"; Tasks: desktopicon
Name: "{group}\Désinstaller Illama Launcher"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\IllamaLauncher.exe"; Description: "Lancer Illama Launcher"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\IllamaLauncher"
Type: filesandordirs; Name: "{userappdata}\IllamaLauncher"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  TempDir: String;
  FindRec: TFindRec;
  DirPath: String;
  Cleaned: Integer;
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    // Nettoyer les anciens dossiers _MEI* avant l'installation
    TempDir := ExpandConstant('{tmp}\..');
    Cleaned := 0;
    
    if FindFirst(TempDir + '\_MEI*', FindRec) then
    begin
      try
        repeat
          if FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY <> 0 then
          begin
            DirPath := TempDir + '\' + FindRec.Name;
            try
              DelTree(DirPath, True, True, True);
              Cleaned := Cleaned + 1;
            except
              // Impossible de supprimer (probablement en cours d'utilisation)
            end;
          end;
        until not FindNext(FindRec);
      finally
        FindClose(FindRec);
      end;
    end;
  end;
end;
