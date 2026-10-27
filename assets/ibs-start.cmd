@echo off
wpeinit
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 1 /f >nul
reg add HKCU\Console /v InsertMode /t REG_DWORD /d 1 /f >nul
reg add HKCU\Console /v CtrlKeyShortcutsDisabled /t REG_DWORD /d 0 /f >nul
start "" X:\Windows\System32\ibs-clipboard.exe
start "Prompt WinRE" cmd.exe
X:\sources\recovery\recenv.exe
