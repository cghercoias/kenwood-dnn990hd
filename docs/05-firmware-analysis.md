# 05 — Firmware analysis: teardown of `update.kw` and the boot image

*(Originally written as the phase-1 report; kept in its original form because the numbers are the
point. Every path in it is the analysis workspace on the bench machine, not this repository.)*

Generated 2026-11-08 on the bench laptop. **No file in `raw/` was modified.**
All extracted/modified artifacts are under `out/`.

## 0. Workspace as actually built

| path | what | notes |
|---|---|---|
| `C:\dnn990hd_work\raw\nand_20261108.img` | whole-chip NAND image, 2,050,490,368 B | **NTFS hardlink** to `C:\fwdn\backup\nand_20261108.img` — same data, no extra 2 GB used. MD5 `38e463ef28e95c2b02cccf4397936084` |
| `C:\dnn990hd_work\raw\update.kw` | vendor firmware package, 506,296,726 B | copy of the Kenwood 1.8.0 package. MD5 verified against source |
| `out\firmware\` | `boot.img`, `bootloader.img`, `recovery_recovery-from-boot.p`, `system_build.prop`, `META-INF_MANIFEST.MF` | extracted from the package |
| `out\boot\` | `kernel.bin`, `ramdisk.gz`, `ramdisk.cpio` | parsed out of `boot.img` |
| `out\ramdisk\` | 40 files / 10 dirs unpacked cpio | `init.rc`, `default.prop`, `sbin/adbd`, `lib/modules/*.ko`, … |
| `out\zip_index.txt` | 14,372 entry names | full package manifest |
| `out\inventory.txt` | Kenwood binaries/libs/APKs | absolute paths |

**Tooling deviation:** `binwalk`, `abootimg`, `mkbootimg` and `cpio` are **not installed** on this
Windows host, and there is no Linux userland here. Their work was done with purpose-written
pure-Python parsers (Android boot header, gzip, cpio "newc", ext4 superblock, magic scanner).
Results are byte-exact and were cross-checked against `file(1)`. Nothing was installed.

---

## 1. Identity, kernel, partition layout

| item | value |
|---|---|
| Android | **4.0.4 / IMM76D**, build `binks_v8-userdebug 4.0.4 IMM76D eng.root.20181003.133037 test-keys` |
| Linux kernel | **3.0.8-tcc** `#3 PREEMPT Wed Oct 3 18:03:44 JST 2018`, built by `root@Prominence`, gcc 4.4.3 |
| SoC | Telechips **TCC8801** (microarchitecture not recorded in the unit's own logs — do not assume Cortex-A5/A8 without checking `/proc/cpuinfo` on your unit) |
| Main NAND | Toshiba `TH58NVG4S0FTAK0`, 2 GiB → `/dev/block/ndda` |
| Second device | `/dev/block/mtdblock0`, 83,886,080 B (80 MB), imaged separately |
| Partition driver | `tcc_nand_v8.ko` + `tcc_init_nand_v8.ko` (in the ramdisk) |

### Partition table — authoritative (512-byte sectors, verified to reconcile)

The kernel uses a **static** table; the MBR only declares 3 entries plus an extended chain, so
`/sys/class/block/nddaN/{start,size}` is the reference. Sizes below are derived from consecutive
starts and the sum equals the device size exactly.

| name | start sector | size (sectors) | size | end sector | role |
|---|---|---|---|---|---|
| ndda1 | 32 | 20,480 | 10.0 MB | 20,512 | `boot` — `ANDROID!` header confirmed |
| ndda2 | 20,512 | 962,560 | 470.0 MB | 983,072 | `/system` ext4 |
| ndda3 | 983,072 | 716,800 | 350.0 MB | 1,699,872 | `/data` ext4 |
| ndda4 | 1,699,872 | 32 | 16 KB | 1,699,904 | MBR artefact |
| ndda5 | 1,699,904 | 307,232 | 150.0 MB | 2,007,136 | `/cache` ext4 |
| ndda6 | 2,007,136 | 20,512 | 10.0 MB | 2,027,648 | **recovery — ZERO FILL** |
| ndda7 | 2,027,648 | 10,272 | 5.0 MB | 2,037,920 | unused / unknown |
| ndda8 | 2,037,920 | 10,272 | 5.0 MB | 2,048,192 | unused / unknown |
| ndda9 | 2,048,192 | 2,080 | 1.0 MB | 2,050,272 | unused / unknown |
| ndda10 | 2,050,272 | 2,080 | 1.0 MB | 2,052,352 | unused / unknown |
| ndda11 | 2,052,352 | 307,232 | 150.0 MB | 2,359,584 | hibernate **snapshot** (carries a stale `/data` superblock copy) |
| ndda12 | 2,359,584 | 20,512 | 10.0 MB | 2,380,096 | `/.sysinfo` ext4 |
| ndda13 | 2,380,096 | 16,416 | 8.0 MB | 2,396,512 | `.garmin` ext4 |
| ndda14 | 2,396,512 | 2,080 | 1.0 MB | 2,398,592 | snapshot header area |
| ndda15 | 2,398,592 | 1,606,272 | 784.3 MB | 4,004,864 | large region, zero fill (reserved/unused) |

Reconciliation: last end 4,004,864 sectors × 512 = **2,050,490,368 B = image size**. ✔

`file(1)` independently reports the MBR as: partition 2 at sector 20,512 (962,560 sectors),
partition 3 at 983,072 (716,800 sectors), partition 4 type `0xf` at 1,699,872 — consistent.

---

## 2. Boot image and kernel cmdline

`out/firmware/boot.img` — 9,838,592 B, MD5 `a134587f19ac78f14733aed347783bf6`

| header field | value |
|---|---|
| magic | `ANDROID!` |
| page size | 2048 |
| kernel size / load | 8,093,284 B @ **0x40008000** |
| ramdisk size / load | 1,741,626 B @ **0x41000000** |
| second stage size / load | 0 @ 0x40f00000 |
| tags address | **0x40000100** |
| board name | (empty) |

### Cmdline — two different ones, and the difference matters

| source | cmdline |
|---|---|
| **Vendor package** `boot.img` | `vmalloc=256M console=null vmalloc=256M` |
| **On the chip right now** (ndda1 inside the image) | `vmalloc=256M console=ttyTCC0,115200n8 vmalloc=256M` |

So Kenwood ships the console **explicitly nulled** (`console=null`), and this unit has already been
re-flashed with a console-enabled boot (ramdisk 1,735,786 B vs 1,741,626 B in the package — a
re-packed ramdisk, ~5.8 KB smaller). **The kernel console is already live on this unit.**

---

## 3. USB gadget and console configuration

### `default.prop` (verbatim, 129 B)

```
#
# ADDITIONAL_DEFAULT_PROPERTIES
#
ro.secure=1
ro.allow.mock.location=0
ro.debuggable=1
persist.sys.usb.config=mass_storage,adb
```

Consequences: `ro.debuggable=1` ⇒ **adbd runs as root** with no `adb root` step; the default USB
composition is already `mass_storage,adb` ⇒ VID:PID `18D1:DEED`, which is the combination needed to
get a shell back after any wipe that rebuilds `/data`.

### `init.tcc8800.usb.rc` — full VID/PID map

| `sys.usb.config` | VID:PID | adbd |
|---|---|---|
| `adb` | `18D1:D00D` | started |
| `mass_storage` | `18D1:B058` | stopped |
| `mass_storage,adb` | `18D1:DEED` | started |
| `rndis` | `140E:A020` | stopped |
| `rndis,adb` | `140E:A021` | started |

RNDIS descriptors: manufacturer `Telechips`, vendorID `140e`, `wceis 1`.

### Console service

`init.rc` (and identically `init.factory.rc`):

```
service console /system/bin/sh
    console
    start console
```

With `console=ttyTCC0,115200n8` in the cmdline, init binds `/dev/console` to **ttyTCC0** and starts
a **root shell** on it. Nothing is disabled — the shell is waiting for a UART that isn't wired yet.

### UART assignment on this board

| device | user | evidence |
|---|---|---|
| `ttyTCC0` | **kernel console / root shell** | cmdline |
| `ttyTCC1` | **Bluetooth** | `init.tcc8800.rc`: `hciattach -n -s 3000000 /dev/ttyTCC1 bcsp 3000000`, `bccmd -t bcsp -d /dev/ttyTCC1` |
| `ttyTCC3` | **GPS** | `setprop ro.kernel.android.gps ttyTCC3`, `chmod 0666 /dev/ttyTCC3` |

`ueventd.tcc8800.rc` grants `0666` to `ttyTCC1`, `ttyTCC2`, `ttyUSB0`; `ttyTCC3` is commented out.

**Prior bench result (do not repeat blindly):** probing **CN102 pin 3** produced ~65 ms of boot
ROM/LK output then silence, with stop-bit validity 41–47.9 %. That is consistent with that pad being
**ttyTCC1 (Bluetooth)** at a different rate, not the console. The hunt for the **ttyTCC0** pads is
still open and is the single highest-value hardware lead for a fallback shell.

---

## 4. Kenwood-specific components in `/system`

Counts: **15** Kenwood binaries in `system/bin`, **28** Kenwood `.so` in `system/lib`, **17** APKs.
(Context: the whole `/system` has 271 `.so` and 64 APKs — the rest is stock Android 4.0.4.)

### Daemons and tools — `system/bin`

| binary | role (from name / prior on-device evidence) |
|---|---|
| `syscomd` / `syscomd.demo` | **front-panel MCU (Syscom) daemon** — keys, panel motor, power/amp control |
| `panelcomd` / `panelcomd.demo` | **LCD panel controller daemon** — 800×480 CPT `CLAA069LA0ACW`, backlight, LCD enable |
| `kwplayer` | Kenwood media player engine |
| `kwresetter` | reset/watchdog handling |
| `kwupdatecheck` | **consumes `update.kw` + `programinfo.bin`** — the vendor updater entry point |
| `kwclient` | client to the Kenwood system service |
| `kw_vbusctrl` | USB VBUS control |
| `kw_qbwd`, `kw_qbcounter`, `kw_mkqb_timeinit` | **quickboot** (hibernate) watchdog/counter/time base — related to `ro.QB.enable` and ndda11 |
| `kw_lostdel`, `kwdellost` | housekeeping for lost+found |
| `kw_mountnotf` | suppresses mount notifications |

### Kernel modules in the ramdisk (`/lib/modules`)

`syscom.ko`, `panelcom.ko`, `kwgpio.ko`, `kwram.ko`, `kwtmcdec.ko`, `dec_gpio.ko`,
`vfullkeyboard.ko`, `ufsd.ko`, `tcc_nand_v8.ko`, `tcc_init_nand_v8.ko`,
`ehci-hcd.ko`, `ohci-hcd.ko`

`syscom.ko` + `panelcom.ko` are **kernel modules**, not Android services: the front panel and LCD are
driven from kernel space. That is why a UI-only fault model fails on this unit.

### Native libraries — `system/lib`

`libkw_Application.so`, `libkw_System.so`, `libkw_Controller.so`, `libkw_Framework.so`,
`libkw_Middleware0..4.so`, `libkw_MultimediaCore.so`, `libkw_mediaplayer.so`, `libkw_AbstractionDevice.so`,
`libkw_ProcessCommProxy.so`, `libkw_SystemCallWrapper.so`, `libkw_UIDomain.so`, `libkw_Testmode.so`,
`libkw_i2c_api.so`, `libkw_spi_api.so`, `libkw_videocontrol.so`, `libkw_opening_logo.so`,
`libkw_tmcdecint.so`, `libkw_threadutility.so`, `libkw_iconv.so`,
`libKWGUIMain.so`, `libKwSkia.so`, `libNaviCore.so`, `libKnlNaviInterface.so`, `libKwNaviVoice.so`

Key symbols known from prior work: `libkw_System.so` exports `SyscomWd`, `StartSyscom`,
`RetrySyscom`, `MidSysSystemCmdIf::GetSyscomVersion`, `GetSyscomRomCorre` — the MCU handshake.

### Applications — `system/app`

`KWLauncher`, `MultiMediaPlayer`, `Navigation` (Garmin), `KwSystemService`, `KwAccountService`,
`KenwoodDriveClientService`, `KWAupeo`, `KWMixedMediaSearch`, `KWPhotoPicker`, `KWRss`,
`KWSchedule`, `KWSns`, `KWSyncAdapter`, `KWTtsView`, `KWWeather`, `MultimediaKeyboard`,
`MultimediaDemo`

Bloat candidates for Phase 3 (cloud/social, no audio/DSP role): `KWSns`, `KWRss`, `KWWeather`,
`KwAccountService`, `KenwoodDriveClientService`, `KWSyncAdapter`, `MultimediaDemo`.
**Do not touch**: `KwSystemService`, `KWLauncher`, `MultiMediaPlayer`, `Navigation`,
`MultimediaKeyboard`, and anything in `bin/` or `lib/` listed above.

---

## 5. Blockers and risks discovered (read before Phase 2)

1. **The recovery partition is empty.** `ndda6` (10 MB) is zero fill — no `ANDROID!`, no ramdisk,
   nothing. Android 4.0's Settings *Factory data reset* calls `RecoverySystem.rebootWipeUserData`,
   which writes a BCB and reboots into **recovery**. With no recovery image, that path cannot run.
   → **Do not use Settings → Factory data reset on this unit** until a recovery image is restored.
   Safe substitutes: (a) wipe `/data` contents from the root shell, or (b) first restore a working
   recovery built from `boot.img` + `recovery/recovery-from-boot.p`.
2. **`factory.fstab` is a legacy decoy.** It declares `yaffs2` for `/system`, `/data`, `/cache` and
   mtd devices; the real boot path (`init.tcc8800.fs.rc`, the `init.tcc8800.fs` trigger) mounts
   **ext4** from `ndda2/3/5/12/13` after `e2fsck -fy`. Trust `init.tcc8800.fs.rc`, never
   `factory.fstab`, when reasoning about mounts or formatting.
3. **`/data` mounts with `errors=panic,data=journal,commit=1`.** Any ext4 error while mounted
   panics the kernel by design — a corrupt `/data` does not degrade, it stops the unit.
4. **ndda11 holds a stale `/data` superblock copy** (hibernate snapshot). A naive "restore the
   snapshot" or a tool that trusts the first ext4 magic it finds will pick the wrong filesystem.
5. **Boot partition is only 10 MB.** A boot patch is a 10 MB container, not a 2 GB write; FWDN area
   addressing and the 640-byte FAI header apply.
6. **`ndda15` (784 MB) is zero fill and has never been imaged individually.** It is inside the
   whole-chip image taken today, so nothing is lost — but no tool has ever looked inside it.

---

## 6. Proposed Phase 2 (NOT executed — awaiting approval)

1. **Console first, software side is already done.** No cmdline change is needed: the pad hunt for
   **ttyTCC0** is the only remaining work. Board-level: identify the TCC8801 UART0 pins from the
   datasheet/board, then confirm by watching for `init: /dev/console` output.
2. **Verify the ramdisk patch set** currently on the unit (`ro.QB.enable 1→0`, USB `mass_storage,adb`)
   against `out/ramdisk/`, and re-derive `diag2.fai` reproducibly from `out/firmware/boot.img` so it
   is no longer an opaque artifact.
3. **Build a recovery image** from `boot.img` + `recovery-from-boot.p` before any factory reset is
   attempted, so the supported wipe path exists again.
4. **Bloat removal list** (section 4) as a `system` repack, applied only after (2) and (3) are proven.

### What a reviewer should double-check before anything is flashed

- Boot header: `page=2048`, kernel `0x40008000`, ramdisk `0x41000000`, tags `0x40000100`;
  when patching, change **only** the `ramdisk_size` field at byte offset 16 of the header page and
  leave every other header byte intact.
- Cmdline at header offset 64 (512 bytes, NUL padded). Stock is `console=null`; the unit runs
  `console=ttyTCC0,115200n8`. Do not "fix" the running unit — it is already correct.
- Ramdisk must be gzip + cpio **newc**; preserve the `TRAILER!!!` entry and 4-byte alignment.
- Any boot container for FWDN must keep `START*512 + SIZE*512 == 2,050,490,368` for whole-chip
  containers, or be a pure prefix (base 0) write for a boot-only patch.
