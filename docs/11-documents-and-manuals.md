# 11 — Documents worth having (and why they are not in this repo)

Every PDF referenced below is the manufacturer's own copyrighted material — Kenwood's owner manuals,
Telechips' SoC datasheet, Toshiba's memory datasheets. They are **not** redistributed here. What is
here is the index: part numbers, exact file names and what each one is actually good for, so you can
get the same set from the vendor or from the copy that came with your unit.

Kenwood's support site carries the DNN990HD manuals by model (`DNN990HD` → *Manuals*); the firmware
update instructions ship inside each update package as well, so if you have the `.kw` or the FAI set
you already have them.

## Unit manuals

| file | part number | size | what it is good for |
|---|---|---|---|
| `Kenwood DNN990HD Instruction Manual.pdf` | — | 11.7 MB | the owner's manual: menus, sources, nav, Bluetooth, settings. This is the document the on-screen UI assumes you have read. |
| `B59-2163-00_quick_start_guide.pdf` | **B59-2163-00** | 33.6 MB | quick start guide, DNN990HD / DNN770HD. Wiring, installation, first power-up. |
| `DNN990HD_DNN770HD_reference_guide_IM365.pdf` | **IM365** | 21.5 MB | reference guide, both models. The most complete printed description of the UI. |

The `_unlocked` copies of the two large guides are the same documents with the print/password
restrictions removed for searching — text extraction works, which is why they are worth having if you
intend to grep for a menu string.

## Firmware update instructions

| file | size | what it is good for |
|---|---|---|
| `13DNN_FWupdate_en.pdf` | 392 KB | the short procedure for the stock update path (USB stick, `programinfo.bin`, the greyed-out **Update** button). This is the document that explains why an already-current unit cannot be updated from the UI — see [docs/04](04-vendor-update-attempt.md). |
| `13DNN-FW_en.pdf` | 1.8 MB | the full firmware-update manual, with the failure table and the recovery section. |
| `13DNN_DAB-FWupdate_en.pdf` | 492 KB | the DAB variant's copy of the same procedure. The screens are identical, which makes it a useful cross-check on version numbering. |

None of these mention FWDN. The boot-ROM route in [docs/09](09-fwdn-mode.md) is not a Kenwood
procedure at all — it is Telechips' chip-level downloader, which is why it needed reverse engineering
rather than a manual.

## Silicon datasheets

| file | size | why it is on this bench |
|---|---|---|
| `TCC8801.pdf` | 1.0 MB | the SoC itself: memory map, boot modes, USB device controller, the NAND controller the bootloader drives. Everything in [docs/06](06-partitions-and-boot-image.md) that is not measured is from here. |
| `TC58NVG3S0FTA00.PDF` | 40 KB | Toshiba NAND in the same TSOP-48 SLC family as the fitted `TH58NVG4S0FTAK0`. Not the exact part — a close reference for how these devices are organised (page, block, OOB), which is the arithmetic the sector counts in [docs/10](10-nand-backup-with-fwdn.md) rest on. |
| `THGAF4G8N2LBAIR.PDF` | 2.6 MB | Toshiba eMMC, collected while working out what is actually fitted. The unit turned out to carry raw NAND, so this one is background only — an eMMC board would need a completely different backup route (`dd` from a shell, no FWDN sector dump). |
| `Ricoh_R1180N_150mA_LDO_SOT-23-5.pdf` | 557 KB | power rail parts on the processor board, used while chasing the dead panel ([docs/02](02-panel-dark-fix.md)). |
| `Ricoh_R5325x_dual_150mA_LDO_SOT-23-6.pdf` | 466 KB | ditto — the dual LDO next to it. |
| `XC6220_Torex_1A_LDO_SOT-25.pdf` | 538 KB | the second-source LDO fitted on some boards. |
| `XC6220_DYW-second-source_with_marking_table.pdf` | 389 KB | Torex's own top-marking table for XC6220 — the document that lets you read the two-character code on the part and know which rail you are looking at. |
| `XC6223_Torex_300mA_LDO_SOT-25.pdf` | 803 KB | related 300 mA part, same footprint family. |

## How this set was used

Roughly: manuals to understand what the unit is *supposed* to do, the SoC datasheet to understand what
the bootloader can do, and the memory datasheet to know what the backup actually contains. The
diagnosis in [docs/05](05-firmware-analysis.md) came from the firmware itself — the manuals only
confirm intent.

Next: back to [docs/08](08-cn902-port-and-cable.md) if you are about to open the unit, or
[docs/03](03-nand-backup-and-restore.md) if you already have a shell.
