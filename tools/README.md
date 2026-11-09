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

### `make_figures.py` — regenerate the diagrams in `../images/`

```bash
pip install pillow
python make_figures.py
```

Pure PIL, no data files, Segoe UI from `C:\Windows\Fonts`. Every number drawn in the figures is also
in the markdown next to them — the figures are for orientation, the text is the reference.

### `make_figures_fwdn.py` — the connector / strap / timing figures

```bash
python make_figures_fwdn.py --src "S:/path/to/photos"
```

Draws `fig05`–`fig07` and writes the two cropped photos (`photo-cn902-connector.jpg`,
`photo-fwdn-strap.jpg`) that those figures are built from. It needs the two original board photographs
(`ANNOTATED_CN902_front.jpg` and `FWDN_TP764.png`) in `--src`; without them the figures cannot be
rebuilt, so the committed PNGs are the reference copies.

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
