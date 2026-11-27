"""Partitioning Oracle Attacks: hybrid cartoon + diagram Short for 0xLore.

Usage: python3 render.py <dir with kokoro model files> <output.mp4> [cover.jpg]
Cartoon lines ("C") play on the night rooftop. Diagram lines ("D") raise a
glowing screen over the rooftop and shrink the characters below it.
All facts: Len, Grubbs, Ristenpart, "Partitioning Oracle Attacks",
USENIX Security 2021 (see script.md for the source of each line).
"""
import sys, os, re, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import soundfile as sf
from multiprocessing import Pool

WORK, OUT = sys.argv[1], sys.argv[2]
COVER = sys.argv[3] if len(sys.argv) > 3 else None
W, H, FPS, SR, SS = 1080, 1920, 30, 24000, 2
INK = (22, 20, 38); YEL = (255, 210, 40); WHITE = (245, 247, 252); RED = (255, 90, 90)
GREEN = (90, 225, 130); DIM = (160, 172, 205); PANEL = (14, 24, 52); NAVY = (8, 15, 36); GRID = (22, 36, 70)
F = "/usr/share/fonts/opentype/inter/"; DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONOF = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def font(n, s): return ImageFont.truetype(F + n, s)
XB = "Inter-ExtraBold.otf" if os.path.exists(F + "Inter-ExtraBold.otf") else "Inter-Bold.otf"
CAP = font(XB, 76); LBL = font("Inter-Bold.otf", 54); LBL_S = font("Inter-SemiBold.otf", 40)
TITLE = font(XB, 84); BIGN = font(XB, 150)

# ------------------------------------------------------------------ script
# (speaker, mode, text). *word* = yellow keyword.
LINES = [
 ("rio", "C", "Guessing a password online is slow. One guess... one try."),
 ("mina", "C", "What if one try could test *4,091* passwords at once?"),
 ("mina", "D", "Picture a server that hides behind a password. Send the wrong one... and it says *nothing*. No error. Just silence."),
 ("rio", "C", "So I can't even tell if I'm close."),
 ("mina", "D", "But send the *right* one, and the server quietly opens a *door* to wait for a reply. And you can see that door from outside. That's a *leak*. A simple yes or no."),
 ("mina", "C", "Now the twist. Some encryption, like AES-GCM, lets you build one message that unlocks with *thousands* of different passwords."),
 ("rio", "C", "Wait. One message, thousands of passwords?"),
 ("mina", "D", "*4,091* of them. Door stays *shut*? All 4,091 are wrong. Gone in one go. Door *opens*? The password is in that group. So *split* it in half... and try *again*."),
 ("mina", "D", "Like a game of *twenty* *questions*. Every answer cuts the list in half."),
 ("rio", "C", "Does that actually work?"),
 ("mina", "D", "In simulations with real leaked passwords, one in five was cracked in just *124* tries. Normal guessing? Around *60,000*."),
 ("mina", "C", "It's called a *partitioning* *oracle* attack. Researchers found it in a real proxy tool, Shadowsocks, and helped fix it."),
 ("rio", "C", "Follow *0xLore* for more hidden gems."),
]
VOICE = {"rio": "am_michael", "mina": "af_heart"}
SAY = {"4,091": "four thousand ninety-one", "124": "a hundred and twenty-four", "60,000": "sixty thousand",
       "32": "thirty-two", "AES-GCM": "A-E-S G-C-M", "0xLore": "oh-ex Lore", "Shadowsocks": "Shadow-socks"}
def tts_text(s):
    s = s.replace("*", "").replace("...", ",")
    for k, v in sorted(SAY.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", v, s)
    return s
def clean(w): return re.sub(r"[^\w-]", "", w.replace("*", "")).lower()

from kokoro_onnx import Kokoro
kok = Kokoro(os.path.join(WORK, "kokoro-v1.0.onnx"), os.path.join(WORK, "voices-v1.0.bin"))
def trim(x, thr=0.01):
    i = np.where(np.abs(x) > thr)[0]; return x[max(i[0] - 240, 0): i[-1] + 480]

voice, words, turns = [np.zeros(int(SR * 0.25))], [], []
t = 0.25
for li, (spk, mode, text) in enumerate(LINES):
    start = t
    for ph in [p for p in re.split(r"(?<=[.?!])\s+", text) if p.strip()]:
        speed = 1.1 if len(ph.split()) <= 4 else 1.18
        s, _ = kok.create(tts_text(ph), voice=VOICE[spk], speed=speed, lang="en-us")
        s = trim(np.asarray(s, np.float32)); dur = len(s) / SR
        toks = ph.split(); wts = [len(clean(w)) + 2 + (6 if w.endswith("...") else 4 if re.search(r"[.?!,]$", w) else 0) for w in toks]
        acc = t
        for w, wt in zip(toks, wts):
            d = dur * wt / sum(wts)
            words.append(dict(text=w.replace("*", "").replace("...", ""), key=w.startswith("*"), start=acc, end=acc + d,
                              c=clean(w), spk=spk, line=li, pause=w.endswith("..."))); acc += d
        turns.append((spk, t, t + dur, s)); voice.append(s); t += dur
        g = 0.3 if ph.rstrip().endswith("?") else 0.13; voice.append(np.zeros(int(SR * g))); t += g
    g = 0.18; voice.append(np.zeros(int(SR * g))); t += g
    LINES[li] = (spk, mode, text, start, t)
TOTAL = t + 1.6
voice = np.concatenate(voice); NF = int(TOTAL * FPS); print("duration", round(TOTAL, 2))

def W_(li, prefix, nth=1):
    k = 0
    for w in words:
        if w["line"] == li and w["c"].startswith(prefix):
            k += 1
            if k == nth: return w["start"]
    raise SystemExit(f"no word {prefix!r} in line {li}")
def LS(li): return LINES[li][3]
def LE(li): return LINES[li][4]

mouth = {"rio": np.zeros(NF), "mina": np.zeros(NF)}
hop = SR // FPS
for spk, a, b, s in turns:
    for k in range(int((b - a) * FPS)):
        seg = s[k * hop:(k + 1) * hop]
        if len(seg) and int(a * FPS) + k < NF: mouth[spk][int(a * FPS) + k] = min(1, np.sqrt(np.mean(seg ** 2)) * 9)
for m in mouth.values(): m[:] = np.convolve(m, [0.25, 0.5, 0.25], "same")
def speaking(spk, t): return any(s == spk and a <= t < b for s, a, b, _ in turns)
def mode_at(t):
    for li, L in enumerate(LINES):
        if t < L[4]: return L[1]
    return "C"

# ------------------------------------------------------------------ audio
n = int(TOTAL * SR); tt = np.arange(n) / SR
chords = [[110, 164.81, 196], [87.31, 130.81, 174.61], [98, 146.83, 196], [82.41, 123.47, 164.81]]
pad = np.zeros(n)
for k in range(int(TOTAL / 4) + 1):
    a = k * 4; m = (tt >= a) & (tt < a + 4.6); x = tt[m] - a
    env = np.clip(np.minimum(x / 0.6, (4.6 - x) / 0.6), 0, 1)
    for f in chords[k % 4]: pad[m] += env * (np.sin(2 * np.pi * f * tt[m]) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt[m]))
pulse = np.zeros(n); beat = 60 / 100; L = int(0.25 * SR)
for k in range(int(TOTAL / beat)):
    i = int(k * beat * SR); seg = np.sin(2 * np.pi * 55 * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 14)
    pulse[i:i + L] += seg[:max(0, min(L, n - i))]
sfx = np.zeros(n)
def add(sig, at):
    i = int(at * SR); L_ = min(len(sig), n - i)
    if L_ > 0 and i >= 0: sfx[i:i + L_] += sig[:L_]
x = np.arange(int(1.3 * SR)) / SR
BOOM = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-x * 2.5) + 35) / SR) * np.exp(-x * 3) * 0.6
x2 = np.arange(int(0.12 * SR)) / SR; BLIP = np.sin(2 * np.pi * 880 * x2) * np.exp(-x2 * 30) * 0.12
x3 = np.arange(int(0.4 * SR)) / SR
WHOOSH = np.convolve(np.random.default_rng(2).standard_normal(len(x3)), np.ones(40) / 40, "same") * np.sin(np.pi * x3 / x3[-1]) * 0.3
BOOMS = [W_(1, "4091"), W_(5, "twist"), W_(11, "partitioning")]
for b in BOOMS: add(BOOM, b)
prev = "C"
for li, L_ in enumerate(LINES):
    if L_[1] != prev: add(WHOOSH, L_[3] - 0.2)
    prev = L_[1]
music = pad / np.max(np.abs(pad)) * 0.07 + pulse * 0.06
fade = np.clip(np.minimum(tt / 0.8, (TOTAL - tt) / 1.4), 0, 1)
BLIPS = []
mix_extra = []

# ------------------------------------------------------------------ backdrop + characters (shared with test scene)
def backdrop():
    px = np.zeros((H, W, 3), np.float32); top, bot = np.array([16, 14, 48]), np.array([88, 52, 120])
    for y in range(H): px[y] = top + (bot - top) * min(1, y / 1250)
    im = Image.fromarray(px.astype(np.uint8)); d = ImageDraw.Draw(im); r = random.Random(7)
    for _ in range(140): x_, y_ = r.randrange(W), r.randrange(0, 700); d.ellipse((x_, y_, x_ + 3, y_ + 3), fill=(230, 230, 255))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((760, 170, 940, 350), fill=(255, 244, 200, 255))
    g = g.filter(ImageFilter.GaussianBlur(40)); im.paste(g, (0, 0), g); d.ellipse((770, 180, 930, 340), fill=(255, 246, 215))
    for layer, (col, lo, hi, win) in enumerate([((44, 36, 92), 520, 820, (120, 100, 160)), ((30, 26, 64), 640, 980, (255, 196, 110))]):
        x_ = -20
        while x_ < W:
            bw = r.randrange(90, 190); ty = r.randrange(lo, hi - 120); glass = layer == 1 and r.random() < 0.25
            d.rectangle((x_, ty, x_ + bw, 1330), fill=(26, 58, 92) if glass else col, outline=INK, width=4)
            if glass:
                for gx in range(x_ + 14, x_ + bw - 6, 22): d.line([(gx, ty + 10), (gx, 1330)], fill=(60, 110, 150), width=3)
            else:
                for wy in range(ty + 24, 1300, 46):
                    for wx in range(x_ + 16, x_ + bw - 24, 34):
                        if r.random() < 0.55: d.rectangle((wx, wy, wx + 16, wy + 22), fill=win)
            if r.random() < 0.3: d.line([(x_ + bw // 2, ty), (x_ + bw // 2, ty - 60)], fill=INK, width=5)
            x_ += bw + r.randrange(-10, 14)
    d.polygon([(0, 1420), (W, 1420), (W, H), (0, H)], fill=(52, 54, 72))
    for y in range(1450, H, 60): d.line([(0, y), (W, y)], fill=(60, 62, 82), width=2)
    d.rectangle((0, 1250, W, 1420), fill=(140, 70, 60), outline=INK, width=5)
    for row, y in enumerate(range(1262, 1410, 34)):
        d.line([(0, y + 30), (W, y + 30)], fill=(110, 52, 48), width=3)
        for bx in range(-40 + (row % 2) * 45, W, 90): d.line([(bx, y), (bx, y + 30)], fill=(110, 52, 48), width=3)
    d.rectangle((0, 1238, W, 1262), fill=(170, 160, 160), outline=INK, width=4)
    for px_, s in ((70, 1.0), (1010, 1.1), (560, 0.7)):
        d.polygon([(px_ - 40 * s, 1250), (px_ + 40 * s, 1250), (px_ + 30 * s, 1180), (px_ - 30 * s, 1180)], fill=(150, 90, 60), outline=INK)
        for a in range(-60, 61, 30):
            ex = px_ + math.sin(math.radians(a)) * 90 * s; ey = 1180 - math.cos(math.radians(a)) * 110 * s
            d.ellipse((ex - 26 * s, ey - 14 * s, ex + 26 * s, ey + 14 * s), fill=(60, 140, 80), outline=INK, width=3)
    lights = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lights)
    pts = [(x_, 1205 + 40 * math.sin(math.pi * (x_ % 360) / 360)) for x_ in range(0, W + 1, 8)]
    d.line(pts, fill=INK, width=3)
    for x_, y_ in pts[::5]: ld.ellipse((x_ - 9, y_ - 4, x_ + 9, y_ + 14), fill=(255, 220, 140, 255))
    gl = lights.filter(ImageFilter.GaussianBlur(10)); im.paste(gl, (0, 0), gl); im.paste(lights, (0, 0), lights)
    return im.convert("RGBA")
BG = backdrop()
BG_DIM = Image.alpha_composite(BG, Image.new("RGBA", (W, H), (6, 8, 24, 150)))

STYLE = {
 "rio":  dict(x=300, face=1,  skin=(196, 140, 100), hair=(30, 24, 30), top=(255, 190, 40), pants=(56, 90, 150), hairstyle="spiky"),
 "mina": dict(x=790, face=-1, skin=(222, 172, 140), hair=(70, 50, 50), top=(40, 160, 150), pants=(150, 150, 160), hairstyle="bun"),
}
FEET = 1640
SURPRISE = [(LS(1), LE(1)), (LS(6), LE(6) + 0.3), (W_(10, "124") - 0.2, LE(10) + 0.5)]   # Rio's surprised face
SHRUG = [(LS(3), LE(3) + 0.3)]

def draw_char(d, name, t, fi):
    st = STYLE[name]; S = SS; f = st["face"]; x0 = st["x"]
    talk = speaking(name, t); m = mouth[name][min(fi, NF - 1)]
    fy = FEET + math.sin(t * 2.2 + x0) * 4
    def P(x, y): return (x * S, y * S)
    def circ(c, r): return (c[0] * S - r * S, c[1] * S - r * S, c[0] * S + r * S, c[1] * S + r * S)
    def line(a, b, w, col):
        d.line([P(*a), P(*b)], fill=INK, width=int((w + 10) * S)); d.ellipse(circ(b, (w + 10) / 2), fill=INK)
        d.line([P(*a), P(*b)], fill=col, width=int(w * S)); d.ellipse(circ(b, w / 2), fill=col)
    def ell(c, rx, ry, col, ow=5): d.ellipse(P(c[0] - rx, c[1] - ry) + P(c[0] + rx, c[1] + ry), fill=col, outline=INK, width=int(ow * S))
    surprise = name == "rio" and any(a <= t < b for a, b in SURPRISE)
    shrug = name == "rio" and any(a <= t < b for a, b in SHRUG)
    for dx in (-30, 30):
        d.rounded_rectangle(P(x0 + dx - 22, fy - 250) + P(x0 + dx + 22, fy - 20), 14 * S, fill=st["pants"], outline=INK, width=5 * S)
        ell((x0 + dx + 10 * f, fy - 14), 36, 18, (240, 240, 240))
    sh_y = fy - 440
    g = 0.55 + 0.35 * math.sin(t * 5.0) if talk else 0.0
    if shrug:
        line((x0 - 70 * f, sh_y), (x0 - 170 * f, fy - 470), 34, st["top"]); ell((x0 - 170 * f, fy - 470), 20, 20, st["skin"], 4)
    else:
        line((x0 - 70 * f, sh_y), (x0 - 95 * f, fy - 255), 34, st["top"])
    d.rounded_rectangle(P(x0 - 92, fy - 460) + P(x0 + 92, fy - 230), 46 * S, fill=st["top"], outline=INK, width=5 * S)
    d.arc(P(x0 - 45, fy - 330) + P(x0 + 45, fy - 270), 0, 180, fill=INK, width=4 * S)
    if shrug: hx, hy = x0 + 170 * f, fy - 470
    else: hx, hy = x0 + f * (95 + 70 * g), fy - 255 - 220 * g
    line((x0 + 70 * f, sh_y), (hx, hy), 34, st["top"]); ell((hx, hy), 20, 20, st["skin"], 4)
    lean = 14 * f if talk else (-10 * f if surprise else 0)
    cx = x0 + lean; cy = fy - 575 + (math.sin(t * 9) * 4 if talk else 0)
    if st["hairstyle"] == "bun": ell((cx - 8 * f, cy - 120), 44, 40, st["hair"])
    ell((cx - 96 * f, cy + 10), 18, 24, st["skin"]); ell((cx, cy), 112, 118, st["skin"], 6)
    if st["hairstyle"] == "spiky":
        pts = [P(cx - 118, cy - 10)]
        for i in range(9):
            a = math.pi + i * math.pi / 8; r_ = 150 if i % 2 else 112
            pts.append(P(cx + r_ * math.cos(a), cy - 25 + r_ * math.sin(a)))
        pts += [P(cx + 118, cy - 10), P(cx + 60, cy - 60), P(cx - 60, cy - 60)]
        d.polygon(pts, fill=st["hair"], outline=INK, width=5 * S)
    else:
        d.chord(P(cx - 116, cy - 122) + P(cx + 116, cy + 60), 180, 360, fill=st["hair"], outline=INK, width=5 * S)
        d.polygon([P(cx + 100 * f, cy - 40), P(cx + 118 * f, cy + 70), P(cx + 84 * f, cy + 40)], fill=st["hair"], outline=INK)
    blink = (t + x0 / 300) % 3.7 < 0.12
    other = STYLE["mina" if name == "rio" else "rio"]["x"]
    look = 7 * (1 if other > x0 else -1)
    if mode_at(t) == "D": look = 0; up = -6
    else: up = 0
    for ex in (-40, 40):
        e = (cx + ex + 10 * f, cy + 6)
        if blink: d.line([P(e[0] - 16, e[1]), P(e[0] + 16, e[1])], fill=INK, width=5 * S)
        else:
            ell(e, 18, 27 if surprise else 22, WHITE, 4); ell((e[0] + look, e[1] + 2 + up), 9, 10, INK, 0)
        by = e[1] - (46 if surprise else 34) - (4 if talk and math.sin(t * 3) > 0.6 else 0)
        d.line([P(e[0] - 18, by + (0 if ex * f > 0 else 4)), P(e[0] + 18, by + (4 if ex * f > 0 else 0))], fill=INK, width=6 * S)
    mc = (cx + 18 * f, cy + 62)
    if m > 0.12:
        oh = 6 + 30 * m
        d.ellipse(P(mc[0] - 24, mc[1] - oh / 2) + P(mc[0] + 24, mc[1] + oh / 2), fill=(120, 30, 40), outline=INK, width=4 * S)
        if oh > 16: d.chord(P(mc[0] - 14, mc[1]) + P(mc[0] + 14, mc[1] + oh / 2), 180, 360, fill=(230, 100, 110))
    elif surprise: ell(mc, 13, 16, (120, 30, 40), 4)
    else: d.arc(P(mc[0] - 22, mc[1] - 16) + P(mc[0] + 22, mc[1] + 10), 20, 160, fill=INK, width=5 * S)

def chars_layer(t, fi, scale, feet_y):
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for name in ("rio", "mina"): draw_char(d, name, t, fi)
    bb = lay.getbbox(); crop = lay.crop(bb)
    k = scale / SS
    small = crop.resize((max(1, int(crop.width * k)), max(1, int(crop.height * k))), Image.LANCZOS)
    px = 540 + (bb[0] / SS - 540) * scale; py = feet_y + (bb[1] / SS - FEET) * scale
    return small, (int(px), int(py))

# ------------------------------------------------------------------ overlay helpers
def ctext(d, xy, s, f, fill):
    syms = "✔✘→↓⏱"
    if not any(c in syms for c in s): d.text(xy, s, font=f, fill=fill, anchor="mm"); return
    fb = ImageFont.truetype(DJ, f.size); parts = [(c, fb if c in syms else f) for c in s]
    x_ = xy[0] - sum(d.textlength(c, font=q) for c, q in parts) / 2
    for c, q in parts: d.text((x_, xy[1]), c, font=q, fill=fill, anchor="lm"); x_ += d.textlength(c, font=q)
def glow(fn):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); bb = lay.getbbox(); p = 40
    bb = (max(bb[0] - p, 0), max(bb[1] - p, 0), min(bb[2] + p, W), min(bb[3] + p, H)); c = lay.crop(bb)
    g = np.array(c.filter(ImageFilter.GaussianBlur(14))); g[..., 3] = (g[..., 3] * 0.85).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(g), c), bb[:2]
def box(d, xy, col=YEL, fill=PANEL + (240,), w=6, r=24): d.rounded_rectangle(xy, r, fill=fill, outline=col, width=w)
def arrow(d, a, b, col=YEL, w=8):
    d.line([a, b], fill=col, width=w); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6): d.line([b, (b[0] + 30 * math.cos(ang + s), b[1] + 30 * math.sin(ang + s))], fill=col, width=w)
def keyicon(d, x, y, col, s=1.0):
    d.ellipse((x - 11 * s, y - 11 * s, x + 11 * s, y + 11 * s), outline=col, width=max(2, int(5 * s)))
    d.line([(x + 11 * s, y), (x + 44 * s, y)], fill=col, width=max(2, int(6 * s))); d.line([(x + 36 * s, y), (x + 36 * s, y + 10 * s)], fill=col, width=max(2, int(6 * s)))
def packet(d, cx, cy, col=YEL, label="packet"):
    box(d, (cx - 130, cy - 70, cx + 130, cy + 70), col); ctext(d, (cx, cy - 12), label, LBL_S, col)
    d.rectangle((cx - 22, cy + 24, cx + 22, cy + 56), fill=col); d.arc((cx - 16, cy + 4, cx + 16, cy + 36), 180, 360, fill=col, width=6)
def server(d, cx, cy, col=DIM, port=None):
    box(d, (cx - 150, cy - 130, cx + 150, cy + 130), col)
    for k in range(3): d.rounded_rectangle((cx - 110, cy - 95 + k * 62, cx + 110, cy - 55 + k * 62), 8, outline=col, width=4)
    for k in range(3): d.ellipse((cx + 80, cy - 84 + k * 62, cx + 96, cy - 68 + k * 62), fill=GREEN if port else col)
    ctext(d, (cx, cy + 160), "SERVER", LBL_S, col)
def keygrid(d, x0, y0, cols, rows, col, step=70, s=0.75, cross=False, dimmed=None):
    for r_ in range(rows):
        for c_ in range(cols):
            x_, y_ = x0 + c_ * step, y0 + r_ * 46
            cc = col if not dimmed or not dimmed(c_, r_) else (70, 76, 100)
            keyicon(d, x_, y_, cc, s)
            if cross: d.line([(x_ - 12, y_ - 14), (x_ + 40, y_ + 14)], fill=RED, width=5)

# screen region for diagram mode
SX0, SY0, SX1, SY1 = 40, 150, 1040, 1180
def screen_bg():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((SX0, SY0, SX1, SY1), 36, fill=NAVY + (245,), outline=(70, 90, 140), width=6)
    for x_ in range(SX0 + 30, SX1, 50): d.line([(x_, SY0 + 6), (x_, SY1 - 6)], fill=GRID + (255,))
    for y_ in range(SY0 + 30, SY1, 50): d.line([(SX0 + 6, y_), (SX1 - 6, y_)], fill=GRID + (255,))
    g = im.filter(ImageFilter.GaussianBlur(20)); out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(g); out.alpha_composite(im); return out
SCREEN = screen_bg()

# ------------------------------------------------------------------ overlay timeline: (start, end, draw_fn)
EL = []
def at(start, end, fn, blip=True):
    EL.append((start, end, glow(fn)))
    if blip: BLIPS.append(start)
def sign(text, col=YEL, sub=None, y=330):
    def fn(d):
        w_ = max(d.textlength(text, font=LBL), d.textlength(sub or "", font=LBL_S)) + 100
        box(d, (540 - w_ / 2, y - 70, 540 + w_ / 2, y + (90 if sub else 70)), col)
        ctext(d, (540, y - (12 if sub else 0)), text, LBL, col)
        if sub: ctext(d, (540, y + 50), sub, LBL_S, DIM)
    return fn

def door(d, cx, cy, open_, col):
    box(d, (cx - 80, cy - 120, cx + 80, cy + 120), col, fill=(30, 24, 20, 255) if open_ else PANEL + (240,))
    if open_:
        d.polygon([(cx - 80, cy - 120), (cx - 10, cy - 95), (cx - 10, cy + 135), (cx - 80, cy + 120)], fill=(120, 90, 60), outline=INK)
        d.polygon([(cx - 10, cy - 95), (cx + 80, cy - 120), (cx + 80, cy + 120), (cx - 10, cy + 135)], fill=(255, 230, 150, 180))
    else:
        d.ellipse((cx + 40, cy - 8, cx + 56, cy + 8), fill=col)
def grid_state(state):
    def fn(d):
        col = {"all": YEL, "shut": RED, "open": GREEN, "half": YEL, "quarter": YEL}[state]
        box(d, (80, 600, 1000, 960), col)
        dim = {"half": (lambda c, r: c >= 6), "quarter": (lambda c, r: c >= 3)}.get(state)
        keygrid(d, 130, 650, 12, 5, col, cross=state == "shut", dimmed=dim)
        if state in ("half", "quarter"): x_ = 540 if state == "half" else 330; d.line([(x_, 620), (x_, 880)], fill=WHITE, width=6)
        ctext(d, (540, 920), {"all": "4,091 passwords · 1 message", "shut": "all 4,091 wrong", "open": "password is in here",
                              "half": "split in half", "quarter": "...and again"}[state], LBL, col)
    return fn
# 0-1 (C)
at(LS(0), LE(0), sign("guess #1  ✘   #2  ✘   #3  ✘", RED))
at(W_(1, "4091"), LE(1), lambda d: (ctext(d, (540, 330), "4,091", BIGN, YEL), ctext(d, (540, 450), "passwords per try?!", LBL, WHITE)))
# 2 (D) silent server
at(LS(2), LE(2), lambda d: (server(d, 760, 420), ctext(d, (540, 230), "a password-protected server", LBL_S, DIM)))
at(W_(2, "wrong"), LE(2), lambda d: (box(d, (70, 360, 430, 480), RED), ctext(d, (250, 420), "wrong password", LBL_S, RED), arrow(d, (440, 420), (590, 420), RED)))
at(W_(2, "nothing"), LE(2), lambda d: (ctext(d, (540, 800), "NO ERROR.", TITLE, WHITE), ctext(d, (540, 910), "JUST SILENCE.", TITLE, DIM)))
# 3 (C)
at(LS(3), LE(3), sign("am I even close?", DIM), blip=False)
# 4 (D) the door = the leak
at(LS(4), LE(4), lambda d: (box(d, (70, 360, 430, 480), GREEN), ctext(d, (250, 420), "right password", LBL_S, GREEN),
                            arrow(d, (440, 420), (590, 420), GREEN), server(d, 760, 420, GREEN, True)))
at(W_(4, "door"), LE(4), lambda d: (door(d, 300, 820, True, GREEN), ctext(d, (650, 780), "a door opens", LBL, GREEN),
                                    ctext(d, (650, 850), "(a network port)", LBL_S, DIM)))
at(W_(4, "see"), LE(4), lambda d: ctext(d, (650, 930), "visible from outside", LBL_S, YEL))
at(W_(4, "leak"), LE(4), lambda d: (box(d, (150, 1000, 930, 1120)), ctext(d, (540, 1060), "LEAK = a yes / no answer", LBL, YEL)))
# 5-6 (C) twist
at(W_(5, "thousands"), LE(5), sign("1 message, unlocks with 1000s of passwords", YEL, "possible with AES-GCM"))
at(LS(6), LE(6), sign("one message?!", WHITE), blip=False)
# 7 (D) split
at(LS(7), W_(7, "shut"), grid_state("all"))
at(W_(7, "shut"), W_(7, "opens"), lambda d: (door(d, 540, 400, False, RED), ctext(d, (540, 560), "door stays shut", LBL, RED)))
at(W_(7, "all"), W_(7, "opens"), grid_state("shut"))
at(W_(7, "opens"), LE(7), lambda d: (door(d, 540, 400, True, GREEN), ctext(d, (540, 560), "door opens", LBL, GREEN)))
at(W_(7, "opens"), W_(7, "split"), grid_state("open"))
at(W_(7, "split"), W_(7, "again"), grid_state("half"))
at(W_(7, "again"), LE(7), grid_state("quarter"))
# 8 (D) twenty questions
def halving(d):
    ctext(d, (540, 260), "TWENTY QUESTIONS", TITLE, YEL)
    for i, (n_, w_) in enumerate([("4,091", 880), ("2,046", 440), ("1,023", 220), ("512", 110), ("...", 0), ("1", 14)]):
        y_ = 380 + i * 110
        if w_: d.rounded_rectangle((100, y_, 100 + w_, y_ + 60), 10, fill=YEL if n_ != "1" else GREEN)
        ctext(d, (100 + max(w_, 0) + 110 if w_ < 700 else 540, y_ + 30), n_ if n_ != "1" else "1 → the password", LBL_S, WHITE if w_ >= 700 else (GREEN if n_ == "1" else WHITE))
at(LS(8), LE(8), halving)
# 9 (C)
at(LS(9), LE(9), sign("does it actually work?", WHITE), blip=False)
# 10 (D) stats
at(LS(10), LE(10), lambda d: (ctext(d, (540, 260), "simulated with real leaked passwords", LBL_S, DIM),
                              ctext(d, (540, 340), "1 in 5 passwords cracked", LBL, WHITE)))
at(W_(10, "124"), LE(10), lambda d: (ctext(d, (150, 520), "this trick", LBL_S, YEL), d.rounded_rectangle((280, 490, 310, 550), 6, fill=YEL),
                                     ctext(d, (480, 520), "124 tries", LBL, YEL)))
at(W_(10, "60000"), LE(10), lambda d: (ctext(d, (150, 700), "guessing", LBL_S, RED), d.rounded_rectangle((280, 670, 1000, 730), 6, fill=RED),
                                       ctext(d, (640, 800), "~60,000 tries", LBL, RED)))
# 11 (C) name + real world
at(W_(11, "partitioning"), LE(11), lambda d: (d.rounded_rectangle((80, 250, 1000, 520), 24, fill=(200, 40, 50, 255), outline=INK, width=8),
                                              ctext(d, (540, 340), "PARTITIONING", font(XB, 100), WHITE), ctext(d, (540, 445), "ORACLE ATTACK", font(XB, 86), YEL)))
at(W_(11, "shadowsocks"), LE(11), lambda d: (box(d, (160, 580, 920, 690), GREEN), ctext(d, (540, 635), "found in Shadowsocks · fixed ✔", LBL_S, GREEN)))
# 12 (C) end
at(LS(12), TOTAL + 1, lambda d: (ctext(d, (540, 330), "FOLLOW", font(XB, 130), YEL), ctext(d, (540, 450), "◆ 0xLore", ImageFont.truetype(MONOF, 64), WHITE)))

for b in BLIPS: add(BLIP, b)
mix = (music + sfx) * fade; mix[:len(voice)] += voice
mix /= max(1, np.max(np.abs(mix)) / 0.97); WAV = os.path.join(WORK, "po.wav"); sf.write(WAV, mix, SR)

def wm():
    f = ImageFont.truetype(MONOF, 40); im = Image.new("RGBA", (260, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(14, 30), (30, 14), (46, 30), (30, 46)], fill=YEL + (170,)); d.text((62, 30), "0xLore", font=f, fill=WHITE + (170,), anchor="lm"); return im
WM = wm()
chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    if len(cur) == 3 or w["pause"] or re.search(r"[.?!,]$", w["text"]) or i == len(words) - 1 or words[i + 1]["line"] != w["line"]:
        chunks.append(cur); cur = []
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def dmix(t):
    """0 = cartoon mode, 1 = diagram mode, eased around line boundaries."""
    v = 0.0
    for li, L_ in enumerate(LINES):
        if L_[1] == "D":
            a, b = L_[3], L_[4]
            nxt_d = li + 1 < len(LINES) and LINES[li + 1][1] == "D"
            prv_d = li > 0 and LINES[li - 1][1] == "D"
            if (a - 0.3 if not prv_d else a) <= t < (b if nxt_d else b + 0.3):
                v = max(v, min(1 if prv_d else ease((t - a + 0.3) / 0.35), 1 if nxt_d else ease((b + 0.3 - t) / 0.35)))
    return v

def render(fi):
    t = fi / FPS; k = dmix(t)
    im = BG.copy() if k < 0.01 else Image.blend(BG, BG_DIM, k)
    scale = 1 - 0.32 * k; feet = FEET + 70 * k
    ch, pos = chars_layer(t, fi, scale, feet); im.alpha_composite(ch, pos)
    if k > 0.01:
        sc = SCREEN if k >= 1 else Image.fromarray((np.array(SCREEN) * np.array([1, 1, 1, k])).astype(np.uint8))
        im.alpha_composite(sc)
    for a, b, (lay, p) in EL:
        if a <= t < b:
            e = ease((t - a) / 0.3); l2 = lay
            if e < 1:
                s_ = 0.85 + 0.15 * e; l2 = lay.resize((max(1, int(lay.width * s_)), max(1, int(lay.height * s_))))
                al = np.array(l2); al[..., 3] = (al[..., 3] * e).astype(np.uint8); l2 = Image.fromarray(al)
            im.alpha_composite(l2, (p[0] + (lay.width - l2.width) // 2, p[1] + (lay.height - l2.height) // 2))
    # camera drift in cartoon mode
    spk = next((s for s, a, b, _ in turns if a - 0.2 <= t < b + 0.3), None)
    z = 1 + (0.06 if spk else 0.02) * (1 - k)
    tx = STYLE[spk]["x"] if spk else 540
    cx = 540 + (tx - 540) * 0.35 * (1 - k)
    cw, chh = int(W / z), int(H / z); x0 = int(min(max(cx - cw / 2, 0), W - cw)); y0 = int((H - chh) * 0.55)
    if z > 1.001: im = im.crop((x0, y0, x0 + cw, y0 + chh)).resize((W, H), Image.BILINEAR)
    for bt in BOOMS:
        if 0 <= t - bt < 0.3:
            amp = 12 * (1 - (t - bt) / 0.3); im = Image.fromarray(np.roll(np.array(im), int(amp * math.sin(t * 80)), 1))
    im.alpha_composite(WM, (W - WM.width - 30, 40))
    d = ImageDraw.Draw(im); d.rectangle((0, 0, int(W * t / TOTAL), 10), fill=YEL)
    c = next((c for c in chunks if c[0]["start"] - 0.05 <= t < c[-1]["end"] + 0.2), None)
    if c:
        texts = [w["text"] if "0xLore" in w["text"] else w["text"].upper() for w in c]; widths = [d.textlength(s + " ", font=CAP) for s in texts]
        x_ = (W - sum(widths)) / 2; y_ = 1785
        for w, s, wd in zip(c, texts, widths):
            if t >= w["start"] - 0.05:
                pop = ease((t - w["start"] + 0.05) / 0.12)
                d.text((x_, y_ + int(10 * (1 - pop))), s, font=CAP, fill=YEL if w["key"] else WHITE, stroke_width=8, stroke_fill=INK)
            x_ += wd
    return im.convert("RGB").tobytes()

def make_cover(path):
    im = BG.copy(); d0 = ImageDraw.Draw(im)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle((0, 0, W, 680), fill=(8, 10, 30, 215))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(30)))
    # Rio, big and shocked
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tsur = (SURPRISE[1][0] + SURPRISE[1][1]) / 2
    old = dict(STYLE["rio"]); STYLE["rio"]["x"] = 540; draw_char(d, "rio", tsur, int(tsur * FPS)); STYLE["rio"].update(old)
    bb = lay.getbbox(); cr = lay.crop(bb); sc = 1.25
    cr = cr.resize((int(cr.width * sc / SS), int(cr.height * sc / SS)), Image.LANCZOS)
    im.alpha_composite(cr, (540 - cr.width // 2 + 40, H - cr.height + 60))
    def fn(d):
        ctext(d, (540, 230), "4,091", font(XB, 220), YEL)
        ctext(d, (540, 390), "PASSWORDS.", font(XB, 120), WHITE)
        d.rounded_rectangle((150, 470, 930, 610), 22, fill=(200, 40, 50, 255), outline=INK, width=8)
        ctext(d, (540, 540), "ONE TRY.", font(XB, 100), WHITE)
        ctext(d, (540, 1830), "◆ 0xLore", ImageFont.truetype(MONOF, 60), WHITE)
    g, p = glow(fn); im.alpha_composite(g, p)
    im.convert("RGB").save(path, quality=92)

if __name__ == "__main__":
    if COVER: make_cover(COVER)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for buf in p.imap(render, range(NF), chunksize=8): ff.stdin.write(buf)
    ff.stdin.close(); ff.wait(); print("done", OUT, NF)
