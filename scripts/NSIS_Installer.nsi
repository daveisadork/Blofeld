; -*- coding: latin-1 -*-
;
; Blofeld - All-in-one music server
; Copyright 2010 Dave Hayes <dwhayes@gmail.com>
;
; This program is free software; you can redistribute it and/or
; modify it under the terms of the GNU General Public License
; as published by the Free Software Foundation; either version 2
; of the License, or (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program; if not, write to the Free Software
; Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.

!addplugindir win\nsis\Plugins
!addincludedir win\nsis\Include

!include "MUI2.nsh"
!include Sections.nsh
;!include "registerExtension.nsh"


Name "${_PRODUCT}"
OutFile "..\${_FILE}"


; Some default compiler settings (uncomment and change at will):
; SetCompress auto ; (can be off or force)
; SetDatablockOptimize on ; (can be off)
; CRCCheck on ; (can be off)
; AutoCloseWindow false ; (can be true for the window go away automatically at end)
; ShowInstDetails hide ; (can be show to have them shown, or nevershow to disable)
; SetDateSave off ; (can be on to have files restored to their orginal date)
WindowIcon on

InstallDir "$PROGRAMFILES\Blofeld"
InstallDirRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Blofeld" ""
;DirText $(MsgSelectDir)

  ;Vista redirects $SMPROGRAMS to all users without this
  RequestExecutionLevel admin
  FileErrorText "If you have no admin rights, try to install into a user directory."


;--------------------------------
;Variables

  Var MUI_TEMP
  Var STARTMENU_FOLDER
;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

  ;Show all languages, despite user's codepage
  !define MUI_LANGDLL_ALLLANGUAGES

  !define MUI_ICON "..\blofeld.ico"


;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "..\COPYING"
  !define MUI_COMPONENTSPAGE_NODESC
  !insertmacro MUI_PAGE_COMPONENTS

  !insertmacro MUI_PAGE_DIRECTORY

  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\Blofeld"
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  !define MUI_STARTMENUPAGE_DEFAULTFOLDER "Blofeld"
  ;Remember the installer language
  !define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
  !define MUI_LANGDLL_REGISTRY_KEY "Software\Blofeld"
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

  !insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER


  !insertmacro MUI_PAGE_INSTFILES
  ; !define MUI_FINISHPAGE_RUN
  ; !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
  ; !define MUI_FINISHPAGE_RUN_TEXT $(MsgStartSab)
  !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\NEWS.txt"
  !define MUI_FINISHPAGE_SHOWREADME_TEXT $(MsgShowRelNote)
  ;!define MUI_FINISHPAGE_LINK "View the BlofeldPlus Wiki"
  ;!define MUI_FINISHPAGE_LINK_LOCATION "http://wiki.blofeld.org/"
  ;!define MUI_FINISHPAGE_LINK $(MsgSupportUs)
  ;!define MUI_FINISHPAGE_LINK_LOCATION "http://www.blofeld.org/contribute/"

  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !define MUI_UNPAGE_COMPONENTSPAGE_NODESC
  !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

  ; Set supported languages
  !insertmacro MUI_LANGUAGE "English" ;first language is the default language
  !insertmacro MUI_LANGUAGE "French"
  !insertmacro MUI_LANGUAGE "German"
  !insertmacro MUI_LANGUAGE "Dutch"
  !insertmacro MUI_LANGUAGE "Swedish"


;--------------------------------
;Reserve Files

  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.

  !insertmacro MUI_RESERVEFILE_LANGDLL


; Function LaunchLink
  ; ExecShell "" "$INSTDIR\Blofeld.exe"
; FunctionEnd

;--------------------------------


Section "Blofeld" blofeld

SetOutPath "$INSTDIR"

; add files / whatever that need to be installed here.
File /r "..\dist\*"


WriteRegStr HKEY_LOCAL_MACHINE "SOFTWARE\Blofeld" "" "$INSTDIR"
WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\Blofeld" "DisplayName" "Blofeld (remove only)"
WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\Blofeld" "UninstallString" '"$INSTDIR\uninstall.exe"'
;WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\Blofeld" "DisplayIcon" '"$INSTDIR\need-a-.ico"'
; write out uninstaller
WriteUninstaller "$INSTDIR\Uninstall.exe"

  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application

    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Blofeld.lnk" "$INSTDIR\Blofeld.exe"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Blofeld - SafeMode.lnk" "$INSTDIR\Blofeld-console.exe" "--debug"
    WriteINIStr "$SMPROGRAMS\$STARTMENU_FOLDER\Blofeld Web Interface.url" "InternetShortcut" "URL" "http://localhost:8083/"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\Uninstall.exe"



  !insertmacro MUI_STARTMENU_WRITE_END


SectionEnd ; end of default section

Section /o "Apache CouchDB 1.2.0" couchdb
    SetOutPath $INSTDIR\lib
    ; IfFileExists "$PROGRAMFILES\Apache Software Foundation\CouchDB\bin\couchjs.exe" endCouchDB beginCouchDB
    ; Goto endCouchDB
    ; beginCouchDB:
    ; MessageBox MB_YESNO "Blofeld requires Apache CouchDB and you don't appear to have it installed. Would you like to install it now?" /SD IDYES IDNO endCouchDB
    File "setup-couchdb-1.2.0_otp_R15B.exe"
    ExecWait "$INSTDIR\lib\setup-couchdb-1.2.0_otp_R15B.exe"
    Delete "$INSTDIR\lib\setup-couchdb-1.2.0_otp_R15B.exe"
SectionEnd

Section /o "GStreamer v0.10.7" gstreamer
    SetOutPath $INSTDIR\lib
    ; IfFileExists "$PROGRAMFILES\OSSBuild\GStreamer\v0.10.7\bin\gst-launch.exe" endGStreamer beginGStreamer
    ; Goto endGStreamer
    ; beginGStreamer:
    ; MessageBox MB_YESNO "Blofeld requires GStreamer and you don't appear to have it installed. Would you like to install it now?" /SD IDYES IDNO endGStreamer
    File "GStreamer-WinBuilds-GPL-x86-Beta04-0.10.7.msi"
    ExecWait '"msiexec" /i "$INSTDIR\lib\GStreamer-WinBuilds-GPL-x86-Beta04-0.10.7.msi"'
    Delete "$INSTDIR\lib\GStreamer-WinBuilds-GPL-x86-Beta04-0.10.7.msi"
SectionEnd

Section /o $(MsgRunAtStart) startup
    CreateShortCut "$SMPROGRAMS\Startup\Blofeld.lnk" "$INSTDIR\Blofeld.exe" "-b0"
SectionEnd ;

Section /o $(MsgIcon) desktop
    CreateShortCut "$DESKTOP\Blofeld.lnk" "$INSTDIR\Blofeld.exe"
SectionEnd ; end of desktop icon section

;Section /o $(MsgAssoc) assoc
    ;${registerExtension} "$INSTDIR\nzb.ico" "$INSTDIR\Blofeld.exe" ".nzb" "NZB File"
    ;${registerExtension} "$INSTDIR\Blofeld.exe" ".nzb" "NZB File"
;SectionEnd ; end of file association section

; begin uninstall settings/section
UninstallText $(MsgUninstall)

Section "un.$(MsgDelProgram)" Uninstall
;make sure blofeld.exe isnt running..if so shut it down

    StrCpy $0 "blofeld.exe"
    DetailPrint "Searching for processes called '$0'"
    KillProc::FindProcesses
    StrCmp $1 "-1" wooops
    DetailPrint "-> Found $0 processes"

    StrCmp $0 "0" completed
    Sleep 1500

    StrCpy $0 "blofeld.exe"
    DetailPrint "Killing all processes called '$0'"
    KillProc::KillProcesses
    StrCmp $1 "-1" wooops
    DetailPrint "-> Killed $0 processes, failed to kill $1 processes"

    Goto completed

    wooops:
    DetailPrint "-> Error: Something went wrong :-("
    Abort

    completed:
    DetailPrint "Process Killed"


    ; add delete commands to delete whatever files/registry keys/etc you installed here.
    Delete "$INSTDIR\uninstall.exe"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Blofeld"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Blofeld"

    ; Delete installation files are carefully as possible
    ; Using just rmdir /r "$instdir" is considered unsafe!
    RMDir /r "$INSTDIR\interfaces\classic"
    RMDir /r "$INSTDIR\interfaces\default"
    RMDir "$INSTDIR\interfaces"
    Delete "$INSTDIR\lib\*.pyd"
    Delete "$INSTDIR\lib\API-MS-Win-Core-LocalRegistry-L1-1-0.dll"
    Delete "$INSTDIR\lib\blofeld.zip"
    Delete "$INSTDIR\lib\libg*.dll"
    Delete "$INSTDIR\lib\MPR.dll"
    Delete "$INSTDIR\lib\pythoncom26.dll"
    Delete "$INSTDIR\lib\pywintypes26.dll"
    RMDir "$INSTDIR\lib\"
    RMDir /r "$INSTDIR\views\_design\albums"
    RMDir /r "$INSTDIR\views\_design\artists"
    RMDir /r "$INSTDIR\views\_design\search"
    RMDir /r "$INSTDIR\views\_design\songs"
    RMDir "$INSTDIR\views\_design"
    RMDir "$INSTDIR\views"
    Delete "$INSTDIR\AUTHORS.txt"
    Delete "$INSTDIR\Blofeld-console.exe"
    Delete "$INSTDIR\Blofeld-service.exe"
    Delete "$INSTDIR\Blofeld.exe"
    Delete "$INSTDIR\blofeld.ico"
    Delete "$INSTDIR\ChangeLog.txt"
    Delete "$INSTDIR\COPYING.txt"
    Delete "$INSTDIR\INSTALL.txt"
    Delete "$INSTDIR\NEWS.txt"
    Delete "$INSTDIR\python26.dll"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\w9xpopen.exe"
    RMDir "$INSTDIR"

    !insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP

    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld - SafeMode.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld Web Interface.url"
    RMDir  "$SMPROGRAMS\$MUI_TEMP"

    Delete "$SMPROGRAMS\Startup\Blofeld.lnk"

    Delete "$DESKTOP\Blofeld.lnk"

    DeleteRegKey HKEY_CURRENT_USER  "Software\Blofeld"

SectionEnd ; end of uninstall section

Section "un.$(MsgDelSettings)" DelSettings
    Delete "$LOCALAPPDATA\blofeld\blofeld.cfg"
    RMDir "$LOCALAPPDATA\blofeld"
SectionEnd


Section "un.$(MsgDelLogs)" DelLogs
    RMDir /r "$LOCALAPPDATA\blofeld\log"
    RMDir "$LOCALAPPDATA\blofeld"
SectionEnd


Section "un.$(MsgDelCache)" DelCache
    RMDir /r "$LOCALAPPDATA\blofeld\cache"
    RMDir "$LOCALAPPDATA\blofeld"
SectionEnd

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
  !insertmacro SetSectionFlag ${blofeld} ${SF_RO}


IfFileExists "$PROGRAMFILES\Apache Software Foundation\CouchDB\bin\couchjs.exe" endCouchDB beginCouchDB
Goto endCouchDB
beginCouchDB:
!insertmacro SelectSection ${couchdb}
endCouchDB:


IfFileExists "$PROGRAMFILES\OSSBuild\GStreamer\v0.10.7\bin\gst-launch.exe" endGStreamer beginGStreamer
Goto endGStreamer
beginGStreamer:
!insertmacro SelectSection ${gstreamer}
endGStreamer:


;make sure blofeld.exe isnt running..if so abort
        loop:
        StrCpy $0 "Blofeld.exe"
		KillProc::FindProcesses
        StrCmp $0 "0" endcheck
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION $(MsgCloseSab) IDOK loop IDCANCEL exitinstall
        exitinstall:
        Abort
        endcheck:
FunctionEnd

; eof

;--------------------------------
;Language strings
; MsgWarnRunning 'Please close "Blofeld.exe" first'
  LangString MsgStartSab    ${LANG_ENGLISH} "Start Blofeld (hidden)"
  LangString MsgStartSab    ${LANG_DUTCH}   "Start Blofeld (verborgen)"
  LangString MsgStartSab    ${LANG_FRENCH}  "Lancer Blofeld (caché)"
  LangString MsgStartSab    ${LANG_GERMAN}  "Blofeld starten (unsichtbar)"
  LangString MsgStartSab    ${LANG_SWEDISH} "Starta Blofeld (dold)"

  LangString MsgShowRelNote ${LANG_ENGLISH} "Show Release Notes"
  LangString MsgShowRelNote ${LANG_DUTCH}   "Toon Vrijgave Bericht (Engels)"
  LangString MsgShowRelNote ${LANG_FRENCH}  "Afficher les notes de version"
  LangString MsgShowRelNote ${LANG_GERMAN}  "Versionshinweise anzeigen"
  LangString MsgShowRelNote ${LANG_SWEDISH} "Visa release noteringar"

  LangString MsgSupportUs   ${LANG_ENGLISH} "Support the project, Donate!"
  LangString MsgSupportUs   ${LANG_DUTCH}   "Steun het project, Doneer!"
  LangString MsgSupportUs   ${LANG_FRENCH}  "Supportez le projet, faites un don !"
  LangString MsgSupportUs   ${LANG_GERMAN}  "Bitte unterstützen Sie das Projekt durch eine Spende!"
  LangString MsgSupportUs   ${LANG_SWEDISH} "Donera och stöd detta projekt!"

  LangString MsgCloseSab    ${LANG_ENGLISH} "Please close $\"Blofeld.exe$\" first"
  LangString MsgCloseSab    ${LANG_DUTCH}   "Sluit $\"Blofeld.exe$\" eerst af"
  LangString MsgCloseSab    ${LANG_FRENCH}  "Quittez $\"Blofeld.exe$\" avant l\'installation, SVP"
  LangString MsgCloseSab    ${LANG_GERMAN}  "Schliessen Sie bitte zuerst $\"Blofeld.exe$\"."
  LangString MsgCloseSab    ${LANG_SWEDISH} "Var vänlig stäng $\"Blofeld.exe$\" först"

  LangString MsgUninstall   ${LANG_ENGLISH} "This will uninstall Blofeld from your system"
  LangString MsgUninstall   ${LANG_DUTCH}   "Dit verwijdert Blofeld van je systeem"
  LangString MsgUninstall   ${LANG_FRENCH}  "Ceci désinstallera Blofeld de votre système"
  LangString MsgUninstall   ${LANG_GERMAN}  "Dies entfernt Blofeld von Ihrem System"
  LangString MsgUninstall   ${LANG_SWEDISH} "Detta kommer att avinstallera Blofeld från systemet"

  LangString MsgRunAtStart  ${LANG_ENGLISH} "Run at startup"
  LangString MsgRunAtStart  ${LANG_DUTCH}   "Opstarten bij systeem start"
  LangString MsgRunAtStart  ${LANG_FRENCH}  "Lancer au démarrage"
  LangString MsgRunAtStart  ${LANG_GERMAN}  "Beim Systemstart ausführen"
  LangString MsgRunAtStart  ${LANG_SWEDISH} "Kör vid uppstart"

  LangString MsgIcon        ${LANG_ENGLISH} "Desktop Icon"
  LangString MsgIcon        ${LANG_DUTCH}   "Pictogram op bureaublad"
  LangString MsgIcon        ${LANG_FRENCH}  "Icône sur le Bureau"
  LangString MsgIcon        ${LANG_GERMAN}  "Desktop-Symbol"
  LangString MsgIcon        ${LANG_SWEDISH} "Skrivbordsikon"

  LangString MsgDelProgram  ${LANG_ENGLISH} "Delete Program"
  LangString MsgDelProgram  ${LANG_DUTCH}   "Verwijder programma"
  LangString MsgDelProgram  ${LANG_FRENCH}  "Supprimer le programme"
  LangString MsgDelProgram  ${LANG_GERMAN}  "Programm löschen"
  LangString MsgDelProgram  ${LANG_SWEDISH} "Ta bort programmet"

  LangString MsgDelSettings ${LANG_ENGLISH} "Delete Settings"
  LangString MsgDelSettings ${LANG_DUTCH}   "Verwijder instellingen"
  LangString MsgDelSettings ${LANG_FRENCH}  "Supprimer Paramètres"
  LangString MsgDelSettings ${LANG_GERMAN}  "Einstellungen löschen"
  LangString MsgDelSettings ${LANG_SWEDISH} "Ta bort inställningar"

  LangString MsgDelLogs     ${LANG_ENGLISH} "Delete Logs"
  LangString MsgDelLogs     ${LANG_DUTCH}   "Verwijder logging"
  LangString MsgDelLogs     ${LANG_FRENCH}  "Supprimer les logs"
  LangString MsgDelLogs     ${LANG_GERMAN}  "Protokoll löschen"
  LangString MsgDelLogs     ${LANG_SWEDISH} "Ta bort logg"

  LangString MsgDelCache    ${LANG_ENGLISH} "Delete Cache"
  LangString MsgDelCache    ${LANG_DUTCH}   "Verwijder Cache"
  LangString MsgDelCache    ${LANG_FRENCH}  "Supprimer le cache"
  LangString MsgDelCache    ${LANG_GERMAN}  "Cache löschen"
  LangString MsgDelCache    ${LANG_SWEDISH} "Ta bort temporär-mapp"

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd
