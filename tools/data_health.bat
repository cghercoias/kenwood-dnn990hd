@echo off
setlocal
REM DNN990HD /data health probe. Run with the unit booted and CN902 connected.
REM Run once, reboot the unit, run again: the second run reports whether /data persists.
set "ADB=C:\fwdn\platform-tools\adb.exe"
set "LOG=C:\fwdn\probe\data_health.txt"
set "MARK=/data/local/tmp/persist_probe.txt"
if not exist "C:\fwdn\probe" mkdir "C:\fwdn\probe"

"%ADB%" kill-server >nul 2>&1
"%ADB%" start-server >nul 2>&1

echo === adb devices === > "%LOG%" 2>&1
"%ADB%" devices >> "%LOG%" 2>&1
"%ADB%" shell echo probe >nul 2>&1
if errorlevel 1 goto nodevice

echo. >> "%LOG%"
echo === identity === >> "%LOG%"
"%ADB%" shell "getprop ro.build.display.id; getprop persist.sys.usb.config; getprop sys.boot_completed; getprop ro.setupwizard.mode" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === mount === >> "%LOG%"
"%ADB%" shell "mount" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === df === >> "%LOG%"
"%ADB%" shell "df" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === partitions (sectors) === >> "%LOG%"
"%ADB%" shell "cat /proc/partitions" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === kernel: nand / ext4 / fsck / setup_fs === >> "%LOG%"
"%ADB%" shell "dmesg | grep -iE 'nand|ext4|fsck|bad block|superblock|setup_fs|format|rebuild' | tail -80" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === dmesg tail === >> "%LOG%"
"%ADB%" shell "dmesg | tail -40" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === /data top level === >> "%LOG%"
"%ADB%" shell "ls -la /data" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === /data/system (provisioning lives here) === >> "%LOG%"
"%ADB%" shell "ls -la /data/system 2>/dev/null | head -40" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === /data/property === >> "%LOG%"
"%ADB%" shell "ls -la /data/property 2>/dev/null; echo ---; cat /data/property/* 2>/dev/null | head -40" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === persistence probe === >> "%LOG%"
"%ADB%" shell "if [ -f %MARK% ]; then echo MARKER_PRESENT; cat %MARK%; else echo MARKER_ABSENT; fi" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === writing fresh marker === >> "%LOG%"
"%ADB%" shell "date > %MARK%; cat %MARK%" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === is anything in /data writable at all === >> "%LOG%"
"%ADB%" shell "echo test > /data/local/tmp/wtest 2>&1; cat /data/local/tmp/wtest 2>&1" >> "%LOG%" 2>&1

echo. >> "%LOG%"
echo === log saved: %LOG% === >> "%LOG%"

echo.
type "%LOG%"
echo.
echo ---------------------------------------------------------------
echo Saved to: %LOG%
echo If it says MARKER_ABSENT, that was the first run: reboot the unit,
echo then run this script again. MARKER_PRESENT on run two = /data persists.
echo ---------------------------------------------------------------
pause
exit /b 0

:nodevice
echo NO ADB DEVICE FOUND.
echo.
echo  1. Confirm the cable is in CN902 (internal USB device port) and the laptop end is seated.
echo  2. Try a DIFFERENT physical USB port on the laptop (this host latches dead ports).
echo  3. Re-run this script.
echo.
pause
exit /b 1
