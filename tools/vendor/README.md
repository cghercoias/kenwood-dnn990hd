# vendor — Telechips tools, included as-is

These are **Telechips' own Windows tools**, not ours. They are here because without them this
documentation cannot be reproduced: the downloader is the only way into boot-ROM mode, and the driver
is the only way Windows will talk to it. They are redistributed for preservation, unmodified, with the
checksums below. If a rights holder objects, open an issue and they come down.

| file | size | SHA-256 |
|---|---|---|
| `Telechips_FWDN_V7_Tool_v2.30.zip` | 313,852 B | `b77929f24407235a0abebb23f0e2b1e0a62630f79c21f3ca2955003426f204ac` |
| `Telechips_VTC_Driver_v5.0.0.7.zip` | 1,438,002 B | `0311ff9c7b97a7d763b0b7f81353d621e117ca0cd1823ef7dc812a0a5778c4fb` |

`SHA256SUMS` is a copy of the same values for `sha256sum -c`.

- **FWDN zip** contains `FWDN_V7_v2.30.exe` (724,992 B, dated 2013-01-16) and a `Driver/Download.url`.
- **Driver zip is password protected: `DRIVER123`** (also in `Password.txt` inside). It contains
  32/64-bit self-extractors for VTC Driver v5.0.0.7.
- The loader the tool needs (`bootloader.img`, 136,928 B) is **not** here — it is Kenwood's, and it
  comes out of the vendor update package you already own. See `docs/09`.

Neither tool is signed by anyone you have heard of; both will make your antivirus unhappy. Check the
hashes above before you run them.

## Driver — the short version

```
unzip Telechips_VTC_Driver_v5.0.0.7.zip          (password DRIVER123)
run     x64\VTC Driver Installer v5.0.0.7 for x64.exe
```

Or, if the 2013 catalog trips Windows' publisher check, extract the INF and install it directly from an
elevated prompt:

```
7z x "VTC Driver Installer v5.0.0.7 for x64.exe" -oC:\vtcdrv
pnputil /add-driver C:\vtcdrv\vtcdrv.inf /install
```

The INF maps `USB\VID_140E&PID_B068` to `"Telechips TCC880x VTC USB Driver"`. Extract to a local folder —
Device Manager's *Browse* against a network share will not parse a third-party INF.

## What the downloader can and cannot do

Full procedure in `docs/09` and `docs/10`. The short list of what was measured on a DNN990HD:

| operation | where | status |
|---|---|---|
| read sectors | `Ctrl+Shift+D` → Storage Dump → `Dump` | **works**, byte-exact |
| write sectors | `Ctrl+Shift+D` → `Dump Write` | **dead** — issues `TOTALDUMP_BlockWriteCmd` and waits forever; wedges the loader, needs a power cycle |
| write an area image | `Add File` → `Start` | works (container format below) |
| `Erase`, `Download`, `Low format whole memory` | download tab | never — destroys the partition map |
| `Area Read` (`Ctrl+Shift+R`) | hidden | reads TCC containers only, not raw sectors |
| batch mode | CLI | builds containers host-side, no radio needed |

Menu reality: `System | View | Project | Tools`, no `File` menu, `Tools` holds only `Options…`, and the
`NAND Setting` item in the resources belongs to an unattached `LGE` menu.

## The `.fai` / `.dum` container format

`Add File` validates by **content**, not extension: a header-less `.bin` gives `Error! - Not supported
file`. Only Telechips containers get in. Layout, confirmed against the tool's own output:

```
0x000  "[HEADER]"                 8 B magic
0x008  u32  header size           = 0x30 (RAW_IMAGE) or 0x60 (FILESYSTEM_IMAGE)
0x00C  u32  CRC                   enforced at write time, see below
0x010  char[16] type              "FILESYSTEM_IMAGE" | "RAW_IMAGE" | "KERNEL_IMAGE" | "KEYBOX_IMAGE"
0x020  char[16] format            "TCC FAT IMG V0.1"
0x030  char[16] area              "NAND Data"
0x040  "DISKSIZE"                 8 B literal, then u64 at 0x048 = area size in bytes
0x050  "PART_CNT"                 8 B literal, then u32 at 0x058
0x068  u32  sector size           = 0x200; a zero here breaks the size arithmetic
0x232  partition entry #0         12 B stride: u32 type, u32 start_sector, u32 size_sectors
0x260  16 B stub                  ends 55 AA at 0x26E (a signature tail, not an MBR)
0x270  u64  base address          in bytes
0x278  u64  payload length        in bytes, header excluded
0x280  payload
```

Rules that decide whether a hand-built container is accepted:

- **The declared table must tile the area exactly**:
  `base + Σ(size_sectors × 512) == DISKSIZE`. This is checked before the payload is looked at, so a
  failure here reads as `Part Size Value is wrong` and tells you nothing about your data.
- **The geometry is stored twice and both copies are validated.** `0x236`/`0x23A` hold start/length in
  sectors, `0x270`/`0x278` the same in bytes — and **both byte fields are u64**. Patch them together,
  or the error value will be two 32-bit halves welded together (e.g. `0x20CD0120083F0F3`).
- **`RAW_IMAGE` resolves to no Target**, so the tool accepts it and can never write it. A writable
  container is `FILESYSTEM_IMAGE` + `TCC FAT IMG V0.1` + area `NAND Data`.
- **The CRC at `0x00C` is checked at write time, not at add time** — and it matches no standard CRC-32
  variant. Use the tool as the oracle: add the file with a dummy value, copy the `Target CRC` it prints
  into `0x00C`, re-add. Adding a file writes nothing, so this costs one round trip and no risk.
  Sometimes a zero CRC is accepted outright — try one `Start` first and read the log.
- **The writer honours the container's declared geometry, and that is the dangerous part.** A container
  whose table equals the live table writes only its payload. A container declaring something *else*
  makes the tool rewrite **sector 0** with its own single synthesised entry — which destroys the
  bootloader's named-partition lookup and leaves the unit in LK fastboot (`18D1:D00D`, no logo, dark
  panel). Two cures: make the declared table equal the live one, or make the last write of a session a
  base-`0` container whose payload starts with the real named MBR.

Timing, measured on USB full-speed: the first area write of a session is dominated by erase (512 KB took
53 s), later bulk writes run at ~1–3 MB/s (9.8 MB in 9.5 s; a 2,050,490,368 B whole-disk payload in
12 min 49 s). Never estimate a job from the first write, and never interrupt one.

## Batch mode

The command line is undocumented in the GUI but the usage text is a string in the binary:

```
fwdn_v7.exe -img  -area <Area Name> -file <Source File> [-sa <Sector Address>] -o <Target Image>
fwdn_v7.exe -imgfs -area <Area Name> [-vol <Volume Name>] -size <Disk Size in sectors> [-dir <Folder>] -o <Target Image>
other options: -suppress, -cluster, -nocrc
```

It runs entirely host-side — no radio, no driver, no window — which makes it the way to build a
container while the unit is somewhere else. `-sa` is in sectors and is stored as bytes (`-sa 32` →
`0x4000`). Two catches: its output is a `RAW_IMAGE` (no Target, so it is a layout reference and not a
writable container), and its checksum is not the one the device demands. **Any argument makes the tool
batch-only** — `-nocrc` alone exits silently without opening the GUI.

## Also on this bench, not included

`Telechips_FWDN_V7_Tool_v2.13.zip` (271,370 B) — an older build; everything in this repo was done with
v2.30.
