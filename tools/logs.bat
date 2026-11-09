@echo off
setlocal
set "ADB=C:\Users\Catalin\AppData\Local\hermes\cache\scratch\platform-tools\platform-tools\adb.exe"
set "OUT=C:\fwdn\logs\last"

if not exist "%OUT%" mkdir "%OUT%"
"%ADB%" root >nul 2>&1
ping -n 3 127.0.0.1 >nul
"%ADB%" wait-for-device

echo Grabbing state into %OUT% ...
"%ADB%" shell dmesg                    > "%OUT%\dmesg.txt"    2>&1
"%ADB%" shell logcat -d -v time        > "%OUT%\logcat.txt"   2>&1
"%ADB%" shell logcat -d -b all -v time > "%OUT%\logcat_all.txt" 2>&1
"%ADB%" shell getprop                  > "%OUT%\props.txt"    2>&1
"%ADB%" shell "cat /proc/cmdline"      > "%OUT%\cmdline.txt"  2>&1
"%ADB%" shell "cat /proc/interrupts"   > "%OUT%\interrupts.txt" 2>&1
"%ADB%" shell "dumpsys SurfaceFlinger" > "%OUT%\surfaceflinger.txt" 2>&1
"%ADB%" shell "dumpsys power"          > "%OUT%\power.txt"    2>&1
"%ADB%" shell "ps"                     > "%OUT%\ps.txt"       2>&1
"%ADB%" shell "ls -l /dev/panelcom /dev/syscom /dev/kwgpio /dev/spidev2.0" > "%OUT%\devs.txt" 2>&1
"%ADB%" shell "for f in /sys/class/graphics/fb0/*; do echo $f = $(cat $f 2>/dev/null); done" > "%OUT%\fb0.txt" 2>&1
"%ADB%" shell "screencap -p /data/local/tmp/snap.png"
"%ADB%" pull /data/local/tmp/snap.png "%OUT%\snap.png" >nul 2>&1

echo Done. Files:
dir /b "%OUT%"
echo.
echo Open the folder with:  explorer %OUT%
pause
