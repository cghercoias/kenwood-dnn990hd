# 04 — The official 1.8.0 updater: what it does, and why it is not the fix

Kept as a record, because "just reflash the firmware" is everybody's first instinct — and on this unit
it is wrong for reasons that are specific to the hardware.

## What the package is

| File | Size | Notes |
|---|---|---|
| `update.kw` | 506,296,726 B | the vendor updater payload (a zip) |
| `programinfo.bin` | 156 B | version descriptor the unit's updater reads |

**It is byte-identical to what is already installed.** Verified by comparing the package against the
running `/system` and the NAND image: `build.prop` (`998a8842…`), `boot.img` (`a134587f…`),
`bootloader.img` (`8725b2ef…`) and 20 of 20 randomly chosen files all match. This package restores a
clean `/system`; it does not change the version, because **1.8.0 is the last release Kenwood produced
for the DNN990HD**.

That is also why **[Update]** is greyed out: the unit compares its own version with `programinfo.bin`,
finds nothing newer, and refuses. There is no newer firmware to force, and no way to make the UI
accept this one.

## Procedure, for completeness

1. `update.kw` and `programinfo.bin` at the **root** of a USB stick (not inside a folder), in the
   unit's front USB port. Power stays connected for the whole run (~15 min).
2. HOME → source launcher → **STANDBY**. (Touch, or the front panel keys — the keys work on this unit;
   only EJECT is inert, because no disc mechanism is fitted.)
3. Menu → **Setup** → **Software** → **Software Information** — note the version shown.
4. **[Update]**, accept the confirmation. The screen goes blank briefly, then progress runs for about
   fifteen minutes.
5. When "Update completed" appears: remove the stick, restart.

## Why it does not fix the boot loop

- It rewrites `/system`. This fault is in `/data` (`ndda3`), which this updater never touches — see
  [docs/07](07-data-persistence-and-bootloop.md).
- It **restores the stock `vmute`**, so the panel goes dark again. The fix in
  [docs/02](02-panel-dark-fix.md) must be re-applied afterwards.
- It may not preserve the adb configuration that makes the unit serviceable at all.

## Recovery paths, if you run it anyway

**A — adb came back**

```sh
adb devices                                  # expect the unit's serial, state "device"
adb push patches/vmute /sdcard/vmute
adb shell
mount -o remount,rw /dev/block/ndda2 /system
cat /system/bin/vmute > /data/local/tmp/vmute.orig
cat /sdcard/vmute > /system/bin/vmute
chmod 755 /system/bin/vmute
sync && reboot
```

Then, if the Kenwood apps do not start on their own: `pm enable com.jvckenwood.kwlauncher`,
`pm enable jp.co.kenwood.multimediaplayer`, `pm disable com.android.launcher`.

**B — no adb, only mass storage (`18D1:B058`)**

That is FWDN territory: boot-strap pads bridged (under the heatsink on this board), `140E:B068`, and
the FAI container format. Restore `/system` from the NAND image **per partition**, never whole.

**C — the unit does not boot at all**

Restore partitions one at a time:

```sh
dd if=/mnt/usb/nand.img of=/dev/block/ndda2 bs=512 skip=20512 count=962560   # /system
```

> Do **not** `dd` the whole image back over `/dev/block/ndda`. Its MBR describes three of the fifteen
> partitions and the generic `0x06` entry breaks LK's boot path on this board. It is the most
> expensive mistake available on this hardware — see
> [docs/03](03-nand-backup-and-restore.md#never-restore-the-whole-image).

## Outcome on this unit

The update was never needed and was not run to completion: the package matches the installed system,
so there was nothing to gain and three things to lose (the panel, adb, and the current `/system`
state). The unit is 1.8.0 and always was.
