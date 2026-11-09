#!/usr/bin/env python3
"""Wrap a raw payload in the Telechips FWDN ".fai" container.

This is the container the FWDN V7 tool's file list accepts for an area write
(Target column: "NAND Data"). It is a 640-byte header followed by the payload,
nothing else -- no compression, no checksum unless you ask the tool for one.

Header layout as measured against containers this tool actually accepted
(all offsets hex, all integers little-endian):

    0x000  "[HEADER]"                8 bytes
    0x008  u32   header length       0x60 = 96
    0x010  "FILESYSTEM_IMAGE"        16 bytes   (or "RAW_IMAGE" -- see docs/10)
    0x020  "TCC FAT IMG V0.1"        16 bytes   container format tag
    0x030  area name                 32 bytes   e.g. "NAND Data"
    0x040  "DISKSIZE"                 8 bytes
    0x048  u32   disk size in bytes             (whole NAND area, 0x7A380000 here)
    0x050  "PART_CNT"                 8 bytes
    0x058  u32   number of area entries         (always 1 in our containers)
    0x068  u32   sector size                    512
    0x232  u8    entry type                     0x83
    0x236  u32   start sector
    0x23A  u32   sector count
    0x26E  "U\xaa"                   2 bytes    entry trailer
    0x270  u64   payload byte offset             0 (payload starts right after header)
    0x278  u64   payload byte length
    0x280  start of payload

Both the "block" pair (0x236/0x23A) and the "byte" pair (0x270/0x278) have to
agree with the payload, or the tool rejects the file with
"Part Size Value is wrong!". The tool also validates the payload *content*, not
the extension: a raw file whose first bytes are not a recognised header gives
"<file>'s type is unknown.".

Usage:
    python build_fai.py -p mbr_header.bin --start-sector 0 -o mbr_restore.fai
    python build_fai.py -p boot.img --start-sector 32 --name "NAND Data" -o boot_fix.fai
"""

import argparse
import hashlib
import os
import struct
import sys

HEADER_LEN = 0x280          # the payload starts here; the declared header is 96 bytes
SECTOR = 512
DISKSIZE_DEFAULT = 0x7A380000  # 2,050,490,368 B -- this model's whole "NAND Data" area


def build_header(payload_len, start_sector, sector_count, name, disksize):
    h = bytearray(HEADER_LEN)
    h[0x000:0x008] = b"[HEADER]"
    struct.pack_into("<I", h, 0x008, 0x60)
    h[0x010:0x020] = b"FILESYSTEM_IMAGE"
    h[0x020:0x030] = b"TCC FAT IMG V0.1"
    nb = name.encode("ascii")[:31]
    h[0x030:0x030 + len(nb)] = nb
    h[0x040:0x048] = b"DISKSIZE"
    struct.pack_into("<I", h, 0x048, disksize)
    h[0x050:0x058] = b"PART_CNT"
    struct.pack_into("<I", h, 0x058, 1)
    struct.pack_into("<I", h, 0x068, SECTOR)
    h[0x232] = 0x83
    struct.pack_into("<I", h, 0x236, start_sector)
    struct.pack_into("<I", h, 0x23A, sector_count)
    h[0x26E:0x270] = b"\x55\xaa"
    struct.pack_into("<Q", h, 0x270, 0)
    struct.pack_into("<Q", h, 0x278, payload_len)
    return bytes(h)


def main():
    ap = argparse.ArgumentParser(description="Build a Telechips FWDN .fai container.")
    ap.add_argument("-p", "--payload", required=True, help="raw payload file (512-byte sectors)")
    ap.add_argument("--start-sector", type=int, required=True, help="first sector the payload lands on")
    ap.add_argument("--sectors", type=int, help="sector count to declare (default: payload size / 512)")
    ap.add_argument("--name", default="NAND Data", help='area name, default "NAND Data"')
    ap.add_argument("--disksize", default=f"0x{DISKSIZE_DEFAULT:x}", help="whole-area size in bytes")
    ap.add_argument("-o", "--out", required=True, help="output .fai file")
    a = ap.parse_args()

    payload = open(a.payload, "rb").read()
    n = len(payload)
    if n % SECTOR:
        print(f"warning: payload is not a multiple of {SECTOR} ({n} bytes); the tool may refuse it")
    if n == 0:
        print("error: empty payload")
        return 1

    sectors = a.sectors if a.sectors is not None else (n + SECTOR - 1) // SECTOR
    if sectors * SECTOR < n:
        print(f"error: --sectors {sectors} is too small for {n} bytes")
        return 1

    disksize = int(a.disksize, 0)
    hdr = build_header(n, a.start_sector, sectors, a.name, disksize)

    with open(a.out, "wb") as fh:
        fh.write(hdr)
        fh.write(payload)

    last = a.start_sector + sectors - 1
    print(f"  payload      {n:,} bytes  md5 {hashlib.md5(payload).hexdigest()}")
    print(f"  area         {a.name!r}")
    print(f"  covers       sector {a.start_sector:,} .. {last:,}"
          f"   (bytes {a.start_sector*SECTOR:,} .. {(last+1)*SECTOR-1:,})")
    print(f"  disksize     0x{disksize:x}")
    print(f"  wrote        {a.out}  ({os.path.getsize(a.out):,} bytes)")
    print("\nPress no other button: select the file, confirm Target reads 'NAND Data', then Start.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
