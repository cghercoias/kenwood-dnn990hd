#!/usr/bin/env python3
"""Inspect a Kenwood DNN990HD whole-NAND image without mounting anything.

  python nand_inspect.py nand.img            # partition table + verification
  python nand_inspect.py nand.img --boot     # also decode the Android boot header
  python nand_inspect.py nand.img --extract 3 out.img   # carve ndda3 to out.img

Read-only. Nothing is ever written back to the source image.
"""
import sys, struct, os

# name, start sector, size in sectors, role  (kernel static table, verified against a real image)
PARTS = [
    ("ndda1",       32,   20480, "boot (ANDROID!)"),
    ("ndda2",    20512,  962560, "/system ext4"),
    ("ndda3",   983072,  716800, "/data ext4"),
    ("ndda4",  1699872,      32, "MBR artefact"),
    ("ndda5",  1699904,  307232, "/cache ext4"),
    ("ndda6",  2007136,   20512, "recovery - zero fill"),
    ("ndda7",  2027648,   10272, "zero"),
    ("ndda8",  2037920,   10272, "zero"),
    ("ndda9",  2048192,    2080, "zero"),
    ("ndda10", 2050272,    2080, "zero"),
    ("ndda11", 2052352,  307232, "hibernate snapshot"),
    ("ndda12", 2359584,   20512, "/.sysinfo ext4"),
    ("ndda13", 2380096,   16416, ".garmin ext4"),
    ("ndda14", 2396512,    2080, "zero"),
    ("ndda15", 2398592, 1606272, "zero fill"),
]
SECTOR = 512
EXT4_MAGIC = 0xEF53

def table(total_bytes):
    end = PARTS[-1][1] + PARTS[-1][2]
    print(f"{'name':<8}{'start':>10}{'sectors':>11}{'MiB':>9}  role")
    for n, s, k, r in PARTS:
        print(f"{n:<8}{s:>10,}{k:>11,}{k*SECTOR/2**20:>9.1f}  {r}")
    print(f"\nlast end {end:,} sectors x {SECTOR} = {end*SECTOR:,} bytes")
    if total_bytes:
        ok = end * SECTOR == total_bytes
        print(f"image size        {total_bytes:,} bytes   -> {'OK' if ok else 'MISMATCH'}")
        return ok
    return True

def ext4_at(f, name, start):
    off = start * SECTOR + 1024 + 56          # superblock magic lives at +0x38
    f.seek(off); m = f.read(2)
    if len(m) == 2 and struct.unpack("<H", m)[0] == EXT4_MAGIC:
        f.seek(start * SECTOR + 1024 + 4); blocks = struct.unpack("<I", f.read(4))[0]
        return f"ext4, {blocks} blocks"
    return "no ext4 superblock"

def boot(f):
    off = PARTS[0][1] * SECTOR
    f.seek(off); h = f.read(1632)
    if h[:8] != b"ANDROID!":
        print(f"boot header at {off:,}: magic {h[:8]!r} - not an Android boot image"); return
    (magic, ksz, kaddr, rsz, raddr, ssz, saddr, tags, page) = struct.unpack("<8s8I", h[:40])
    cmd = h[64:64+512].split(b"\x00")[0].decode(errors="replace")
    print(f"\nboot header at {off:,}")
    print(f"  page_size    {page}")
    print(f"  kernel       {ksz:,} bytes @ 0x{kaddr:08x}")
    print(f"  ramdisk      {rsz:,} bytes @ 0x{raddr:08x}")
    print(f"  second       {ssz:,} bytes @ 0x{saddr:08x}")
    print(f"  tags_addr    0x{tags:08x}")
    print(f"  cmdline      {cmd}")

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    path = sys.argv[1]
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        table(size)
        print()
        for n, s, k, r in PARTS:
            if "ext4" in r:
                print(f"  {n:<7} {ext4_at(f, n, s)}")
        if "--boot" in sys.argv:
            boot(f)
        if "--extract" in sys.argv:
            i = sys.argv.index("--extract")
            n, out = int(sys.argv[i+1]), sys.argv[i+2]
            name, s, k, r = PARTS[n-1]
            with open(out, "wb") as o:
                f.seek(s*SECTOR); left = k*SECTOR
                while left:
                    b = f.read(min(left, 1 << 20))
                    if not b: break
                    o.write(b); left -= len(b)
            print(f"\ncarved {name} -> {out} ({os.path.getsize(out):,} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
