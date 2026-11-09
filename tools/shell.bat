@echo off
title KENWOOD DNN990HD - root shell
set "ADB=C:\Users\Catalin\AppData\Local\hermes\cache\scratch\platform-tools\platform-tools\adb.exe"

"%ADB%" get-state >nul 2>&1
if errorlevel 1 (
  echo Unit not detected on USB. Check the cable and that the unit is powered.
  pause
  exit /b 1
)

echo Requesting root...
"%ADB%" root
ping -n 3 127.0.0.1 >nul
"%ADB%" wait-for-device
"%ADB%" shell id

echo.
echo ================================================================
echo  You are now in a root shell on the radio.
echo  Handy commands (no tab completion here, type them in full):
echo    dmesg ^| tail -30          kernel messages
echo    logcat -d ^| tail -50      Android log
echo    getprop ^| grep -i QB      quickboot props
echo    dumpsys SurfaceFlinger    layer stack / display state
echo    cat /sys/class/graphics/fb0/pan
echo    ls /dev/panelcom /dev/syscom /dev/kwgpio
echo  exit   leaves the shell
echo ================================================================
echo.

"%ADB%" shell
echo.
echo Shell closed.
pause
