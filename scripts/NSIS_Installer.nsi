; -*- coding: latin-1 -*-
;
; Copyright 2008-2010 The Blofeld-Team <team@blofeld.org>
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
; Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

!addplugindir win\nsis\Plugins
!addincludedir win\nsis\Include

!include "MUI2.nsh"
; !include "registerExtension.nsh"


Name "${SAB_PRODUCT}"
OutFile "${SAB_FILE}"


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

  !define MUI_ICON "../blofeld.ico"


;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "../COPYING"
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
  !define MUI_FINISHPAGE_RUN
  !define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
  !define MUI_FINISHPAGE_RUN_TEXT $(MsgStartSab)
  !define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
  !define MUI_FINISHPAGE_SHOWREADME_TEXT $(MsgShowRelNote)
  ;!define MUI_FINISHPAGE_LINK "View the BlofeldPlus Wiki"
  ;!define MUI_FINISHPAGE_LINK_LOCATION "http://wiki.blofeld.org/"
  !define MUI_FINISHPAGE_LINK $(MsgSupportUs)
  !define MUI_FINISHPAGE_LINK_LOCATION "http://www.blofeld.org/contribute/"

  !insertmacro MUI_PAGE_FINISH

  !insertmacro MUI_UNPAGE_CONFIRM
  !define MUI_UNPAGE_COMPONENTSPAGE_NODESC
  !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

  ; Set supported languages
  !insertmacro MUI_LANGUAGE "English" ;first language is the default language
  ; !insertmacro MUI_LANGUAGE "French"
  ; !insertmacro MUI_LANGUAGE "German"
  ; !insertmacro MUI_LANGUAGE "Dutch"
  ; !insertmacro MUI_LANGUAGE "Swedish"


;--------------------------------
;Reserve Files

  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.

  !insertmacro MUI_RESERVEFILE_LANGDLL


Function LaunchLink
  ExecShell "" "$INSTDIR\Blofeld.exe"
FunctionEnd

;--------------------------------
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY

;make sure blofeld.exe isnt running..if so abort
        loop:
        StrCpy $0 "Blofeld.exe"
		; KillProc::FindProcesses
        StrCmp $0 "0" endcheck
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION $(MsgCloseSab) IDOK loop IDCANCEL exitinstall
        exitinstall:
        Abort
        endcheck:
FunctionEnd


Section "Blofeld" SecDummy
SetOutPath "$INSTDIR"

IfFileExists $INSTDIR\Blofeld.exe 0 endWarnExist
    IfFileExists $INSTDIR\language\us-en.txt endWarnExist 0
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION $(MsgOldQueue) IDOK endWarnExist IDCANCEL 0
        Abort
endWarnExist:

; add files / whatever that need to be installed here.
File /r "../dist\*"


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
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Blofeld - SafeMode.lnk" "$INSTDIR\Blofeld-console.exe"
    WriteINIStr "$SMPROGRAMS\$STARTMENU_FOLDER\Blofeld - Documentation.url" "InternetShortcut" "URL" "http://wiki.blofeld.org/"
    CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\Uninstall.exe"



  !insertmacro MUI_STARTMENU_WRITE_END


SectionEnd ; end of default section

Section /o $(MsgRunAtStart) startup
    CreateShortCut "$SMPROGRAMS\Startup\Blofeld.lnk" "$INSTDIR\Blofeld.exe" "-b0"
SectionEnd ;

Section $(MsgIcon) desktop
    CreateShortCut "$DESKTOP\Blofeld.lnk" "$INSTDIR\Blofeld.exe"
SectionEnd ; end of desktop icon section

; Section /o $(MsgAssoc) assoc
    ; ${registerExtension} "$INSTDIR\nzb.ico" "$INSTDIR\Blofeld.exe" ".nzb" "NZB File"
    ;${registerExtension} "$INSTDIR\Blofeld.exe" ".nzb" "NZB File"
; SectionEnd ; end of file association section

; begin uninstall settings/section
UninstallText $(MsgUninstall)

Section "un.$(MsgDelProgram)" Uninstall
;make sure blofeld.exe isnt running..if so shut it down

    StrCpy $0 "blofeld.exe"
    DetailPrint "Searching for processes called '$0'"
    ; KillProc::FindProcesses
    StrCmp $1 "-1" wooops
    DetailPrint "-> Found $0 processes"

    StrCmp $0 "0" completed
    Sleep 1500

    StrCpy $0 "blofeld.exe"
    DetailPrint "Killing all processes called '$0'"
    ; KillProc::KillProcesses
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
    Delete   "$INSTDIR\language\email-de-de.tmpl"
    Delete   "$INSTDIR\language\email-us-en.tmpl"
    Delete   "$INSTDIR\language\email-nl-du.tmpl"
    Delete   "$INSTDIR\language\email-fr-fr.tmpl"
    Delete   "$INSTDIR\language\email-sv-se.tmpl"
    Delete   "$INSTDIR\language\de-de.txt"
    Delete   "$INSTDIR\language\us-en.txt"
    Delete   "$INSTDIR\language\nl-du.txt"
    Delete   "$INSTDIR\language\fr-fr.txt"
    Delete   "$INSTDIR\language\sv-se.txt"
    RMDir    "$INSTDIR\language"
    RMDir /r "$INSTDIR\interfaces\Classic"
    RMDir /r "$INSTDIR\interfaces\Plush"
    RMDir /r "$INSTDIR\interfaces\smpl"
    RMDir /r "$INSTDIR\interfaces\Mobile"
    RMDir /r "$INSTDIR\interfaces\wizard"
    RMDir "$INSTDIR\interfaces"
    RMDir /r "$INSTDIR\win\par2"
    RMDir /r "$INSTDIR\win\unrar"
    RMDir /r "$INSTDIR\win\unzip"
    RMDir /r "$INSTDIR\win"
    Delete "$INSTDIR\licenses\*.txt"
    Delete "$INSTDIR\licenses\Python\*.txt"
    RMDir "$INSTDIR\licenses\Python"
    RMDir "$INSTDIR\licenses"
    Delete "$INSTDIR\lib\libeay32.dll"
    Delete "$INSTDIR\lib\pywintypes25.dll"
    Delete "$INSTDIR\lib\ssleay32.dll"
    Delete "$INSTDIR\lib\blofeld.zip"
    Delete "$INSTDIR\lib\*.pyd"
    RMDir  /r "$INSTDIR\lib\"
    Delete "$INSTDIR\CHANGELOG.txt"
    Delete "$INSTDIR\COPYRIGHT.txt"
    Delete "$INSTDIR\email.tmpl"
    Delete "$INSTDIR\GPL2.txt"
    Delete "$INSTDIR\GPL3.txt"
    Delete "$INSTDIR\INSTALL.txt"
    Delete "$INSTDIR\ISSUES.txt"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\MSVCR71.dll"
    Delete "$INSTDIR\nzb.ico"
    Delete "$INSTDIR\PKG-INFO"
    Delete "$INSTDIR\python25.dll"
    Delete "$INSTDIR\python26.dll"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\Blofeld-console.exe"
    Delete "$INSTDIR\Blofeld.exe"
    Delete "$INSTDIR\Sample-PostProc.cmd"
    Delete "$INSTDIR\Uninstall.exe"
    Delete "$INSTDIR\w9xpopen.exe"
    RMDir "$INSTDIR"

    !insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP

    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld - SafeMode.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Blofeld - Documentation.url"
    RMDir  "$SMPROGRAMS\$MUI_TEMP"

    Delete "$SMPROGRAMS\Startup\Blofeld.lnk"

    Delete "$DESKTOP\Blofeld.lnk"

    DeleteRegKey HKEY_CURRENT_USER  "Software\Blofeld"

    ; ${unregisterExtension} ".nzb" "NZB File"


SectionEnd ; end of uninstall section

Section "un.$(MsgDelSettings)" DelSettings
    Delete "$LOCALAPPDATA\blofeld\blofeld.ini"
    RMDir /r "$LOCALAPPDATA\blofeld\admin"
SectionEnd


Section "un.$(MsgDelLogs)" DelLogs
    RMDir /r "$LOCALAPPDATA\blofeld\logs"
SectionEnd


Section "un.$(MsgDelCache)" DelCache
    RMDir /r "$LOCALAPPDATA\blofeld\cache"
    RMDir "$LOCALAPPDATA\blofeld"
SectionEnd

; eof

;--------------------------------
;Language strings
; MsgWarnRunning 'Please close "Blofeld.exe" first'
  LangString MsgStartSab    ${LANG_ENGLISH} "Start Blofeld (hidden)"
  LangString MsgStartSab    ${LANG_DUTCH}   "Start Blofeld (verborgen)"
  LangString MsgStartSab    ${LANG_FRENCH}  "Lancer Blofeld (cach�)"
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
  LangString MsgSupportUs   ${LANG_GERMAN}  "Bitte unterst�tzen Sie das Projekt durch eine Spende!"
  LangString MsgSupportUs   ${LANG_SWEDISH} "Donera och st�d detta projekt!"

  LangString MsgCloseSab    ${LANG_ENGLISH} "Please close $\"Blofeld.exe$\" first"
  LangString MsgCloseSab    ${LANG_DUTCH}   "Sluit $\"Blofeld.exe$\" eerst af"
  LangString MsgCloseSab    ${LANG_FRENCH}  "Quittez $\"Blofeld.exe$\" avant l\'installation, SVP"
  LangString MsgCloseSab    ${LANG_GERMAN}  "Schliessen Sie bitte zuerst $\"Blofeld.exe$\"."
  LangString MsgCloseSab    ${LANG_SWEDISH} "Var v�nlig st�ng $\"Blofeld.exe$\" f�rst"

  LangString MsgOldQueue    ${LANG_ENGLISH} "                  >>>> WARNING <<<<$\r$\n$\r$\nIf not empty, download your current queue with the old program.$\r$\nThe new program will ignore your current queue!"
  LangString MsgOldQueue    ${LANG_DUTCH}   "                  >>>> WAARSCHUWING <<<<$\r$\n$\r$\nIndien niet leeg, download eerst de gehele huidige wachtrij met het oude programma.$\r$\nHet nieuwe programma zal je huidige wachtrij negeren!"
  LangString MsgOldQueue    ${LANG_FRENCH}  "                  >>>> ATTENTION <<<<$\r$\n$\r$\nsi votre file d'attente de t�l�chargement n'est pas vide, terminez la avec la version pr�c�dente du programme.$\r$\nLa nouvelle version l'ignorera!"
  LangString MsgOldQueue    ${LANG_GERMAN}  "                  >>>> ACHTUNG <<<<$\r$\n$\r$\nWarten Sie, bis das alte Programm alle Downloads fertiggestellt hat.$\r$\nDas neue Programm wird die noch ausstehenden Downloads ignorieren!"
  LangString MsgOldQueue    ${LANG_SWEDISH} "                  >>>> VARNING <<<<$\r$\n$\r$\nOm k�n inte �r tom, h�mta din nuvarande k� med det gamla programmet.$\r$\nDet nya programmet kommer att ignorera din nuvarande k�!"

  LangString MsgUninstall   ${LANG_ENGLISH} "This will uninstall Blofeld from your system"
  LangString MsgUninstall   ${LANG_DUTCH}   "Dit verwijdert Blofeld van je systeem"
  LangString MsgUninstall   ${LANG_FRENCH}  "Ceci d�sinstallera Blofeld de votre syst�me"
  LangString MsgUninstall   ${LANG_GERMAN}  "Dies entfernt Blofeld von Ihrem System"
  LangString MsgUninstall   ${LANG_SWEDISH} "Detta kommer att avinstallera Blofeld fr�n systemet"

  LangString MsgRunAtStart  ${LANG_ENGLISH} "Run at startup"
  LangString MsgRunAtStart  ${LANG_DUTCH}   "Opstarten bij systeem start"
  LangString MsgRunAtStart  ${LANG_FRENCH}  "Lancer au d�marrage"
  LangString MsgRunAtStart  ${LANG_GERMAN}  "Beim Systemstart ausf�hren"
  LangString MsgRunAtStart  ${LANG_SWEDISH} "K�r vid uppstart"

  LangString MsgIcon        ${LANG_ENGLISH} "Desktop Icon"
  LangString MsgIcon        ${LANG_DUTCH}   "Pictogram op bureaublad"
  LangString MsgIcon        ${LANG_FRENCH}  "Ic�ne sur le Bureau"
  LangString MsgIcon        ${LANG_GERMAN}  "Desktop-Symbol"
  LangString MsgIcon        ${LANG_SWEDISH} "Skrivbordsikon"

  LangString MsgAssoc       ${LANG_ENGLISH} "NZB File association"
  LangString MsgAssoc       ${LANG_DUTCH}   "NZB bestanden koppelen aan Blofeld"
  LangString MsgAssoc       ${LANG_FRENCH}  "Association des fichiers NZB"
  LangString MsgAssoc       ${LANG_GERMAN}  "Mit NZB-Dateien verkn�pfen"
  LangString MsgAssoc       ${LANG_SWEDISH} "NZB Filassosication"

  LangString MsgDelProgram  ${LANG_ENGLISH} "Delete Program"
  LangString MsgDelProgram  ${LANG_DUTCH}   "Verwijder programma"
  LangString MsgDelProgram  ${LANG_FRENCH}  "Supprimer le programme"
  LangString MsgDelProgram  ${LANG_GERMAN}  "Programm l�schen"
  LangString MsgDelProgram  ${LANG_SWEDISH} "Ta bort programmet"

  LangString MsgDelSettings ${LANG_ENGLISH} "Delete Settings"
  LangString MsgDelSettings ${LANG_DUTCH}   "Verwijder instellingen"
  LangString MsgDelSettings ${LANG_FRENCH}  "Supprimer Param�tres"
  LangString MsgDelSettings ${LANG_GERMAN}  "Einstellungen l�schen"
  LangString MsgDelSettings ${LANG_SWEDISH} "Ta bort inst�llningar"

  LangString MsgDelLogs     ${LANG_ENGLISH} "Delete Logs"
  LangString MsgDelLogs     ${LANG_DUTCH}   "Verwijder logging"
  LangString MsgDelLogs     ${LANG_FRENCH}  "Supprimer les logs"
  LangString MsgDelLogs     ${LANG_GERMAN}  "Protokoll l�schen"
  LangString MsgDelLogs     ${LANG_SWEDISH} "Ta bort logg"

  LangString MsgDelCache    ${LANG_ENGLISH} "Delete Cache"
  LangString MsgDelCache    ${LANG_DUTCH}   "Verwijder Cache"
  LangString MsgDelCache    ${LANG_FRENCH}  "Supprimer le cache"
  LangString MsgDelCache    ${LANG_GERMAN}  "Cache l�schen"
  LangString MsgDelCache    ${LANG_SWEDISH} "Ta bort tempor�r-mapp"

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
FunctionEnd