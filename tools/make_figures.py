#!/usr/bin/env python3
"""Generate the annotated figures for the Kenwood DNN990HD writeup.
Pure PIL, no external assets. Output: ../images/*.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
os.makedirs(OUT, exist_ok=True)

F = "C:/Windows/Fonts/segoeui.ttf"
FB = "C:/Windows/Fonts/segoeuib.ttf"
def f(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)

BG = (18, 20, 24); FG = (232, 236, 240); DIM = (150, 158, 168)
ACC = (86, 170, 255); WARN = (255, 176, 64); BAD = (240, 96, 96); OK = (110, 210, 130)

def canvas(w, h, title, sub=""):
    im = Image.new("RGB", (w, h), BG); d = ImageDraw.Draw(im)
    d.text((40, 26), title, font=f(30, True), fill=FG)
    if sub: d.text((40, 66), sub, font=f(17), fill=DIM)
    d.line((40, 96, w - 40, 96), fill=(60, 66, 74), width=1)
    return im, d

def box(d, x, y, w, h, text, col=FG, edge=(70, 78, 88), fill=(30, 34, 40), size=18, bold=False):
    d.rounded_rectangle((x, y, x + w, y + h), 8, fill=fill, outline=edge, width=2)
    lines = text.split("\n")
    lh = size + 6
    ty = y + (h - lh * len(lines)) // 2 + 2
    for ln in lines:
        tw = d.textlength(ln, font=f(size, bold))
        d.text((x + (w - tw) // 2, ty), ln, font=f(size, bold), fill=col)
        ty += lh

def arrow(d, x1, y1, x2, y2, col=(110, 120, 132)):
    d.line((x1, y1, x2, y2), fill=col, width=3)
    import math
    a = math.atan2(y2 - y1, x2 - x1); L = 11
    for s in (-0.5, 0.5):
        d.line((x2, y2, x2 - L * math.cos(a - s), y2 - L * math.sin(a - s)), fill=col, width=3)

def wrap(d, xy, text, width, font, fill=FG, lh=24):
    x, y = xy; words = text.split(); line = ""
    for wd in words:
        t = (line + " " + wd).strip()
        if d.textlength(t, font=font) > width:
            d.text((x, y), line, font=font, fill=fill); y += lh; line = wd
        else:
            line = t
    if line: d.text((x, y), line, font=font, fill=fill); y += lh
    return y

# ---------------------------------------------------------------- fig 01
def fig01():
    W, H = 1500, 1260
    im, d = canvas(W, H, "DNN990HD boot chain — where the panel dies and where /data is lost",
                   "Every stage below is read from the unit's own firmware (1.8.0, build binks_v8-userdebug)")
    steps = [
        ("LK bootloader (bootloader.img)", "shows system/media/bootanimation.zip  ->  the 'System Rebuilding...' frame", FG),
        ("Linux 3.0.8-tcc kernel", "cmdline on the chip: vmalloc=256M console=ttyTCC0,115200n8 resume=/dev/block/ndda11", FG),
        ("init  ->  on fs", "e2fsck -fy ndda3  then  mount ext4 ndda3 /data  (errors=panic,data=journal,commit=1)", FG),
        ("setup_fs ndda3 ndda5 ndda12 ndda13", "'create filesystems if necessary' - reformats any partition it cannot verify", WARN),
        ("Zygote / system_server", "surfaceflinger, adbd (ro.debuggable=1 -> root shell), no hwcomposer", FG),
        ("SurfaceFlinger  ->  exec /system/bin/vmute", "one ioctl on /dev/kwgpio (0x4208a629) gates the LCD video line", BAD),
        ("KWLauncher (Adobe AIR)", "reads skin_type from KwSystemService configuration.db (this unit: TypeC)", FG),
    ]
    y = 120
    for i, (t1, t2, col) in enumerate(steps):
        box(d, 70, y, 640, 86, t1, col=col, size=20, bold=True)
        d.text((740, y + 18), "", font=f(16))
        wrap(d, (740, y + 14), t2, 700, f(16), fill=DIM, lh=22)
        if i < len(steps) - 1: arrow(d, 390, y + 86, 390, y + 112)
        y += 110
    # side annotations
    d.rounded_rectangle((70, 900, 1440, 984), 8, fill=(48, 32, 20), outline=WARN, width=2)
    d.text((90, 916), "THE LOOP:", font=f(20, True), fill=WARN)
    d.text((230, 916), "if setup_fs cannot verify ndda3's filesystem it reformats /data -> empty /data -> setup wizard -> restart -> repeat."
                       , font=f(16), fill=FG)
    d.text((230, 944), "This is why a firmware flash and a Settings 'erase everything' never helped: neither one repairs ndda3.", font=f(16), fill=FG)
    d.rounded_rectangle((70, 1000, 1440, 1084), 8, fill=(46, 22, 22), outline=BAD, width=2)
    d.text((90, 1016), "PANEL DEATH:", font=f(20, True), fill=BAD)
    d.text((300, 1016), "vmute is exec'd at boot-complete; replacing it with a no-op script restores the display permanently (survives /data wipes).", font=f(16), fill=FG)
    d.text((300, 1044), "Stock md5 acadb8e58e5f370bd224ee7516332b49  ->  replacement 275 B script md5 2b95ede435392cf62eaccf8b69b30701", font=f(15), fill=DIM)
    d.line((40, 1110, W - 40, 1110), fill=(60, 66, 74))
    yy = 1130
    for ln in [
        "cmdline on chip : vmalloc=256M console=ttyTCC0,115200n8 vmalloc=256M resume=/dev/block/ndda11 androidboot.memtype=1 (LK appends the last two)",
        "vendor boot.img : vmalloc=256M console=null vmalloc=256M      <- Kenwood nulls the console in the shipping image",
        "USB identities  : 18D1:DEED adb+mass_storage | 18D1:B058 mass_storage | 18D1:D00D LK fastboot | 140E:B068 FWDN | 140E:A020/A021 rndis",
    ]:
        d.text((70, yy), ln, font=f(15), fill=DIM); yy += 26
    im.save(os.path.join(OUT, "fig01-boot-chain.png"))


def fig02():
    parts = [("ndda1", 32, 20480, "boot  ANDROID!"), ("ndda2", 20512, 962560, "/system ext4"),
             ("ndda3", 983072, 716800, "/data ext4"), ("ndda4", 1699872, 32, "MBR artefact"),
             ("ndda5", 1699904, 307232, "/cache ext4"), ("ndda6", 2007136, 20512, "recovery EMPTY"),
             ("ndda7", 2027648, 10272, "unused"), ("ndda8", 2037920, 10272, "unused"),
             ("ndda9", 2048192, 2080, "unused"), ("ndda10", 2050272, 2080, "unused"),
             ("ndda11", 2052352, 307232, "hibernate snapshot"), ("ndda12", 2359584, 20512, "/.sysinfo ext4"),
             ("ndda13", 2380096, 16416, ".garmin ext4"), ("ndda14", 2396512, 2080, "snapshot hdr"),
             ("ndda15", 2398592, 1606272, "zero fill")]
    TOTAL = 4004864
    W, H = 1560, 780
    im, d = canvas(W, H, "NAND partition layout — TH58NVG4S0FTAK0, 2 GiB, 512-byte sectors",
                   "kernel static table; sizes derived from consecutive starts and reconcile to 4,004,864 sectors = 2,050,490,368 bytes")
    x0, x1 = 60, 1500; bw = x1 - x0
    y = 150; bh = 74
    for name, st, sz, role in parts:
        w = max(3, int(bw * sz / TOTAL)); col = (52, 84, 126)
        if "data" in role: col = (150, 96, 40)
        if "EMPTY" in role: col = (150, 50, 50)
        if "system" in role: col = (40, 110, 70)
        d.rounded_rectangle((x0, y, x0 + w, y + bh), 3, fill=col, outline=(200, 210, 220))
        x0 += w
    # tick labels for the big ones only
    x0 = 60
    for name, st, sz, role in parts:
        w = max(3, int(bw * sz / TOTAL))
        if w > 60:
            t = name
            d.text((x0 + w // 2 - d.textlength(t, font=f(16, True)) // 2, y + 8), t, font=f(16, True), fill=(255, 255, 255))
            s = f"{sz*512/2**20:.0f} MB"
            d.text((x0 + w // 2 - d.textlength(s, font=f(14)) // 2, y + 34), s, font=f(14), fill=(235, 240, 245))
        x0 += w
    # callouts for the small ones
    small = [p for p in parts if bw * p[2] / TOTAL <= 60]
    yy = y + bh + 40
    for i, (name, st, sz, role) in enumerate(small):
        col = 60 + (i % 4) * 370; row = i // 4
        d.text((col, yy + row * 26), f"{name}  {sz*512//1024} KiB  {role}", font=f(15), fill=DIM)
    # table
    ty = yy + 3 * 26 + 20
    d.text((60, ty), "name      start sector     size (sectors)      size        role", font=f(16, True), fill=FG)
    ty += 28
    for name, st, sz, role in parts:
        line = f"{name:<9} {st:>12,} {sz:>18,} {sz*512/2**20:>9.1f} MB   {role}"
        d.text((60, ty), line, font=f(15), fill=(200, 208, 216)); ty += 21
    d.text((60, ty + 8), f"last end {parts[-1][1]+parts[-1][2]:,} sectors x 512 = {TOTAL*512:,} bytes = image size  OK",
           font=f(16, True), fill=OK)
    im.save(os.path.join(OUT, "fig02-partitions.png"))

# ---------------------------------------------------------------- fig 03
def fig03():
    W, H = 1400, 800
    im, d = canvas(W, H, "The panel-dark fault: the vmute chain",
                   "root cause established on this unit - the LCD is switched off by software one second after boot-complete")
    box(d, 80, 140, 340, 96, "SurfaceFlinger\n(boot-complete)", size=19, bold=True)
    box(d, 530, 140, 340, 96, "exec /system/bin/vmute", col=WARN, size=19, bold=True)
    box(d, 980, 140, 340, 96, "open(\"/dev/kwgpio\")", size=19, bold=True)
    arrow(d, 420, 188, 530, 188); arrow(d, 870, 188, 980, 188)
    box(d, 980, 300, 340, 96, "ioctl(3, 0x4208a629, ...)", col=BAD, size=19, bold=True)
    arrow(d, 1150, 236, 1150, 300)
    box(d, 980, 460, 340, 96, "LCD video line OFF\n(panel goes dark, unit keeps running)", col=BAD, size=17, bold=True)
    arrow(d, 1150, 396, 1150, 460)
    d.rounded_rectangle((80, 300, 900, 400), 8, fill=(30, 34, 40), outline=(70, 78, 88), width=2)
    d.text((100, 316), "Stock vmute: 275 B shell script, md5 acadb8e58e5f370bd224ee7516332b49", font=f(16), fill=DIM)
    d.text((100, 344), "Fix: replace it with a no-op that still exists and is still mode 755.", font=f(16), fill=FG)
    d.text((100, 370), "SurfaceFlinger only exec()s the path - it does not verify behaviour.", font=f(16), fill=OK)
    d.rounded_rectangle((80, 460, 900, 706), 8, fill=(22, 40, 28), outline=OK, width=2)
    d.text((100, 476), "Why this fix survives everything", font=f(19, True), fill=OK)
    yy = 510
    for ln in ["- it lives in /system, which a factory data reset does not touch",
               "- it is re-applied by nothing: it simply never runs the ioctl again",
               "- a firmware flash DOES undo it (the vendor package restores stock vmute),",
               "  so re-apply after any update or FWDN restore",
               "- the LCD backlight is separate: no /sys/class/leds/lcd-backlight exists on this kernel",
               "- brightness lives in the mediaplayer DB as screen_brightness = 102"]:
        d.text((100, yy), ln, font=f(16), fill=FG); yy += 28
    d.text((80, 736), "Do not chase the MCU: keys work, the panel tilt motor works, so Syscom/panelcom are alive.",
           font=f(17, True), fill=WARN)
    im.save(os.path.join(OUT, "fig03-vmute-chain.png"))

# ---------------------------------------------------------------- fig 04
def fig04():
    W, H = 1500, 760
    im, d = canvas(W, H, "Android boot image header — 2048-byte page, as used by this unit",
                   "patch ONLY ramdisk_size at header offset 16; every other header byte must stay as found")
    fields = [("magic 'ANDROID!'", 0, 8), ("kernel_size", 8, 4), ("kernel_addr", 12, 4),
              ("ramdisk_size", 16, 4), ("ramdisk_addr", 20, 4), ("second_size", 24, 4),
              ("second_addr", 28, 4), ("tags_addr", 32, 4), ("page_size", 36, 4),
              ("(unused)", 40, 4), ("(unused)", 44, 4), ("board name[16]", 48, 16),
              ("cmdline[512]", 64, 512)]
    x0, y = 60, 150; scale = 2.4
    for name, off, ln in fields:
        w = max(28, int(ln * scale))
        col = (150, 96, 40) if off == 16 else (52, 84, 126)
        d.rounded_rectangle((x0, y, x0 + w, y + 64), 4, fill=col, outline=(200, 210, 220))
        d.text((x0 + 6, y + 22), f"+{off}", font=f(14, True), fill=(255, 255, 255))
        if w > 60:
            d.text((x0 + 6, y + 44), name[:16], font=f(13), fill=(225, 232, 240))
        x0 += w + 4
        if x0 > 1380: x0 = 60; y += 90
    ty = 300
    d.text((60, ty), "Values as found on this unit (read from ndda1 inside the NAND image):", font=f(19, True), fill=FG)
    ty += 40
    for ln in ["page_size   = 2048",
               "kernel      = 8,093,284 bytes   load address 0x40008000",
               "ramdisk     = 1,735,786 bytes   load address 0x41000000   (vendor package: 1,741,626)",
               "second      = 0 bytes           load address 0x40f00000",
               "tags_addr   = 0x40000100",
               "cmdline     = vmalloc=256M console=ttyTCC0,115200n8 vmalloc=256M   (50 bytes, the rest of the field is zero)",
               "              LK adds  resume=/dev/block/ndda11 androidboot.memtype=1  at runtime; vendor package has console=null instead"]:
        d.text((60, ty), ln, font=f(16), fill=(205, 213, 222)); ty += 30
    d.rounded_rectangle((60, ty + 14, 1440, ty + 104), 8, fill=(22, 30, 44), outline=ACC, width=2)
    d.text((80, ty + 28), "Repack rules", font=f(18, True), fill=ACC)
    d.text((80, ty + 56), "ramdisk must stay gzip + cpio 'newc' with a TRAILER!!! entry and 4-byte alignment. Do not touch the 512-byte cmdline", font=f(16), fill=FG)
    d.text((80, ty + 82), "block unless you intend to change the console - and on this unit ttyTCC0 is already enabled.", font=f(16), fill=FG)
    im.save(os.path.join(OUT, "fig04-boot-header.png"))

fig01(); fig02(); fig03(); fig04()
print("figures written to", os.path.abspath(OUT))
for n in sorted(os.listdir(OUT)): print("  ", n, os.path.getsize(os.path.join(OUT, n)), "B")
