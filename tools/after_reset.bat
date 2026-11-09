@echo off
title Radio - restore the Kenwood home screen after a factory reset
cd /d "%~dp0"
set ADB=%~dp0platform-tools\adb.exe

echo ==========================================
echo  After a factory reset the radio comes up
echo  on the stock Android launcher. This puts
echo  the Kenwood menus back as HOME.
echo ==========================================
echo.
echo Looking for the radio (plug USB in, wait)...
"%ADB%" wait-for-device

echo.
echo [1/3] Disabling the stock Android launcher...
"%ADB%" shell pm disable com.android.launcher
echo [2/3] Enabling the Kenwood launcher and player...
"%ADB%" shell pm enable com.jvckenwood.kwlauncher
"%ADB%" shell pm enable jp.co.kenwood.multimediaplayer

echo.
echo [3/3] Current state (only com.android.launcher should be listed as disabled):
"%ADB%" shell pm list packages -d

echo.
echo Restarting the radio...
"%ADB%" reboot

echo.
echo Done. The Kenwood menus come back in about a minute.
echo If the screen stays on the Android launcher, run this file again.
pause
