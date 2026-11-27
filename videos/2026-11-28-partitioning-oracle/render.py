"""Partitioning Oracle Attacks, v3: hybrid cartoon + diagram Short for 0xLore.

Usage: python3 render_v3.py <dir with kokoro model files> <output.mp4> <cover.jpg>

Format: 1080x1920 (9:16), 30 fps, H.264 yuv420p, AAC 48 kHz, loudness -14 LUFS.
Safe zone for Shorts/Reels UI: all text and diagrams stay inside
x 40-1040, y 250-1540. Captions sit at y ~1400-1520. The watermark is at top
centre, outside the corner icons.

Built-in QA (the render aborts on failure): text out of the safe zone,
overlay gaps or flicker, empty diagram screens, hook later than 1.5 s,
end tail over 1.8 s. Loudness is normalised and verified after encoding.

Mechanism summary (all scenes must match it), from Len, Grubbs, Ristenpart,
"Partitioning Oracle Attacks", USENIX Security 2021, §4 (Shadowsocks):
the server silently drops packets it can't decrypt, but opens a UDP port when
decryption works, and the attacker can detect that port. AES-GCM is not
key-committing, so one packet can be built that decrypts under 4,091
password-derived keys (limited by UDP size; 32 s to compute). Port closed →
all 4,091 crossed off. Port open → the password is in that batch, and the
attacker finds it by offline trial decryption of the reply. In simulations with
breach data: 20% of passwords recovered with 124 packets vs ~60,000 for plain
remote guessing.
"""
import sys, os, re, math, random, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import soundfile as sf
import pyloudnorm as pyln
from multiprocessing import Pool

WORK, OUT, COVER = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS, SR, SS = 1080, 1920, 30, 24000, 2
SAFE = (40, 250, 1040, 1540)          # x0, y0, x1, y1 for text/diagrams
CAP_Y, CAP_MAXW = 1405, 960
INK = (22, 20, 38); YEL = (255, 210, 40); WHITE = (245, 247, 252); RED = (255, 90, 90)
GREEN = (90, 225, 130); DIM = (160, 172, 205); PANEL = (14, 24, 52); NAVY = (8, 15, 36); GRID = (22, 36, 70)
F = "/usr/share/fonts/opentype/inter/"; DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONOF = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
def font(n, s): return ImageFont.truetype(F + n, s)
XB = "Inter-ExtraBold.otf" if os.path.exists(F + "Inter-ExtraBold.otf") else "Inter-Bold.otf"
LBL = font("Inter-Bold.otf", 60); LBL_S = font("Inter-SemiBold.otf", 46); TITLE = font(XB, 92); BIGN = font(XB, 170)
QA = []   # list of failure strings

# ------------------------------------------------------------------ script
LINES = [
 ("mina", "C", "*4,091* passwords... in one try. Want to see how?"),
 ("rio", "C", "Online? No way. That's one guess per try."),
 ("mina", "D", "Picture a proxy server, kind of like a VPN. You and the server share a *password*, and it becomes the *secret* *key* that encrypts your traffic. Send a packet locked with the wrong password... and it says *nothing*. No error. Just silence."),
 ("rio", "C", "So I can't even tell if I'm close."),
 ("mina", "D", "But send the *right* one, and the server quietly opens a *door* to wait for a reply. You can see that door from outside. That's a *leak*. A simple yes or no."),
 ("mina", "C", "Now the twist. Some encryption, like AES-GCM, lets you build one message that unlocks with *thousands* of passwords."),
 ("rio", "C", "Wait. One message... thousands of passwords?"),
 ("mina", "D", "*4,091* of them. Door stays *shut*? All 4,091 are wrong. Crossed off in one go. Door *opens*? The password is in that batch, and the attacker finds it *offline*."),
 ("mina", "D", "And it works because people pick *guessable* passwords. The attacker tests the *most* *common* ones first."),
 ("rio", "C", "Does that actually work?"),
 ("mina", "D", "In simulations with real leaked passwords, one in five was cracked in just *124* tries. Normal guessing? Around *60,000*."),
 ("mina", "C", "It's called a *partitioning* *oracle* attack. Researchers found it in a real proxy tool, Shadowsocks, and helped fix it."),
 ("rio", "C", "Follow *0xLore* for more hidden gems."),
]
VOICE = {"rio": "am_michael", "mina": "af_heart"}
SAY = {"4,091": "four thousand ninety-one", "124": "a hundred and twenty-four", "60,000": "sixty thousand",
       "AES-GCM": "A-E-S G-C-M", "0xLore": "oh-ex Lore", "Shadowsocks": "Shadow-socks"}
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

voice, words, turns = [np.zeros(int(SR * 0.15))], [], []
t = 0.15
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
VOICE_END = turns[-1][2]
TOTAL = VOICE_END + 1.4
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
def line_at(t):
    for li, L in enumerate(LINES):
        if t < L[4]: return li
    return len(LINES) - 1

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
BOOMS = [W_(0, "4091"), W_(5, "twist"), W_(11, "partitioning")]
for b in BOOMS: add(BOOM, b)
prev = "C"
for L_ in LINES:
    if L_[1] != prev: add(WHOOSH, L_[3] - 0.2)
    prev = L_[1]
BLIPS = []

# ------------------------------------------------------------------ backdrop
def backdrop():
    px = np.zeros((H, W, 3), np.float32); top, bot = np.array([16, 14, 48]), np.array([88, 52, 120])
    for y in range(H): px[y] = top + (bot - top) * min(1, y / 1250)
    im = Image.fromarray(px.astype(np.uint8)); d = ImageDraw.Draw(im); r = random.Random(7)
    for _ in range(140): x_, y_ = r.randrange(W), r.randrange(0, 700); d.ellipse((x_, y_, x_ + 3, y_ + 3), fill=(230, 230, 255))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((70, 40, 230, 200), fill=(255, 244, 200, 255))
    g = g.filter(ImageFilter.GaussianBlur(40)); im.paste(g, (0, 0), g); d.ellipse((80, 50, 220, 190), fill=(255, 246, 215))
    for layer, (col, lo, hi, win) in enumerate([((44, 36, 92), 560, 840, (120, 100, 160)), ((30, 26, 64), 680, 1000, (255, 196, 110))]):
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

# ------------------------------------------------------------------ characters
STYLE = {
 "rio":  dict(x=300, face=1,  skin=(196, 140, 100), hair=(30, 24, 30), top=(255, 190, 40), pants=(56, 90, 150), hairstyle="spiky"),
 "mina": dict(x=790, face=-1, skin=(222, 172, 140), hair=(70, 50, 50), top=(40, 160, 150), pants=(150, 150, 160), hairstyle="bun"),
}
FEET = 1640
SURPRISE = [(LS(1), LS(1) + 0.8), (LS(6), LE(6) + 0.3), (W_(10, "124") - 0.2, LE(10) + 0.5)]
SHRUG = [(LS(3), LE(3) + 0.3)]
SMIRK = [(LS(0), LE(0)), (LS(5), LE(5)), (LS(11), LE(11))]       # Mina's knowing look

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
    smirk = name == "mina" and any(a <= t < b for a, b in SMIRK)
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
    for ex in (-40, 40):
        e = (cx + ex + 10 * f, cy + 6)
        if blink: d.line([P(e[0] - 16, e[1]), P(e[0] + 16, e[1])], fill=INK, width=5 * S)
        else:
            ell(e, 18, 27 if surprise else 22, WHITE, 4); ell((e[0] + look, e[1] + 2), 9, 10, INK, 0)
        # friendly arched brows; surprise = high; smirk = one brow raised
        lift = 46 if surprise else 36
        if smirk and ex * f > 0: lift += 12
        if talk and math.sin(t * 3) > 0.6: lift += 4
        by = e[1] - lift
        d.arc(P(e[0] - 20, by - 8) + P(e[0] + 20, by + 14), 200, 340, fill=INK, width=6 * S)
    mc = (cx + 18 * f, cy + 62)
    if m > 0.12:
        oh = 6 + 30 * m
        d.ellipse(P(mc[0] - 24, mc[1] - oh / 2) + P(mc[0] + 24, mc[1] + oh / 2), fill=(120, 30, 40), outline=INK, width=4 * S)
        if oh > 16: d.chord(P(mc[0] - 14, mc[1]) + P(mc[0] + 14, mc[1] + oh / 2), 180, 360, fill=(230, 100, 110))
    elif surprise: ell(mc, 13, 16, (120, 30, 40), 4)
    elif smirk: d.arc(P(mc[0] - 22, mc[1] - 20) + P(mc[0] + 26, mc[1] + 6), 10, 120, fill=INK, width=5 * S)
    else: d.arc(P(mc[0] - 22, mc[1] - 16) + P(mc[0] + 22, mc[1] + 10), 20, 160, fill=INK, width=5 * S)

def chars_layer(t, fi, scale, feet_y):
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for name in ("rio", "mina"): draw_char(d, name, t, fi)
    bb = lay.getbbox(); crop = lay.crop(bb); k = scale / SS
    small = crop.resize((max(1, int(crop.width * k)), max(1, int(crop.height * k))), Image.LANCZOS)
    return small, (int(540 + (bb[0] / SS - 540) * scale), int(feet_y + (bb[1] / SS - FEET) * scale))

# ------------------------------------------------------------------ overlay helpers
SYMS = "✔✘→◆"
def ctext(d, xy, s, f, fill):
    if not any(c in SYMS for c in s): d.text(xy, s, font=f, fill=fill, anchor="mm"); return
    fb = ImageFont.truetype(DJ, f.size); parts = [(c, fb if c in SYMS else f) for c in s]
    x_ = xy[0] - sum(d.textlength(c, font=q) for c, q in parts) / 2
    for c, q in parts: d.text((x_, xy[1]), c, font=q, fill=fill, anchor="lm"); x_ += d.textlength(c, font=q)
def box(d, xy, col=YEL, fill=PANEL + (240,), w=6, r=24): d.rounded_rectangle(xy, r, fill=fill, outline=col, width=w)
def arrow(d, a, b, col=YEL, w=8):
    d.line([a, b], fill=col, width=w); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6): d.line([b, (b[0] + 30 * math.cos(ang + s), b[1] + 30 * math.sin(ang + s))], fill=col, width=w)
def keyicon(d, x, y, col, s=1.0):
    d.ellipse((x - 11 * s, y - 11 * s, x + 11 * s, y + 11 * s), outline=col, width=max(2, int(5 * s)))
    d.line([(x + 11 * s, y), (x + 44 * s, y)], fill=col, width=max(2, int(6 * s))); d.line([(x + 36 * s, y), (x + 36 * s, y + 10 * s)], fill=col, width=max(2, int(6 * s)))
def server(d, cx, cy, col=DIM, lit=False, s=1.0):
    box(d, (cx - 150 * s, cy - 130 * s, cx + 150 * s, cy + 130 * s), col)
    for k in range(3):
        d.rounded_rectangle((cx - 110 * s, cy + (-95 + k * 62) * s, cx + 110 * s, cy + (-55 + k * 62) * s), 8, outline=col, width=4)
        d.ellipse((cx + 80 * s, cy + (-84 + k * 62) * s, cx + 96 * s, cy + (-68 + k * 62) * s), fill=GREEN if lit else col)
def door(d, cx, cy, open_, col):
    box(d, (cx - 90, cy - 135, cx + 90, cy + 135), col, fill=(30, 24, 20, 255) if open_ else PANEL + (240,))
    if open_:
        d.polygon([(cx - 90, cy - 135), (cx - 10, cy - 108), (cx - 10, cy + 150), (cx - 90, cy + 135)], fill=(120, 90, 60), outline=INK)
        d.polygon([(cx - 10, cy - 108), (cx + 90, cy - 135), (cx + 90, cy + 135), (cx - 10, cy + 150)], fill=(255, 230, 150, 200))
    else: d.ellipse((cx + 45, cy - 9, cx + 63, cy + 9), fill=col)
def keygrid(d, x0, y0, cols, rows, col, step=64, s=0.75, cross=False):
    for r_ in range(rows):
        for c_ in range(cols):
            x_, y_ = x0 + c_ * step, y0 + r_ * 46; keyicon(d, x_, y_, col, s)
            if cross: d.line([(x_ - 12, y_ - 14), (x_ + 40, y_ + 14)], fill=RED, width=5)

EL = []   # (start, end, layer, pos, content_bbox, name)
def at(start, end, fn, name, blip=True):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); bb = lay.getbbox()
    if bb is None: QA.append(f"empty overlay {name}"); return
    if bb[0] < SAFE[0] or bb[1] < SAFE[1] or bb[2] > SAFE[2] or bb[3] > SAFE[3]:
        QA.append(f"overlay '{name}' outside safe zone: bbox {bb}")
    p = 40; pb = (max(bb[0] - p, 0), max(bb[1] - p, 0), min(bb[2] + p, W), min(bb[3] + p, H)); c = lay.crop(pb)
    g = np.array(c.filter(ImageFilter.GaussianBlur(14))); g[..., 3] = (g[..., 3] * 0.85).astype(np.uint8)
    EL.append((start, end, Image.alpha_composite(Image.fromarray(g), c), pb[:2], bb, name))
    if blip: BLIPS.append(start)
def sign(lines, col=YEL, y=420):
    """C-mode sign: 1-2 lines, auto-sized box."""
    if isinstance(lines, str): lines = [lines]
    def fn(d):
        fonts = [LBL] + [LBL_S] * (len(lines) - 1)
        w_ = max(d.textlength(s, font=f) for s, f in zip(lines, fonts)) + 90
        h_ = 110 + 64 * (len(lines) - 1)
        box(d, (540 - w_ / 2, y - h_ / 2, 540 + w_ / 2, y + h_ / 2), col)
        for i, (s, f) in enumerate(zip(lines, fonts)):
            ctext(d, (540, y - (len(lines) - 1) * 32 + i * 64), s, f, col if i == 0 else DIM)
    return fn

# screen for diagram mode (inside the safe zone)
SX0, SY0, SX1, SY1 = 40, 260, 1040, 1180
def screen_bg():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((SX0, SY0, SX1, SY1), 36, fill=NAVY + (245,), outline=(70, 90, 140), width=6)
    for x_ in range(SX0 + 30, SX1, 50): d.line([(x_, SY0 + 6), (x_, SY1 - 6)], fill=GRID + (255,))
    for y_ in range(SY0 + 30, SY1, 50): d.line([(SX0 + 6, y_), (SX1 - 6, y_)], fill=GRID + (255,))
    g = im.filter(ImageFilter.GaussianBlur(20)); out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(g); out.alpha_composite(im); return out
SCREEN = screen_bg()

# ------------------------------------------------------------------ overlay timeline
# 0 (C) hook
at(W_(0, "4091"), LE(0), lambda d: (ctext(d, (540, 400), "4,091", BIGN, YEL), ctext(d, (540, 530), "passwords · one try", LBL, WHITE)), "hook")
# 1 (C)
at(LS(1), LE(1), sign("1 guess = 1 try", RED), "one-guess")
# 2 (D) silent server
at(LS(2), LE(2), lambda d: (server(d, 760, 470), ctext(d, (760, 640), "PROXY SERVER", LBL_S, DIM),
                            ctext(d, (300, 340), "VPN-like proxy", LBL, WHITE)), "server")
at(W_(2, "password"), W_(2, "nothing"), lambda d: (ctext(d, (540, 720), "you + server share it", LBL_S, DIM), box(d, (60, 760, 330, 880), WHITE), ctext(d, (195, 820), "password", LBL_S, WHITE),
                                                arrow(d, (338, 820), (392, 820)), box(d, (400, 760, 660, 880)), ctext(d, (530, 820), "secret key", LBL_S, YEL),
                                                arrow(d, (668, 820), (722, 820)), box(d, (730, 760, 1020, 880), GREEN), ctext(d, (875, 820), "encrypted", LBL_S, GREEN)), "pw-key")
at(W_(2, "wrong"), LE(2), lambda d: (box(d, (70, 420, 500, 520), RED), ctext(d, (285, 470), "wrong password", LBL_S, RED),
                                     arrow(d, (510, 470), (595, 470), RED)), "wrong")
at(W_(2, "nothing"), LE(2), lambda d: (ctext(d, (540, 850), "NO ERROR.", TITLE, WHITE), ctext(d, (540, 980), "JUST SILENCE.", TITLE, DIM)), "silence")
# 3 (C)
at(LS(3), LE(3), sign("am I even close?", DIM), "close", blip=False)
# 4 (D) the door
at(LS(4), LE(4), lambda d: (box(d, (70, 420, 500, 520), GREEN), ctext(d, (285, 470), "right password", LBL_S, GREEN),
                            arrow(d, (510, 470), (595, 470), GREEN), server(d, 760, 470, GREEN, True), ctext(d, (760, 640), "SERVER", LBL_S, GREEN)), "right")
at(LS(4), W_(4, "door"), lambda d: door(d, 250, 860, False, DIM), "door-closed", blip=False)
at(W_(4, "door"), LE(4), lambda d: (door(d, 250, 860, True, GREEN), ctext(d, (650, 800), "a door opens", LBL, GREEN),
                                    ctext(d, (650, 870), "(a network port)", LBL_S, DIM)), "door")
at(W_(4, "see"), LE(4), lambda d: ctext(d, (650, 950), "visible from outside", LBL_S, YEL), "visible")
at(W_(4, "leak"), LE(4), lambda d: (box(d, (110, 1040, 970, 1150)), ctext(d, (540, 1095), "LEAK = a yes / no answer", LBL, YEL)), "leak")
# 5-6 (C) twist
at(W_(5, "twist"), W_(5, "thousands"), sign(["THE TWIST", "AES-GCM"], YEL), "twist-title")
at(W_(5, "thousands"), LE(5), sign(["1 message", "unlocks with 1000s of passwords"], YEL), "twist")
at(LS(6), LE(6), sign("one message?!", WHITE), "one-message", blip=False)
# 7 (D) batches of 4,091
def grid(state):
    def fn(d):
        col = {"all": YEL, "shut": RED, "open": GREEN}[state]
        box(d, (70, 700, 1010, 1100), col)
        keygrid(d, 120, 750, 14, 6, col, cross=state == "shut")
        ctext(d, (540, 1055), {"all": "4,091 passwords · 1 message", "shut": "all 4,091 crossed off",
                               "open": "password is in this batch"}[state], LBL, col)
    return fn
T_SHUT, T_ALL, T_OPEN, T_OFF = W_(7, "shut"), W_(7, "all"), W_(7, "opens"), W_(7, "offline")
at(LS(7), T_SHUT, lambda d: (ctext(d, (540, 340), "ONE MESSAGE", TITLE, YEL), ctext(d, (540, 440), "tests a whole batch", LBL_S, DIM)), "batch-title")
at(LS(7), T_ALL, grid("all"), "grid-all")
at(T_SHUT, T_OPEN, lambda d: (door(d, 540, 470, False, RED), ctext(d, (540, 640), "door stays shut", LBL, RED)), "door-shut")
at(T_ALL, T_OPEN, grid("shut"), "grid-shut")
at(T_OPEN, LE(7), lambda d: (door(d, 540, 470, True, GREEN), ctext(d, (540, 640), "door opens", LBL, GREEN)), "door-open")
at(T_OPEN, T_OFF, grid("open"), "grid-open")
at(T_OFF, LE(7), lambda d: (box(d, (70, 700, 1010, 1100), GREEN), ctext(d, (540, 820), "checked offline", LBL, WHITE),
                            ctext(d, (540, 930), "✔ password found", TITLE, GREEN)), "found")
# 8 (D) why it works: guessable passwords, most likely first
def ranked(d):
    ctext(d, (540, 340), "WHY IT WORKS", TITLE, YEL)
    ctext(d, (540, 440), "people pick guessable passwords", LBL_S, WHITE)
    for i, wdt in enumerate([860, 700, 560, 430, 320, 230]):
        y_ = 540 + i * 80
        d.rounded_rectangle((110, y_, 110 + wdt, y_ + 52), 10, fill=YEL if i < 3 else (120, 110, 60))
        ctext(d, (80, y_ + 26), f"#{i + 1}", font("Inter-SemiBold.otf", 32), DIM)
at(LS(8), LE(8), ranked, "ranked")
at(W_(8, "most"), LE(8), lambda d: (box(d, (110, 1040, 970, 1150)), ctext(d, (540, 1095), "most common passwords tested first", LBL_S, YEL)), "most-common")
# 9 (C)
at(LS(9), LE(9), sign("does it actually work?", WHITE), "work", blip=False)
# 9 (D) stats: rows visible from the start, numbers land on the words
T124, T60 = W_(10, "124"), W_(10, "60000")
at(LS(10), LE(10), lambda d: (ctext(d, (540, 340), "simulated with real leaked passwords", LBL_S, DIM),
                            ctext(d, (540, 420), "1 in 5 passwords cracked", LBL, WHITE),
                            ctext(d, (210, 600), "this trick", LBL_S, YEL), ctext(d, (210, 820), "guessing", LBL_S, RED)), "stats")
at(LS(10), T124, lambda d: ctext(d, (600, 600), "? tries", LBL, DIM), "q1", blip=False)
at(T124, LE(10), lambda d: (d.rounded_rectangle((360, 570, 390, 630), 6, fill=YEL), ctext(d, (560, 600), "124 tries", LBL, YEL)), "n124")
at(LS(10), T60, lambda d: ctext(d, (600, 820), "? tries", LBL, DIM), "q2", blip=False)
at(T60, LE(10), lambda d: (d.rounded_rectangle((360, 790, 1000, 850), 6, fill=RED), ctext(d, (680, 920), "~60,000 tries", LBL, RED)), "n60k")
# 10 (C)
at(W_(11, "partitioning"), LE(11), lambda d: (d.rounded_rectangle((90, 320, 990, 590), 24, fill=(200, 40, 50, 255), outline=INK, width=8),
                                              ctext(d, (540, 410), "PARTITIONING", font(XB, 98), WHITE), ctext(d, (540, 515), "ORACLE ATTACK", font(XB, 84), YEL)), "name")
at(W_(11, "shadowsocks"), LE(11), lambda d: (box(d, (140, 650, 940, 760), GREEN), ctext(d, (540, 705), "found in Shadowsocks · fixed ✔", LBL_S, GREEN)), "fixed")
# 11 (C) end card
at(LS(12), TOTAL + 1, lambda d: (ctext(d, (540, 420), "FOLLOW", font(XB, 130), YEL), ctext(d, (540, 545), "◆ 0xLore", ImageFont.truetype(MONOF, 64), WHITE)), "follow")

# ------------------------------------------------------------------ captions (auto-fit)
chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    if len(cur) == 3 or w["pause"] or re.search(r"[.?!,]$", w["text"]) or i == len(words) - 1 or words[i + 1]["line"] != w["line"]:
        chunks.append(cur); cur = []
_m = ImageDraw.Draw(Image.new("RGB", (10, 10)))
def cap_text(w): return w["text"] if "0xLore" in w["text"] else w["text"].upper()
CAPFONT = {}
for ci, c in enumerate(chunks):
    size = 78
    while size > 50:
        f = font(XB, size)
        if sum(_m.textlength(cap_text(w) + " ", font=f) for w in c) - _m.textlength(" ", font=f) <= CAP_MAXW: break
        size -= 2
    CAPFONT[ci] = font(XB, size)
    wtot = sum(_m.textlength(cap_text(w) + " ", font=CAPFONT[ci]) for w in c)
    if wtot - _m.textlength(" ", font=CAPFONT[ci]) > CAP_MAXW: QA.append(f"caption too wide: {' '.join(cap_text(w) for w in c)}")

# ------------------------------------------------------------------ mode mix
def dmix(t):
    v = 0.0
    for li, L_ in enumerate(LINES):
        if L_[1] == "D":
            a, b = L_[3], L_[4]
            nxt_d = li + 1 < len(LINES) and LINES[li + 1][1] == "D"
            prv_d = li > 0 and LINES[li - 1][1] == "D"
            lo = a if prv_d else a - 0.25; hi = b if nxt_d else b + 0.05
            if lo <= t < hi:
                v = max(v, min(1 if prv_d else ease((t - lo) / 0.3), 1 if nxt_d else ease((hi - t + 0.25) / 0.3)))
    return v
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

# ------------------------------------------------------------------ QA (before render)
def qa_timeline():
    step = 1 / FPS; t = 0; empty = 0
    while t < TOTAL:
        active = [e for e in EL if e[0] <= t < e[1]]
        if dmix(t) > 0.5 and not active:
            empty += step
            if empty > 0.25: QA.append(f"diagram screen empty around {t:.2f}s"); empty = -1e9
        else: empty = 0 if empty >= 0 else empty
        t += step
    # flicker: an overlay ends and the next one in the same slot starts > 1 frame later within the same line
    ends = sorted(EL, key=lambda e: e[1])
    for e in EL:
        for o in EL:
            if o is e: continue
            ov = not (o[4][2] < e[4][0] or o[4][0] > e[4][2] or o[4][3] < e[4][1] or o[4][1] > e[4][3])
            gap = o[0] - e[1]
            if ov and 0 < gap < 0.6 and line_at(e[1] - 0.01) == line_at(o[0]):
                QA.append(f"flicker: '{e[5]}' ends {gap:.2f}s before '{o[5]}' starts in the same place")
    first_visual = min(e[0] for e in EL)
    first_word = words[0]["start"]
    hook_word = W_(0, "4091")
    if hook_word > 1.5: QA.append(f"hook number lands at {hook_word:.2f}s (> 1.5s)")
    if first_word > 0.5: QA.append(f"first word at {first_word:.2f}s")
    if TOTAL - VOICE_END > 1.8: QA.append(f"end tail {TOTAL - VOICE_END:.2f}s")
    if TOTAL > 90: QA.append(f"too long: {TOTAL:.1f}s")
qa_timeline()

# ------------------------------------------------------------------ audio mix + loudness
for b in BLIPS: add(BLIP, b)
music = pad / np.max(np.abs(pad)) * 0.07 + pulse * 0.06
fade = np.clip(np.minimum(tt / 0.6, (TOTAL - tt) / 1.0), 0, 1)
mix = (music + sfx) * fade; mix[:len(voice)] += voice
meter = pyln.Meter(SR); lufs = meter.integrated_loudness(mix)
mix = pyln.normalize.loudness(mix, lufs, -13.0)
peak = np.max(np.abs(mix))
if peak > 0.89: mix = np.tanh(mix / 0.89 * 1.0) * 0.89      # soft limit to ~ -1 dBTP
WAV = os.path.join(WORK, "po3.wav"); sf.write(WAV, mix, SR)

# ------------------------------------------------------------------ frame render
def wm():
    f = ImageFont.truetype(MONOF, 38); im = Image.new("RGBA", (240, 56), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(12, 28), (28, 12), (44, 28), (28, 44)], fill=YEL + (180,)); d.text((58, 28), "0xLore", font=f, fill=WHITE + (180,), anchor="lm"); return im
WM = wm()

def render(fi):
    t = fi / FPS; k = dmix(t)
    im = BG.copy() if k < 0.01 else Image.blend(BG, BG_DIM, k)
    ch, pos = chars_layer(t, fi, 1 - 0.40 * k, FEET + 120 * k); im.alpha_composite(ch, pos)
    if k > 0.01:
        im.alpha_composite(SCREEN if k >= 1 else Image.fromarray((np.array(SCREEN) * np.array([1, 1, 1, k])).astype(np.uint8)))
    for a, b, lay, p, bb, name in EL:
        if a <= t < b:
            e = ease((t - a) / 0.25); l2 = lay
            if e < 1:
                s_ = 0.88 + 0.12 * e; l2 = lay.resize((max(1, int(lay.width * s_)), max(1, int(lay.height * s_))))
                al = np.array(l2); al[..., 3] = (al[..., 3] * e).astype(np.uint8); l2 = Image.fromarray(al)
            im.alpha_composite(l2, (p[0] + (lay.width - l2.width) // 2, p[1] + (lay.height - l2.height) // 2))
    spk = next((s for s, a, b, _ in turns if a - 0.2 <= t < b + 0.3), None)
    z = 1 + (0.05 if spk else 0.02) * (1 - k)
    tx = STYLE[spk]["x"] if spk else 540
    cx = 540 + (tx - 540) * 0.3 * (1 - k)
    if z > 1.001:
        cw, chh = int(W / z), int(H / z); x0 = int(min(max(cx - cw / 2, 0), W - cw)); y0 = int((H - chh) * 0.6)
        im = im.crop((x0, y0, x0 + cw, y0 + chh)).resize((W, H), Image.BILINEAR)
    for bt in BOOMS:
        if 0 <= t - bt < 0.3:
            amp = 10 * (1 - (t - bt) / 0.3); im = Image.fromarray(np.roll(np.array(im), int(amp * math.sin(t * 80)), 1))
    im.alpha_composite(WM, ((W - WM.width) // 2, 150))
    d = ImageDraw.Draw(im); d.rectangle((0, 0, int(W * t / TOTAL), 10), fill=YEL)
    ci = next((i for i, c in enumerate(chunks) if c[0]["start"] - 0.05 <= t < c[-1]["end"] + 0.2), None)
    if ci is not None:
        c = chunks[ci]; f = CAPFONT[ci]; texts = [cap_text(w) for w in c]; widths = [d.textlength(s + " ", font=f) for s in texts]
        x_ = (W - (sum(widths) - d.textlength(" ", font=f))) / 2
        for w, s, wd in zip(c, texts, widths):
            if t >= w["start"] - 0.05:
                pop = ease((t - w["start"] + 0.05) / 0.12)
                d.text((x_, CAP_Y - int(205 * k) + int(10 * (1 - pop))), s, font=f, fill=YEL if w["key"] else WHITE, stroke_width=8, stroke_fill=INK)
            x_ += wd
    return im.convert("RGB").tobytes()

def make_cover(path):
    im = BG.copy()
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle((0, 250, W, 860), fill=(8, 10, 30, 215))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(30)))
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tsur = (SURPRISE[1][0] + SURPRISE[1][1]) / 2
    old = dict(STYLE["rio"]); STYLE["rio"]["x"] = 540; draw_char(d, "rio", tsur, int(tsur * FPS)); STYLE["rio"].update(old)
    bb = lay.getbbox(); cr = lay.crop(bb); sc = 1.15
    cr = cr.resize((int(cr.width * sc / SS), int(cr.height * sc / SS)), Image.LANCZOS)
    im.alpha_composite(cr, (540 - cr.width // 2 + 40, H - cr.height + 40))
    lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d2 = ImageDraw.Draw(lay2)
    ctext(d2, (540, 400), "4,091", font(XB, 210), YEL)
    ctext(d2, (540, 560), "PASSWORDS.", font(XB, 116), WHITE)
    d2.rounded_rectangle((170, 640, 910, 780), 22, fill=(200, 40, 50, 255), outline=INK, width=8)
    ctext(d2, (540, 710), "ONE TRY.", font(XB, 100), WHITE)
    bb2 = lay2.getbbox()
    if bb2[1] < 285 or bb2[3] > 1635: QA.append(f"cover text outside 4:5 centre crop: {bb2}")
    g = lay2.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(g); im.alpha_composite(lay2)
    im.convert("RGB").save(path, quality=92)

if __name__ == "__main__":
    make_cover(COVER)
    if QA:
        print("QA FAILED:"); [print(" -", q) for q in QA]; sys.exit(2)
    print("QA pre-render: PASS")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-profile:v", "high", "-vf", "setsar=1", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                           "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for buf in p.imap(render, range(NF), chunksize=8): ff.stdin.write(buf)
    ff.stdin.close(); ff.wait(); print("done", OUT, NF)
