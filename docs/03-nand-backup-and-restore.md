# 03 — NAND backup, verification and restore

## Why

On this unit the NAND is the only copy of a build that cannot be re-downloaded: firmware 1.8.0 is the
last release Kenwood made, and the engineering build on the chip (`eng.root.20181003.133037`) is not
the same thing as the consumer package. Before the first write to `/system`, take the whole thing.

## Taking the backup

From a root shell, with a FAT32 USB stick in the front port (mounted at `/mnt/usb` or `/sdcard/usb`):

```sh
dd if=/dev/block/ndda of=/mnt/usb/nand.img bs=1M
# 2,050,490,368 bytes later, verify on the device:
md5sum /mnt/usb/nand.img
```

Two smaller, independent artefacts are worth taking at the same time:

```sh
dd if=/dev/block/mtdblock0 of=/mnt/usb/mtdblock0.img bs=1M      # 83,886,080 B
tar czf /mnt/usb/data.tar.gz /data                              # the user data tree
```

`/data` as a tar is far more useful than as a raw image: it survives a reformat of `ndda3`, and you
can read the databases in it on a PC.

## The three copies that were kept

| Artefact | Size | MD5 |
|---|---|---|
| `nand_20261108.img` | 2,050,490,368 B | `38e463ef28e95c2b02cccf4397936084` |
| `mtdblock0_20261108.img` | 83,886,080 B | `bbcd23d1ea66baf25f795f98773a9605` |
| `data_20261108.tar.gz` | 32,563,496 B | `28ff4b52e6ae3052be7270774a06abfc` |

Held on a USB stick, on the bench PC (`C:\fwdn\backup\`), and on the NAS. The working copy inside
`C:\dnn990hd_work\raw\` is an NTFS **hardlink** to the bench-PC copy, so the 2 GB is not stored twice
(link count 2, md5 unchanged) and the read-only analysis tree cannot damage the archive.

> An earlier, pre-wipe image (`nand_full.bin`, 2,050,490,368 B, Oct 26) is kept as the reference for
> the *original* state. It is **not** the right thing to restore if you want the unit working today —
> see the MBR warning below.

## Verifying an image on a PC

```bash
md5sum nand.img
python - <<'PY'
import struct
f=open("nand.img","rb")
# walk the 15 partitions the kernel knows about; each must start with a plausible signature
for name,start,size in [(…)]:   # see docs/06
    f.seek(start*512); print(name, f.read(8))
PY
```

## Never restore the whole image

The MBR inside `ndda` describes **three** of the fifteen partitions, and one of them (the generic
`0x06` FAT entry) is what breaks LK's boot path on this board. Flashing the whole 2 GB back restores
that MBR and the unit stops booting. This was learned the hard way; the working MBR in the current
image is a rebuild, not the original.

Restore **per partition**, from a shell that is already running:

```sh
# example: /system from the image, offset 20512 sectors
dd if=/mnt/usb/nand.img of=/dev/block/ndda2 bs=512 skip=20512 count=962560
```

Better still, restore the smallest thing that fixes the problem: a single file, or `/data` from the
tar:

```sh
mount -o remount,rw /dev/block/ndda3 /data
cd / && tar xzf /mnt/usb/data.tar.gz
```

## Verifying what you wrote

`md5sum /dev/block/ndda` **never matches** the image while any of the partitions on it are mounted —
the kernel is writing. This is not corruption and it is not a bad NAND. To sanity-check reads, hash a
partition you are not using (`ndda1`, the boot partition, is read-only in practice; its static hash is
`b8b6ef8c…`).

## Reading the result on a PC

The image is a flat 2 GiB blob with an offset-shifted partition layout — every partition starts at the
absolute byte `start * 512`. Any hex or carving tool works if you apply those offsets. Both figures in
`images/` carry the offsets so you don't have to recompute them.
