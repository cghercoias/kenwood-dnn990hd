#!/usr/bin/env python3
"""Generate the FWDN chapter figures (05-07) for the Kenwood DNN990HD writeup.

Reads the two board photographs, crops them down to the area that matters,
and draws the annotation on top. Pure PIL.

    python make_figures_fwdn.py [--src DIR]

--src is the folder holding ANNOTATED_CN902_front.jpg and FWDN_TP764.png.
Default is the bench share; pass any path that contains them.
Output: ../images/*.png  and  ../images/photo-*.jpg
"""
import argparse, os, math
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images")
os.makedirs(OUT, exist_ok=True)

RESAMPLE_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

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

def arrow(d, x1, y1, x2, y2, col=(110, 120, 132), w=3):
    d.line((x1, y1, x2, y2), fill=col, width=w)
    a = math.atan2(y2 - y1, x2 - x1); L = 11
    for s in (-0.5, 0.5):
        d.line((x2, y2, x2 - L * math.cos(a - s), y2 - L * math.sin(a - s)), fill=col, width=w)

def wrap(d, xy, text, width, font, fill=FG, lh=24):
    x, y = xy; line = ""
    for wd in text.split():
        t = (line + " " + wd).strip()
        if d.textlength(t, font=font) > width:
            d.text((x, y), line, font=font, fill=fill); y += lh; line = wd
        else:
            line = t
    if line: d.text((x, y), line, font=font, fill=fill); y += lh
    return y

def paste_fit(im, src, box, label="", border=(70, 78, 88)):
    """Scale src to fit (w,h) of box, centre it, draw a frame. Returns (x,y,w,h) placed."""
    x, y, w, h = box
    sw, sh = src.size; k = min(w / sw, h / sh)
    nw, nh = int(sw * k), int(sh * k)
    im.paste(src.resize((nw, nh), RESAMPLE_LANCZOS), (x + (w - nw) // 2, y + (h - nh) // 2))
    d = ImageDraw.Draw(im)
    d.rectangle((x, y, x + w, y + h), outline=border, width=2)
    if label:
        d.text((x + 8, y + h - 26), label, font=f(15), fill=DIM)
    return x + (w - nw) // 2, y + (h - nh) // 2, nw, nh

def crop_to(src, box, scale=1.0):
    x1, y1, x2, y2 = box
    c = src.convert("RGB").crop((x1, y1, x2, y2))
    if scale != 1.0:
        c = c.resize((int(c.width * scale), int(c.height * scale)), RESAMPLE_LANCZOS)
    return c

# ---------------------------------------------------------------- fig 05
def fig05(src_cn902):
    W, H = 1580, 900
    im, d = canvas(W, H, "CN902 - the SoC USB device port, and the cable that works",
                   "Measured pin functions, not read off a photograph: every row below was settled with a meter")
    crop = crop_to(src_cn902, (1248, 415, 1522, 725))
    crop.save(os.path.join(OUT, "photo-cn902-connector.jpg"), quality=90)
    ctx = crop_to(src_cn902, (1090, 388, 1790, 880), 0.9)
    ctx.save(os.path.join(OUT, "photo-cn902-context.jpg"), quality=88)
    px, py, pw, ph = paste_fit(im, crop, (60, 130, 520, 560), "CN902, 4 contacts (crop of the board photo)")

    # bracketed callout: no per-pin numbers on the photo, orientation is a meter question
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((px + pw - 168, py + ph // 4, px + pw - 18, py + ph // 4 + 150), 6,
                        outline=WARN, width=3)
    d.text((px + pw - 168, py + ph // 4 - 28), "4 contacts", font=f(16, True), fill=WARN)

    d.text((60, 700), "How to find pin 1 without trusting a photo:", font=f(18, True), fill=ACC)
    wrap(d, (60, 728),
         "power off, meter on continuity, one probe on a chassis screw boss, touch each contact in turn. "
         "Exactly one reads 0 ohm - that is pin 1, GND. Count 1-2-3-4 along the housing from there and "
         "you are done; no diagram can tell you which physical end that is.",
         460, f(16), fill=DIM, lh=22)

    # right: pin table
    x0, y0 = 640, 130
    d.text((x0, y0 - 6), "PIN  FUNCTION                CABLE WIRE      EXPECTED READING", font=f(16, True), fill=ACC)
    rows = [
        ("1", "GND", "black", "0 ohm to chassis", OK),
        ("2", "D+", "green", "0 V, then ~3.0-3.3 V once the SoC pulls up", FG),
        ("3", "D-", "white", "0 V always unless traffic is flowing", FG),
        ("4", "chassis / shield bond", "not connected", "0 V, or grounded by screw #3", WARN),
    ]
    yy = y0 + 30
    for pin, fn, wire, exp, col in rows:
        d.rectangle((x0, yy, x0 + 900, yy + 62), outline=(60, 66, 74))
        d.text((x0 + 14, yy + 18), pin, font=f(22, True), fill=col)
        d.text((x0 + 60, yy + 10), fn, font=f(17, True), fill=FG)
        d.text((x0 + 60, yy + 34), wire, font=f(15), fill=DIM)
        wrap(d, (x0 + 300, yy + 18), exp, 580, f(16), fill=col, lh=20)
        yy += 66

    d.rounded_rectangle((x0, yy + 16, x0 + 900, yy + 116), 8, fill=(48, 24, 24), outline=BAD, width=2)
    d.text((x0 + 18, yy + 28), "CUT THE RED WIRE.", font=f(20, True), fill=BAD)
    wrap(d, (x0 + 18, yy + 58),
         "The unit is a self-powered device port: it needs no VBUS. Feeding +5 V from the cable's red lead "
         "into pin 4 destroyed a USB hub on this bench (smoke). Red lead cut, pin 4 open.", 860, f(16), fill=FG, lh=21)

    d.rounded_rectangle((x0, yy + 136, x0 + 900, yy + 226), 8, fill=(26, 36, 44), outline=ACC, width=2)
    d.text((x0 + 18, yy + 148), "THE 1 kOhm RESISTOR IS NOT IN THIS CABLE.", font=f(19, True), fill=ACC)
    wrap(d, (x0 + 18, yy + 178),
         "In series with a 5 V feed it only sank ~5 mA to ground and changed nothing. Its one useful job is "
         "on the FWDN strap pads (next figure).", 860, f(16), fill=FG, lh=21)
    im.save(os.path.join(OUT, "fig05-cn902-pinout.png"))
    print("fig05", im.size)

# ---------------------------------------------------------------- fig 06
def fig06(src_strap):
    W, H = 1580, 900
    im, d = canvas(W, H, "The FWDN strap: two pads beside TP764, and how to hold them down",
                   "Sampled once, at reset. If it is not grounded before 12 V arrives, the unit boots Android as usual")
    crop = crop_to(src_strap, (755, 295, 1035, 505))
    crop.save(os.path.join(OUT, "photo-fwdn-strap.jpg"), quality=92)
    px, py, pw, ph = paste_fit(im, crop, (60, 130, 640, 404), "")

    d = ImageDraw.Draw(im)
    bx, by = px + int(pw * 0.40), py + int(ph * 0.33)
    bw, bh = int(pw * 0.15), int(ph * 0.24)
    d.rectangle((bx, by, bx + bw, by + bh), outline=BAD, width=3)
    d.text((bx - 84, by - 32), "the two pads", font=f(16, True), fill=BAD)
    arrow(d, bx - 78, by - 8, bx - 6, by + 6, col=BAD, w=3)

    d.text((60, 550), "pads beside the TP764 silkscreen (owner's macro, cropped)", font=f(15), fill=DIM)
    d.text((60, 582), "Too small to solder safely - a lifted pad ends the project.", font=f(17, True), fill=WARN)
    wrap(d, (60, 614),
         "Find the grounded pad first, powered off: one pad reads ~0 ohm to chassis, the other runs to the SoC "
         "boot pin. Only the signal pad has to reach ground, so one contact is enough - no bridge, nothing soldered.",
         610, f(15), fill=DIM, lh=21)

    x0 = 720
    steps = [
        ("1", "1 kOhm across the pair - the safe test", "Power up and watch the host. If the Telechips device appears, the pair really is the strap and you never need a hard short.", ACC),
        ("2", "Then the no-solder contact", "Sewing needle or 0.2 mm music wire in a third-hand clamp, clip lead from the needle to a chassis screw boss. One contact, both hands free. A blunt pogo tip is kinder than a sharp point.", FG),
        ("3", "Bridge before 12 V, release after", "The level is latched at reset, so it only has to be present at power-up. Lift it as soon as the tool reports the device - and lift it fully clear, not just off the pad.", FG),
        ("4", "Screw #3 out", "With screw #3 fitted, pin 4 of CN902 is bonded to chassis. Leave it out for every device-mode and boot-ROM session.", FG),
    ]
    yy = 118
    for n, t1, t2, col in steps:
        d.rounded_rectangle((x0, yy, x0 + 800, yy + 142), 8, fill=(30, 34, 40), outline=(70, 78, 88), width=2)
        d.text((x0 + 18, yy + 16), n, font=f(28, True), fill=col)
        d.text((x0 + 60, yy + 18), t1, font=f(18, True), fill=col)
        wrap(d, (x0 + 60, yy + 50), t2, 720, f(16), fill=DIM, lh=22)
        yy += 152

    d.rounded_rectangle((60, 742, 1520, 862), 8, fill=(26, 36, 44), outline=ACC, width=2)
    d.text((78, 754), "WHY THIS PAD AND NOT THE CONNECTOR: the earlier 1 kOhm feed on CN902 pin 4 is withdrawn.",
           font=f(17, True), fill=ACC)
    wrap(d, (78, 784),
         "Pin 4 turned out to be a chassis/shield-bond net, so that feed was sinking ~5 mA into ground while "
         "changing nothing - and with the resistor removed it shorted the host's VBUS to ground. The pad is the "
         "selector; a short there is what puts the SoC into boot-ROM. Lift the bridge and the unit boots Android again.",
         1420, f(16), fill=FG, lh=22)
    im.save(os.path.join(OUT, "fig06-fwdn-strap.png"))
    print("fig06", im.size)

# ---------------------------------------------------------------- fig 07
def fig07():
    W, H = 1580, 800
    im, d = canvas(W, H, "The FWDN window: about 19 seconds, once per power-up",
                   "Measured on this unit. The tool has to be running and waiting before 12 V is applied")
    base = 300
    d.line((60, base, 1520, base), fill=(70, 78, 88), width=3)
    marks = [
        (60, "0 s", "12 V applied, strap held down"),
        (300, "0-2 s", "boot ROM -> UBS loader -> VTC device"),
        (560, "~2 s", "host: 140E:B068 appears"),
        (900, "2-19 s", "the tool's window"),
        (1240, "~19 s", "self-shutdown or watchdog reset"),
    ]
    for x, t, lbl in marks:
        d.line((x, base - 14, x, base + 14), fill=FG, width=2)
        d.text((x - 14, base - 46), t, font=f(18, True), fill=FG)
        wrap(d, (x - 14, base + 26), lbl, 250, f(15), fill=DIM, lh=20)

    d.rounded_rectangle((590, 150, 1210, 250), 8, fill=(26, 36, 44), outline=OK, width=2)
    d.text((608, 162), "WHAT THE TOOL MUST ALREADY BE DOING", font=f(16, True), fill=OK)
    wrap(d, (608, 190),
         "FWDN_V7_v2.30.exe open, bootloader.img added with Target = BOOT, then power the unit. "
         "No host session in the window and the unit simply powers off - that is a normal result, not a fault.",
         600, f(15), fill=FG, lh=20)

    d.rounded_rectangle((60, 470, 760, 700), 8, fill=(48, 24, 24), outline=BAD, width=2)
    d.text((78, 484), "WHAT THE UNIT'S OWN SCREEN DOES: NOTHING", font=f(18, True), fill=BAD)
    wrap(d, (78, 514),
         "In boot-ROM mode the panel has no backlight at all - not a black image, the backlight itself is dark. "
         "Fans run. That dark panel is the discriminator: a lit backlight with a black picture means a normal "
         "power state with a dead display path, which is a different fault entirely.",
         660, f(16), fill=FG, lh=22)

    d.rounded_rectangle((800, 470, 1520, 700), 8, fill=(30, 34, 40), outline=(70, 78, 88), width=2)
    d.text((818, 484), "ON THE PC, IN ORDER", font=f(18, True), fill=FG)
    lines = [
        "140E:B068 found -> that is FWDN (Telechips). 18D1:xxxx would be Android/LK.",
        "\"Unknown device\" with that ID = mode is right, driver is missing.",
        "Dialog 'Device Probing' with No Boot File error = no BOOT row in the file list.",
        "\"Device's SerialNumber : <serial>\" = session is live.",
        "Log line 'Download is complete!' or a finished Dump = the operation really ran.",
    ]
    yy = 516
    for ln in lines:
        wrap(d, (818, yy), "-  " + ln, 680, f(16), fill=DIM, lh=21); yy += 34
    im.save(os.path.join(OUT, "fig07-fwdn-window.png"))
    print("fig07", im.size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="S:/ELECTRONICA/AUDIO/CAR_AUDIO/KENWOOD/photos")
    a = ap.parse_args()
    cn = Image.open(os.path.join(a.src, "ANNOTATED_CN902_front.jpg"))
    st = Image.open(os.path.join(a.src, "FWDN_TP764.png"))
    fig05(cn); fig06(st); fig07()

if __name__ == "__main__":
    main()
