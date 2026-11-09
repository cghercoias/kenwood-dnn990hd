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
