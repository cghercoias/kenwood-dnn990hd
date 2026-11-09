# patches

## `vmute` — the panel fix

`vmute` is a drop-in replacement for `/system/bin/vmute`. The stock file is a 275-byte shell script
(md5 `acadb8e58e5f370bd224ee7516332b49`) that issues one `ioctl` on `/dev/kwgpio` and switches the
LCD video line off. SurfaceFlinger `exec`s it after boot-complete and does not check what it does.

The replacement is the same size (275 bytes, md5 `2b95ede435392cf62eaccf8b69b30701`) and exits 0
without touching GPIO.

### Apply

```sh
adb push patches/vmute /sdcard/vmute
adb shell
mount -o remount,rw /dev/block/ndda2 /system
cat /system/bin/vmute > /data/local/tmp/vmute.orig
cat /sdcard/vmute > /system/bin/vmute
chmod 755 /system/bin/vmute
sync
mount -o remount,ro /dev/block/ndda2 /system
reboot
```

Requirements: `/system` mounted rw, the file must stay executable, and the shebang
`#!/system/bin/sh` must be the first line (no CRLF — this file is LF and must stay LF).

### Revert

```sh
adb shell
mount -o remount,rw /dev/block/ndda2 /system
cat /data/local/tmp/vmute.orig > /system/bin/vmute
chmod 755 /system/bin/vmute
sync && reboot
```

### When it needs re-applying

Only after something rewrites `/system`:

- a vendor firmware update (restores stock `vmute`)
- an FWDN restore of `/system`
- reflashing a whole-NAND image

A factory data reset does **not** undo it, and neither does the `/data` repair in
[docs/07](../docs/07-data-persistence-and-bootloop.md).

### Not included here

The original Kenwood script is not redistributed. Your unit already has it — copy it to
`/data/local/tmp/vmute.orig` before patching, which is both your backup and your verification
(md5 must read `acadb8e58e5f370bd224ee7516332b49`; if it does not, you are on different firmware and
should stop and look at what your `vmute` actually does before replacing it).
