# tools

Everything here is ours. Nothing needs installing beyond Python 3 and Pillow (only for the figures).

## Windows helpers (double-click)

These wrap `C:\fwdn\platform-tools\adb.exe`. They expect the unit's CN902 port to be connected. Edit
the `ADB=` line at the top of each file if your copy lives somewhere else.

| File | What it does | Writes |
|---|---|---|
| `data_health.bat` | `/data` health and persistence probe: identity, mounts, `df`, `/proc/partitions`, NAND slice of `dmesg`, and a marker file that must survive a reboot | `C:\fwdn\probe\data_health.txt` |
| `logs.bat` | full `logcat -b all` + `dmesg` | `C:\fwdn\probe\` |
| `shell.bat` | interactive root shell | — |
| `after_reset.bat` | after a data reset: re-disable the stock launcher, re-enable `com.jvckenwood.kwlauncher` and `jp.co.kenwood.multimediaplayer`, reboot | unit only |

`data_health.bat` is meant to be run **twice with a reboot in between** — see
[docs/07](../docs/07-data-persistence-and-bootloop.md). The file that decides the diagnosis is
`MARKER_PRESENT` vs `MARKER_ABSENT` in the second log.

## Python

### `nand_inspect.py` — read-only whole-image inspector

```bash
python nand_inspect.py nand.img                  # partition table, size reconciliation, ext4 check
python nand_inspect.py nand.img --boot           # + decode the Android boot header in ndda1
python nand_inspect.py nand.img --extract 3 data.img   # carve /data (ndda3) to a separate file
```

It never writes to the image. The partition table it carries is the one recovered from the device and
reconciled to the image size, so a `MISMATCH` on your own dump means your dump is short, not that the
table is wrong.

### Figures and photos are committed as-is

`../images/` holds the finished diagrams and photo crops. Nothing in this repo builds them: they were
drawn once from the measurements in the documents and are shipped as the reference copies. Every
number in a figure appears in the markdown beside it, so the figure is for orientation and the text is
the authority.

### `build_nand_layout.py` — the whole disk from the map

```
python build_nand_layout.py -m ../maps/TCC880X_NAND.ami --check
python build_nand_layout.py -m ../maps/TCC880X_NAND.ami -o nand_layout.fai
python build_nand_layout.py -m ../maps/TCC880X_NAND.ami -o nand_layout.fai --inject boot=boot.img
```

Reads `../maps/TCC880X_NAND.ami`, validates that the fifteen partitions tile the area with no gaps,
and writes a `FILESYSTEM_IMAGE` container: the 16 KiB MBR area, then `0xFF` to the last byte. It also
serves as the map's validator — `--check` runs the same identities FWDN does and writes nothing.

`--inject NAME=FILE` drops your own image into a partition instead of fill. `--partition NAME` emits
one partition on its own, which declares a single-entry geometry and makes the tool **rewrite sector
0** — the script says so out loud; see `../docs/12` before using it.

### `build_mbr.py` — rebuild the partition map

```
python build_mbr.py -o mbr_header.bin
python build_mbr.py -o mbr_header.bin --verify "C:/path/to/nand_dump.img"
```

Writes the 16 KiB header area (four MBR entries + `FF` fill) from the geometry in
`../docs/06`. `--verify` compares it against the first 16 KiB of a dump and exits non-zero on any
difference — use it before writing anything to NAND. The output for the reference unit is byte-exact
against its chip read; see `../docs/12`.

### `build_fai.py` — wrap a payload in an FWDN container

```
python build_fai.py -p mbr_header.bin --start-sector 0 --sectors 4004864 -o mbr_restore.fai
```

640-byte header + payload, with the two size pairs (`0x236`/`0x23A` and `0x270`/`0x278`) kept in
agreement so the tool does not answer `Part Size Value is wrong!`. Field map is in the file's
docstring and in `vendor/README.md`.

### `make_preview.py` — offline browse of every document

```bash
python make_preview.py      # writes ../preview.html, opens with any browser
```

## vendor/

Telechips' FWDN tool and VTC USB driver, checksummed, plus the reverse-engineered `.fai`/`.dum`
container format. See [`vendor/README.md`](vendor/README.md) — it is the page to read before you
hand-build anything the downloader will accept.
