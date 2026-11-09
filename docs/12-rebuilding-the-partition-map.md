# 12 — Rebuilding the partition map (the `.fai` that saves a dead unit)

If the first sectors of NAND are damaged, the bootloader cannot find its partitions: the unit powers
up, never draws the vendor logo, and never reaches a kernel. adb is gone, FWDN's area map is empty, and
the only thing that brings it back is writing **32 sectors at sector 0** — the map itself.

We do not publish that file. Not because it is secret, but because it does not need to be published:
it is 446 zero bytes, four 16-byte partition entries and a `0xFF` fill, and this repo can **rebuild it
byte for byte** from the numbers in [docs/06](06-partitions-and-boot-image.md). Two small scripts:

```bash
python tools/build_mbr.py  -o mbr_header.bin      # the 16 KiB header area
python tools/build_fai.py  -p mbr_header.bin --start-sector 0 \
                           --sectors 4004864 -o mbr_restore.fai
```

On the reference unit those two commands reproduce the bench container **byte for byte** — same
17,024-byte file, md5 `34dbb8107520b7c401ff994817e8208e`, same 16,384-byte payload, md5
`48e98b3aa768e7dfd3672510604a224c` — which is why this page can promise the result without shipping
Kenwood's bytes.

## What is actually in those 32 sectors

```
sector 0        446 zero bytes
                4 x 16-byte MBR entries at 0x1BE
                0x55 0xAA at 0x1FE
sectors 1..31   0xFF fill
```

The four entries, as the bootloader writes them:

| # | label | type | start sector | sectors | what it is |
|---|---|---|---|---|---|
| 0 | boot | `0x00` | 32 | 20,480 | `ndda1` — **type `0x00` on purpose** |
| 1 | system | `0x83` | 20,512 | 962,560 | `ndda2`, the ext4 `/system` |
| 2 | data | `0x83` | 983,072 | 716,800 | `ndda3`, the ext4 `/data` |
| 3 | extended | `0x0F` | 1,699,872 | 2,304,992 | everything after `/data` |

Two things in that table look wrong and are not:

- **Entry 0 is type `0x00`** — "unused" to any normal partition editor. If you open this table in
  `fdisk`, `parted` or a Windows partition tool and let it "repair" the type byte, LK stops finding
  the boot partition again. Do not let a partition editor touch this table.
- **Entry 3 is a DOS extended partition with no EBR chain.** `ndda5`, `ndda6`, `ndda11`, `ndda12`,
  `ndda13` and the rest are *not* in the MBR at all; they come from the bootloader's own table, which
  is why `/sys/class/block/nddaN/start` and `/sys/class/block/nddaN/size` are the authority and the
  MBR is not. The extended entry exists so that the whole disk is covered by *something*.

The CHS fields in the entries are the standard 255-head/63-sector conversion of the LBA, not real
geometry — `build_mbr.py` computes them so the bytes match, and nothing on the unit reads them.

## Writing it

This is an **area write**, so it goes through FWDN's file list, not the hidden dump dialog:

1. `Add File` → `mbr_restore.fai`, and confirm the **Target** column reads `NAND Data`.
2. The strap is fitted and the tool already sees the device ([docs/09](09-fwdn-mode.md)).
3. Press **Start**. It takes under a second.
4. Expect `Download is complete!` and nothing else. If the tool answers
   `Part Size Value is wrong!`, the container's two size fields disagree — rebuild it with
   `build_fai.py` rather than editing the file by hand.

Absolute rules, same as everywhere else on the write path: never `Erase`, never `Low format whole
memory before download`, and **never** confirm *"NAND partition changes is detected. It will erase
whole NAND."*

## Does it fix a unit on its own?

Sometimes, and it is worth knowing which sometimes:

| state | what 32 sectors at 0 buys you |
|---|---|
| MBR overwritten by a bad area write, everything else intact | **full recovery** — LK finds its partitions and boots normally |
| MBR intact, `/system` or `/data` broken | nothing — that is [docs/03](03-nand-backup-and-restore.md) and [docs/07](07-data-persistence-and-bootloop.md) |
| blank chip (all `FF`) | nothing — the MBR is the *first* of several things missing, see [docs/03](03-nand-backup-and-restore.md) |

The failure mode this page exists for is the first row, and it is a self-inflicted one: **an FWDN area
write can corrupt the MBR.** We hit it, which is why this file existed on the bench at all.

## Verify what landed

Read it back before you believe it — 32 sectors from address `00000000` in `Ctrl+Shift+D`
([docs/10](10-nand-backup-with-fwdn.md)) — then compare the readback against the image you built:

```
> python tools/build_mbr.py -o mbr_header.bin --verify readback.bin
```

`--verify` compares against the first 16 KiB of whatever dump you point it at, and exits non-zero with
the offset of the first difference. You can also hash the built file directly:

```
> certutil -hashfile mbr_header.bin MD5
48e98b3aa768e7dfd3672510604a224c      <- reference unit
```

That number is a reference, not a target: if your unit's `ndda1`/`ndda2`/`ndda3` geometry differs, the
hash differs and `--verify` says so loudly. That is the check working, not a failure.
