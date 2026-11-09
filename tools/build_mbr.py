#!/usr/bin/env python3
"""Rebuild the DNN990HD NAND header area (MBR + fill) from scratch.

The unit's first 32 KiB hold nothing but a four-entry MBR in sector 0 and
0xFF fill after it. That is the whole "partition map" a dead unit needs, and
it can be regenerated from the numbers in docs/06 instead of copied out of a
vendor image:

    sector 0       446 zero bytes
                   4 partition entries x 16 bytes at 0x1BE
                   0x55 0xAA at 0x1FE
    sectors 1..31  0xFF fill

Verified: on the reference unit this output is byte-identical to
dump[0:16384] of the chip read (md5 48e98b3aa768e7dfd3672510604a224c).
If your build does not match, stop and compare against your own dump before
you write anything to NAND -- a different geometry means a different unit.

Usage:
    python build_mbr.py -o mbr_header.bin
    python build_mbr.py -o mbr_header.bin --verify C:\\fwdn\\backup\\nand_20261108.img
"""

import argparse
import hashlib
import struct
import sys

SECTOR = 512

# (label, start sector, sector count, MBR type byte)
# This is the DNN990HD map as the bootloader writes it: three usable primaries
# and one DOS extended entry covering everything after /data. The 15 ndda*
# partitions are NOT in here -- they come from the bootloader's own table.
PARTITIONS = [
    ("boot",      32,       20480,   0x00),   # type 0x00: present but "unused" to any OS
    ("system",    20512,    962560,  0x83),
    ("data",      983072,   716800,  0x83),
    ("extended",  1699872,  2304992, 0x0F),
]

HEADS, SECTORS_PER_TRACK = 255, 63


def chs(lba):
    """LBA to the packed CHS triple an MBR entry stores (255 heads, 63 spt)."""
    c = lba // (HEADS * SECTORS_PER_TRACK)
    rem = lba % (HEADS * SECTORS_PER_TRACK)
    h = rem // SECTORS_PER_TRACK
    s = rem % SECTORS_PER_TRACK + 1
    return bytes((h & 0xFF, (s & 0x3F) | ((c >> 2) & 0xC0), c & 0xFF))


def entry(boot, lba, count, ptype):
    c0 = chs(lba)
    c1 = chs(lba + count - 1)
    return (bytes([boot]) + c0 + bytes([ptype]) + c1
            + struct.pack("<II", lba, count))


def build(sectors=32):
    img = bytearray(b"\xff" * (sectors * SECTOR))
    mbr = bytearray(SECTOR)
    for i, (_name, start, count, ptype) in enumerate(PARTITIONS[:4]):
        mbr[0x1BE + i * 16:0x1BE + (i + 1) * 16] = entry(0x00, start, count, ptype)
    mbr[0x1FE:0x200] = b"\x55\xaa"
    img[0:SECTOR] = mbr
    return bytes(img)


def describe(image):
    print(f"  bytes        {len(image):,}  ({len(image)//SECTOR} sectors)")
    print(f"  md5          {hashlib.md5(image).hexdigest()}")
    for i, (label, start, count, ptype) in enumerate(PARTITIONS[:4]):
        print(f"  entry {i}  {label:9s} type 0x{ptype:02x}  sector {start:>9,} .. {start+count-1:>9,}"
              f"  {count*SECTOR/1048576:8.1f} MiB")


def main():
    ap = argparse.ArgumentParser(description="Rebuild the DNN990HD MBR header area.")
    ap.add_argument("-o", "--out", required=True, help="output image (16,384 bytes)")
    ap.add_argument("--sectors", type=int, default=32, help="size in 512-byte sectors (default 32)")
    ap.add_argument("--verify", metavar="DUMP", help="compare against the first sectors of a chip dump")
    a = ap.parse_args()

    image = build(a.sectors)
    describe(image)

    if a.verify:
        with open(a.verify, "rb") as fh:
            ref = fh.read(len(image))
        if ref != image:
            diff = [i for i in range(len(image)) if ref[i] != image[i]]
            print(f"\nVERIFY FAILED against {a.verify}: {len(diff)} bytes differ, first at 0x{diff[0]:x}")
            print("Do not write this image. Your unit's geometry is not the one this script assumes.")
            return 1
        print(f"\nverify OK: byte-identical to the first {len(image)} bytes of {a.verify}")

    with open(a.out, "wb") as fh:
        fh.write(image)
    print(f"\nwrote {a.out}  ({len(image):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
