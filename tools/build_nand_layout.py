#!/usr/bin/env python3
"""Expand a .ami NAND map into an FWDN container.

Three things this does, all offline, no hardware:

    # 1. just show me the layout
    python build_nand_layout.py -m ../maps/TCC880X_NAND.ami --check

    # 2. a blank 2,050,490,368-byte disk with a valid MBR, ready for FWDN
    python build_nand_layout.py -m ../maps/TCC880X_NAND.ami -o nand_layout.fai

    # 3. the same disk with your own images dropped into their partitions
    python build_nand_layout.py -m ../maps/TCC880X_NAND.ami -o nand_layout.fai \
           --inject boot=boot.img --inject system=system.img

    # 4. or one partition on its own, small and quick
    python build_nand_layout.py -m ../maps/TCC880X_NAND.ami --partition sysinfo \
           --inject sysinfo=sysinfo.img -o sysinfo.fai

The output is a `FILESYSTEM_IMAGE` container (area "NAND Data"), which is the only
shape FWDN will actually write -- see tools/vendor/README.md and
docs/12-rebuilding-the-partition-map.md.

Write with FWDN only when you have read docs/09 and docs/10, the strap is fitted,
and the container's geometry matches the table your unit currently has. A
mismatched geometry makes the tool rewrite sector 0 on its own.
"""

import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_fai import build_header, DISKSIZE_DEFAULT  # noqa: E402
from build_mbr import build as build_mbr_area, PARTITIONS as MBR_ENTRIES  # noqa: E402

CHUNK = 1 << 20


MBR_RESERVE = 32   # sectors 0..31 hold the partition table and nothing else


class MapError(Exception):
    pass


def load_map(path):
    area, chip, mbr, parts = {}, {}, [], []
    section = None
    for lineno, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        if section in ("chip", "area"):
            if "=" not in line:
                raise MapError(f"{path}:{lineno}: expected key = value")
            k, v = (s.strip() for s in line.split("=", 1))
            (chip if section == "chip" else area)[k.lower()] = v
        elif section == "mbr":
            if line.startswith("entry|"):
                continue
            f = [s.strip() for s in line.split("|")]
            if len(f) != 4:
                raise MapError(f"{path}:{lineno}: mbr row needs 4 fields")
            mbr.append((int(f[0]), int(f[1], 0), int(f[2]), int(f[3])))
        elif section == "partition":
            if line.startswith("name|"):
                continue
            f = [s.strip() for s in line.split("|")]
            if len(f) < 4:
                raise MapError(f"{path}:{lineno}: partition row needs at least 4 fields")
            parts.append({
                "name": f[0], "start": int(f[1]), "sectors": int(f[2]),
                "fs": f[3], "note": f[4] if len(f) > 4 else "",
            })
        else:
            raise MapError(f"{path}:{lineno}: row outside a section")
    for key, sect in (("area", area), ("chip", chip)):
        if not sect:
            raise MapError(f"{path}: no [{key}] section")
    if len(parts) != 15:
        print(f"warning: map lists {len(parts)} partitions, the reference unit has 15")
    return chip, area, mbr, parts


def check(area, mbr, parts):
    """Everything here is an identity that must hold before a write is safe."""
    sector = int(area.get("sector", 512))
    disksize = int(area["disksize"], 0)
    total = disksize // sector
    problems = []

    # Sectors 0..31 are the MBR area itself, so the first partition starts at 32 and
    # the coverage identity FWDN validates is  first_start + sum(sectors) == total.
    expect = MBR_RESERVE
    for p in parts:
        if p["start"] != expect:
            problems.append(f"{p['name']}: starts at {p['start']:,}, previous partition ends at {expect:,}"
                            f"  (gap or overlap of {abs(p['start']-expect):,} sectors)")
        expect = p["start"] + p["sectors"]
    if expect != total:
        problems.append(f"partitions end at sector {expect:,}, area holds {total:,}"
                        f"  ({expect-total:+,} sectors difference)")

    if mbr:
        if mbr[-1][2] + mbr[-1][3] != total:
            problems.append(f"MBR extended entry ends at {mbr[-1][2]+mbr[-1][3]:,}, area holds {total:,}")
        for i, (_e, _t, st, ln) in enumerate(mbr[:-1]):
            if st + ln > total:
                problems.append(f"MBR entry {i} runs past the end of the area")

    print(f"  {'ok  ' if not problems else 'FAIL'}  area {area.get('name')!r}, {total:,} sectors,"
          f" {disksize:,} bytes")
    print(f"  {'ok  ' if not problems else 'FAIL'}  {len(parts)} partitions tile the area with no gaps"
          if not problems else f"  FAIL  {len(problems)} problem(s):")
    for p in problems:
        print(f"          - {p}")
    return not problems


def main():
    ap = argparse.ArgumentParser(description="Expand a .ami NAND map into an FWDN container.")
    ap.add_argument("-m", "--map", required=True, help="the .ami map file")
    ap.add_argument("-o", "--out", help="output container (.fai)")
    ap.add_argument("--check", action="store_true", help="validate the map and print it, write nothing")
    ap.add_argument("--partition", help="emit one partition instead of the whole area")
    ap.add_argument("--inject", action="append", default=[], metavar="NAME=FILE",
                    help="place FILE at partition NAME instead of fill (repeatable)")
    ap.add_argument("--fill", default="ff", choices=["ff", "00"], help="background byte (default ff)")
    args = ap.parse_args()

    try:
        chip, area, mbr, parts = load_map(args.map)
    except (MapError, KeyError) as e:
        print(f"error: {e}")
        return 2

    sector = int(area.get("sector", 512))
    disksize = int(area["disksize"], 0)
    by_name = {p["name"]: p for p in parts}

    print(f"[{args.map}]  {chip.get('device', '?')}  {chip.get('type', '')}")
    print(f"  area      {area.get('name')!r}  {disksize:,} B  ({disksize//sector:,} sectors)")
    print(f"  {'name':12s} {'start':>10s} {'sectors':>10s}  {'size':>10s}  filesystem")
    for p in parts:
        print(f"  {p['name']:12s} {p['start']:>10,} {p['sectors']:>10,}"
              f"  {p['sectors']*sector/1048576:9.1f}M  {p['fs']}")

    ok = check(area, mbr, parts)
    if args.check or not ok:
        return 0 if ok else 1
    if not args.out:
        print("error: --out is required unless you pass --check")
        return 2

    inject = {}
    for spec in args.inject:
        if "=" not in spec:
            print(f"error: --inject wants NAME=FILE, got {spec!r}")
            return 2
        name, path = spec.split("=", 1)
        if name not in by_name:
            print(f"error: no partition named {name!r} in the map")
            return 2
        p = by_name[name]
        size = os.path.getsize(path)
        if size > p["sectors"] * sector:
            print(f"error: {path} is {size:,} B, larger than {name} ({p['sectors']*sector:,} B)")
            return 2
        inject[name] = open(path, "rb")

    if args.partition:
        if args.partition not in by_name:
            print(f"error: no partition named {args.partition!r}")
            return 2
        print("\n  WARNING: a container that declares ONE partition makes the tool rewrite sector 0"
              "\n           with its own synthesised table. That is the write that breaks the boot"
              "\n           path (18D1:D00D fastboot, no logo, no kernel). Either write the whole"
              "\n           layout, or finish the session with the 32-sector MBR repair from docs/12.")
        p = by_name[args.partition]
        payload_len = p["sectors"] * sector
        start = p["start"]
        regions = [(0, p["name"])]
    else:
        payload_len = disksize
        start = 0
        regions = [(0, "__mbr__")] + [(p["start"] * sector, p["name"]) for p in parts]

    hdr = build_header(payload_len, start, payload_len // sector,
                       area.get("name", "NAND Data"), int(area.get("disksize", DISKSIZE_DEFAULT), 0))
    mbr_bytes = build_mbr_area(32)[:sector] if mbr else b""

    fill = b"\xff" if args.fill == "ff" else b"\x00"
    written = 0
    with open(args.out, "wb") as out:
        out.write(hdr)
        for off, tag in regions:
            if off > written:
                n = off - written
                while n > 0:
                    k = min(CHUNK, n)
                    out.write(fill * k)
                    n -= k
                written = off
            if tag == "__mbr__":
                out.write(mbr_bytes)
                written += len(mbr_bytes)
            elif tag in inject:
                src = inject[tag]
                while True:
                    blk = src.read(CHUNK)
                    if not blk:
                        break
                    out.write(blk)
                    written += len(blk)
            # unfilled partitions are covered by the next gap or the tail
        if written < payload_len:
            n = payload_len - written
            while n > 0:
                k = min(CHUNK, n)
                out.write(fill * k)
                n -= k

    size = os.path.getsize(args.out)
    print(f"\n  wrote     {args.out}  ({size:,} bytes)")
    print(f"  payload   {payload_len:,} B at sector {start:,}  ->  sectors {start:,}..{start+payload_len//sector-1:,}")
    print(f"  contains  Target column must read 'NAND Data', dropdown on 'Default download'")
    print(f"  md5       ", end="")
    with open(args.out, "rb") as fh:
        h = hashlib.md5()
        for blk in iter(lambda: fh.read(CHUNK), b""):
            h.update(blk)
    print(f"            {h.hexdigest()}")
    for p in parts:
        if p["name"] in inject:
            inject[p["name"]].close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
