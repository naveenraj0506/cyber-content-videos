"""15-second cartoon-style test scene (Partitioning Oracle teaser) for 0xLore.

Usage: python3 render_scene.py <dir with kokoro model files> <output.mp4>
Everything is drawn in code: original characters (Rio, Mina), night rooftop
backdrop, lip-sync from the voice envelope, blinks, gestures, camera moves.
Facts used (Len, Grubbs, Ristenpart, "Partitioning Oracle Attacks", USENIX
Security 2021): a ciphertext can be built that is valid under k keys
(k = 2^16 for AES-GCM in < 30 min, Fig. 2); a failed decryption rules out
the whole set at once.
"""
import sys, os, re, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import soundfile as sf
from multiprocessing import Pool

WORK, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, SR, SS = 1080, 1920, 30, 24000, 2      # SS = supersampling for characters
INK = (22, 20, 38); YEL = (255, 210, 40); WHITE = (245, 247, 252); RED = (255, 90, 90)
GREEN = (90, 225, 130); DIM = (170, 180, 210); PANEL = (14, 24, 52)
F = "/usr/share/fonts/opentype/inter/"; DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(n, s): return ImageFont.truetype(F + n, s)
CAP = font("Inter-ExtraBold.otf", 78); LBL = font("Inter-Bold.otf", 54); LBL_S = font("Inter-SemiBold.otf", 40)
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 40)

# ---------------------------------------------------------------- dialogue
LINES = [
 ("rio",  "am_michael", "This server only tells me *one* thing. Did my message decrypt... or *not*?"),
 ("mina", "af_heart",   "Then ask a *smarter* question. One ciphertext, valid for *sixty-five* *thousand* password guesses at once."),
 ("rio",  "am_michael", "Wait... so one *no* rules them *all* out?"),
 ("mina", "af_heart",   "Every. Single. One."),
]

from kokoro_onnx import Kokoro
kok = Kokoro(os.path.join(WORK, "kokoro-v1.0.onnx"), os.path.join(WORK, "voices-v1.0.bin"))
def trim(x, thr=0.01):
    i = np.where(np.abs(x) > thr)[0]; return x[max(i[0] - 240, 0): i[-1] + 480]
def clean(w): return re.sub(r"[^\w-]", "", w.replace("*", "")).lower()

voice, words, turns = [np.zeros(int(SR * 0.4))], [], []
t = 0.4
for spk, vc, text in LINES:
    tts = text.replace("*", "").replace("...", ",")
    s, _ = kok.create(tts, voice=vc, speed=1.12, lang="en-us")
    s = trim(np.asarray(s, np.float32)); dur = len(s) / SR
    toks = text.split(); wts = [len(clean(w)) + 2 + (5 if re.search(r"[.?!,]$", w) else 0) for w in toks]
    acc = t
    for w, wt in zip(toks, wts):
        d = dur * wt / sum(wts)
        words.append(dict(text=w.replace("*", "").replace("...", ""), key=w.startswith("*"), start=acc,
                          end=acc + d, c=clean(w), spk=spk)); acc += d
    turns.append((spk, t, t + dur, s)); voice.append(s); t += dur
    gap = 0.38; voice.append(np.zeros(int(SR * gap))); t += gap
BANNER_T = t + 0.1
TOTAL = BANNER_T + 2.4
voice = np.concatenate(voice); print("duration", round(TOTAL, 2))

# mouth openness per speaker per frame (RMS envelope of their own lines)
NF = int(TOTAL * FPS)
mouth = {"rio": np.zeros(NF), "mina": np.zeros(NF)}
for spk, a, b, s in turns:
    hop = SR // FPS
    for k in range(int((b - a) * FPS)):
        seg = s[k * hop:(k + 1) * hop]
        if len(seg): mouth[spk][int(a * FPS) + k] = min(1, np.sqrt(np.mean(seg ** 2)) * 9)
for m in mouth.values():   # light smoothing so the mouth doesn't flicker
    m[:] = np.convolve(m, [0.25, 0.5, 0.25], "same")

def speaking(spk, t): return any(s == spk and a <= t < b for s, a, b, _ in turns)
def wtime(prefix, spk=None, after=0):
    for w in words:
        if w["start"] >= after and w["c"].startswith(prefix) and (spk is None or w["spk"] == spk): return w["start"]
    raise SystemExit("no word " + prefix)

# ---------------------------------------------------------------- audio mix
n = int(TOTAL * SR); tt = np.arange(n) / SR
pad = sum(np.sin(2 * np.pi * f * tt) * 0.5 + 0.25 * np.sin(2 * np.pi * f * 1.004 * tt) for f in (110, 164.81, 196, 246.94))
pad *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * tt)
crick = np.zeros(n); rng = np.random.default_rng(3)
for k in range(int(TOTAL * 3)):   # soft night ambience ticks
    i = rng.integers(0, n - 2000); crick[i:i + 2000] += np.sin(2 * np.pi * 4200 * np.arange(2000) / SR) * np.exp(-np.arange(2000) / 300) * 0.02
sfx = np.zeros(n)
def add(sig, at):
    i = int(at * SR); L = min(len(sig), n - i)
    if L > 0: sfx[i:i + L] += sig[:L]
L = int(1.3 * SR); x = np.arange(L) / SR
boom = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-x * 2.5) + 35) / SR) * np.exp(-x * 3) * 0.6
T_NO = wtime("no", "rio"); T_ALL = wtime("all", "rio"); T_KEYS = wtime("sixty", "mina")
add(boom, BANNER_T); add(boom * 0.5, T_ALL)
L2 = int(0.12 * SR); blip = np.sin(2 * np.pi * 880 * np.arange(L2) / SR) * np.exp(-np.arange(L2) / SR * 30) * 0.12
for tk in (wtime("decrypt", "rio"), T_KEYS, T_NO): add(blip, tk)
fade = np.clip(np.minimum(tt / 1.0, (TOTAL - tt) / 1.0), 0, 1)
mix = (pad / np.max(np.abs(pad)) * 0.07 + crick + sfx) * fade; mix[:len(voice)] += voice
mix /= max(1, np.max(np.abs(mix)) / 0.97); WAV = os.path.join(WORK, "scene.wav"); sf.write(WAV, mix, SR)

# ---------------------------------------------------------------- backdrop
def backdrop():
    im = Image.new("RGB", (W, H)); px = np.zeros((H, W, 3), np.float32)
    top, bot = np.array([16, 14, 48]), np.array([88, 52, 120])
    for y in range(H): px[y] = top + (bot - top) * min(1, y / 1250)
    im = Image.fromarray(px.astype(np.uint8)); d = ImageDraw.Draw(im); r = random.Random(7)
    for _ in range(140): x, y = r.randrange(W), r.randrange(0, 700); d.ellipse((x, y, x + 3, y + 3), fill=(230, 230, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse((760, 170, 940, 350), fill=(255, 244, 200, 255)); im.paste(glow.filter(ImageFilter.GaussianBlur(40)), (0, 0), glow.filter(ImageFilter.GaussianBlur(40)))
    d.ellipse((770, 180, 930, 340), fill=(255, 246, 215))
    # far + near skyline
    for layer, (col, lo, hi, win) in enumerate([((44, 36, 92), 520, 820, (120, 100, 160)), ((30, 26, 64), 640, 980, (255, 196, 110))]):
        x = -20
        while x < W:
            bw = r.randrange(90, 190); top_y = r.randrange(lo, hi - 120)
            glass = layer == 1 and r.random() < 0.25
            d.rectangle((x, top_y, x + bw, 1330), fill=(26, 58, 92) if glass else col, outline=INK, width=4)
            if glass:
                for gx in range(x + 14, x + bw - 6, 22): d.line([(gx, top_y + 10), (gx, 1330)], fill=(60, 110, 150), width=3)
            else:
                for wy in range(top_y + 24, 1300, 46):
                    for wx in range(x + 16, x + bw - 24, 34):
                        if r.random() < 0.55: d.rectangle((wx, wy, wx + 16, wy + 22), fill=win)
            if r.random() < 0.3: d.line([(x + bw // 2, top_y), (x + bw // 2, top_y - 60)], fill=INK, width=5)
            x += bw + r.randrange(-10, 14)
    # rooftop floor + brick parapet
    d.polygon([(0, 1420), (W, 1420), (W, H), (0, H)], fill=(52, 54, 72))
    for y in range(1450, H, 60): d.line([(0, y), (W, y)], fill=(60, 62, 82), width=2)
    d.rectangle((0, 1250, W, 1420), fill=(140, 70, 60), outline=INK, width=5)
    for row, y in enumerate(range(1262, 1410, 34)):
        d.line([(0, y + 30), (W, y + 30)], fill=(110, 52, 48), width=3)
        for bx in range(-40 + (row % 2) * 45, W, 90): d.line([(bx, y), (bx, y + 30)], fill=(110, 52, 48), width=3)
    d.rectangle((0, 1238, W, 1262), fill=(170, 160, 160), outline=INK, width=4)
    # plants
    for px_, s in ((70, 1.0), (1010, 1.1), (560, 0.7)):
        d.polygon([(px_ - 40 * s, 1250), (px_ + 40 * s, 1250), (px_ + 30 * s, 1180), (px_ - 30 * s, 1180)], fill=(150, 90, 60), outline=INK)
        for a in range(-60, 61, 30):
            ex = px_ + math.sin(math.radians(a)) * 90 * s; ey = 1180 - math.cos(math.radians(a)) * 110 * s
            d.ellipse((ex - 26 * s, ey - 14 * s, ex + 26 * s, ey + 14 * s), fill=(60, 140, 80), outline=INK, width=3)
    # string lights
    lights = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lights)
    pts = [(x, 1205 + 40 * math.sin(math.pi * (x % 360) / 360)) for x in range(0, W + 1, 8)]
    d.line(pts, fill=INK, width=3)
    for x, y in pts[::5]: ld.ellipse((x - 9, y - 4, x + 9, y + 14), fill=(255, 220, 140, 255))
    im.paste(lights.filter(ImageFilter.GaussianBlur(10)), (0, 0), lights.filter(ImageFilter.GaussianBlur(10)))
    im.paste(lights, (0, 0), lights)
    return im
BG = backdrop()

# ---------------------------------------------------------------- characters
STYLE = {
 "rio":  dict(x=300, face=1,  skin=(196, 140, 100), hair=(30, 24, 30), top=(255, 190, 40), pants=(56, 90, 150), hairstyle="spiky"),
 "mina": dict(x=790, face=-1, skin=(222, 172, 140), hair=(70, 50, 50), top=(40, 160, 150), pants=(150, 150, 160), hairstyle="bun"),
}
FEET = 1640

def draw_char(d, st, t, fi, other_x):
    S = SS; f = st["face"]; x0 = st["x"]
    talk = speaking(st["name"], t)
    m = mouth[st["name"]][min(fi, NF - 1)]
    bob = math.sin(t * 2.2 + x0) * 4
    fy = FEET + bob
    def P(x, y): return (x * S, y * S)
    def line(a, b, w, col):
        d.line([P(*a), P(*b)], fill=INK, width=int((w + 10) * S)); d.ellipse(circ(b, (w + 10) / 2), fill=INK)
        d.line([P(*a), P(*b)], fill=col, width=int(w * S)); d.ellipse(circ(b, w / 2), fill=col)
    def circ(c, r): return (c[0] * S - r * S, c[1] * S - r * S, c[0] * S + r * S, c[1] * S + r * S)
    def ell(c, rx, ry, col, ow=5): d.ellipse((P(c[0] - rx, c[1] - ry) + P(c[0] + rx, c[1] + ry)), fill=col, outline=INK, width=int(ow * S))
    # legs + shoes
    for dx in (-30, 30):
        d.rounded_rectangle(P(x0 + dx - 22, fy - 250) + P(x0 + dx + 22, fy - 20), 14 * S, fill=st["pants"], outline=INK, width=5 * S)
        ell((x0 + dx + 10 * f, fy - 14), 36, 18, (240, 240, 240))
    # gesture: talking arm swings up and down with the speech, plus emphasis
    g = 0.0
    if talk: g = 0.55 + 0.35 * math.sin(t * 5.0)
    sh_y = fy - 440
    rest = (x0 - 95 * f, fy - 255)
    line((x0 - 70 * f, sh_y), rest, 34, st["top"])                          # back arm
    # torso
    d.rounded_rectangle(P(x0 - 92, fy - 460) + P(x0 + 92, fy - 230), 46 * S, fill=st["top"], outline=INK, width=5 * S)
    d.arc(P(x0 - 45, fy - 330) + P(x0 + 45, fy - 270), 0, 180, fill=INK, width=4 * S)
    # front arm (gesturing)
    hx = x0 + f * (95 + 70 * g); hy = fy - 255 - 220 * g
    line((x0 + 70 * f, sh_y), (hx, hy), 34, st["top"]); ell((hx, hy), 20, 20, st["skin"], 4)
    # head
    lean = 14 * f if talk else 0
    cx = x0 + lean; cy = fy - 575 + (math.sin(t * 9) * 4 if talk else 0)
    if st["hairstyle"] == "bun":
        ell((cx - 8 * f, cy - 120), 44, 40, st["hair"])
    ell((cx - 96 * f, cy + 10), 18, 24, st["skin"])                          # ear
    ell((cx, cy), 112, 118, st["skin"], 6)
    # hair
    hair = st["hair"]
    if st["hairstyle"] == "spiky":
        pts = [P(cx - 118, cy - 10)]
        for i in range(9):
            a = math.pi + i * math.pi / 8
            r_ = 150 if i % 2 else 112
            pts.append(P(cx + r_ * math.cos(a) * 1.0, cy - 25 + r_ * math.sin(a) * 1.0))
        pts.append(P(cx + 118, cy - 10)); pts.append(P(cx + 60, cy - 60)); pts.append(P(cx - 60, cy - 60))
        d.polygon(pts, fill=hair, outline=INK, width=5 * S)
    else:
        d.chord(P(cx - 116, cy - 122) + P(cx + 116, cy + 60), 180, 360, fill=hair, outline=INK, width=5 * S)
        d.polygon([P(cx + 100 * f, cy - 40), P(cx + 118 * f, cy + 70), P(cx + 84 * f, cy + 40)], fill=hair, outline=INK)
    # eyes (look at the other character), blink every ~3.7 s
    blink = (t + x0 / 300) % 3.7 < 0.12
    look = 7 * (1 if other_x > x0 else -1)
    surprise = st["name"] == "rio" and T_NO - 1.2 <= t < T_ALL + 0.8
    for ex in (-40, 40):
        e = (cx + ex + 10 * f, cy + 6)
        if blink: d.line([P(e[0] - 16, e[1]), P(e[0] + 16, e[1])], fill=INK, width=5 * S)
        else:
            ry = 26 if surprise else 22
            ell(e, 18, ry, WHITE, 4); ell((e[0] + look, e[1] + 2), 9, 10, INK, 0)
        by = e[1] - (44 if surprise else 34) - (4 if talk and math.sin(t * 3) > 0.6 else 0)
        d.line([P(e[0] - 18, by + (0 if ex * f > 0 else 4)), P(e[0] + 18, by + (4 if ex * f > 0 else 0))], fill=INK, width=6 * S)
    # mouth
    mc = (cx + 18 * f, cy + 62)
    if m > 0.12:
        oh = 6 + 30 * m
        d.ellipse(P(mc[0] - 24, mc[1] - oh / 2) + P(mc[0] + 24, mc[1] + oh / 2), fill=(120, 30, 40), outline=INK, width=4 * S)
        if oh > 16: d.chord(P(mc[0] - 14, mc[1]) + P(mc[0] + 14, mc[1] + oh / 2), 180, 360, fill=(230, 100, 110))
    elif surprise: ell(mc, 12, 14, (120, 30, 40), 4)
    else: d.arc(P(mc[0] - 22, mc[1] - 16) + P(mc[0] + 22, mc[1] + 10), 20, 160, fill=INK, width=5 * S)

def chars_layer(t, fi):
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for name in ("rio", "mina"):
        st = dict(STYLE[name], name=name); other = STYLE["mina" if name == "rio" else "rio"]["x"]
        draw_char(d, st, t, fi, other)
    box = lay.getbbox(); crop = lay.crop(box)
    small = crop.resize((crop.width // SS, crop.height // SS), Image.LANCZOS)
    return small, (box[0] // SS, box[1] // SS)

# ---------------------------------------------------------------- overlays
def ctext(d, xy, s, f, fill):
    if not any(c in "✔✘" for c in s): d.text(xy, s, font=f, fill=fill, anchor="mm"); return
    fb = ImageFont.truetype(DJ, f.size); parts = [(c, fb if c in "✔✘" else f) for c in s]
    x = xy[0] - sum(d.textlength(c, font=q) for c, q in parts) / 2
    for c, q in parts: d.text((x, xy[1]), c, font=q, fill=fill, anchor="lm"); x += d.textlength(c, font=q)
def glow(fn):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); bb = lay.getbbox(); p = 40
    bb = (max(bb[0] - p, 0), max(bb[1] - p, 0), min(bb[2] + p, W), min(bb[3] + p, H)); c = lay.crop(bb)
    g = np.array(c.filter(ImageFilter.GaussianBlur(14))); g[..., 3] = (g[..., 3] * 0.85).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(g), c), bb[:2]
def panel(d, xy, col=YEL): d.rounded_rectangle(xy, 26, fill=PANEL + (235,), outline=col, width=6)
def keyicon(d, x, y, col, s=1.0):
    d.ellipse((x - 11 * s, y - 11 * s, x + 11 * s, y + 11 * s), outline=col, width=int(5 * s))
    d.line([(x + 11 * s, y), (x + 44 * s, y)], fill=col, width=int(6 * s)); d.line([(x + 36 * s, y), (x + 36 * s, y + 10 * s)], fill=col, width=int(6 * s))

def keygrid(col, crossed=False):
    def fn(d):
        panel(d, (90, 520, 990, 860), col)
        for r_ in range(4):
            for c_ in range(9):
                x, y = 160 + c_ * 92, 580 + r_ * 50; keyicon(d, x, y, col, 0.8)
                if crossed: d.line([(x - 12, y - 14), (x + 40, y + 14)], fill=RED, width=5)
        ctext(d, (540, 810), "65,536 password guesses" if not crossed else "ALL ruled out ✘", LBL_S, col)
    return glow(fn)

T_SERVER = wtime("server", "rio"); T_CT = wtime("ciphertext", "mina")
OVER = [  # (start, end, layer)
 (T_SERVER, T_CT, glow(lambda d: (panel(d, (240, 440, 840, 700), DIM), ctext(d, (540, 510), "SERVER", LBL, WHITE),
                                   ctext(d, (540, 610), "decrypted?  ✔  or  ✘", LBL_S, YEL)))),
 (T_CT, T_KEYS, glow(lambda d: (panel(d, (250, 520, 830, 660)), ctext(d, (540, 590), "1 ciphertext", LBL, YEL)))),
 (T_KEYS, T_ALL, keygrid(YEL)),
 (T_ALL, BANNER_T, keygrid(RED, True)),
 (BANNER_T, TOTAL + 1, glow(lambda d: (d.rounded_rectangle((60, 380, 1020, 640), 20, fill=(200, 40, 50), outline=INK, width=8),
                                        ctext(d, (540, 470), "PARTITIONING", font("Inter-ExtraBold.otf", 92) if os.path.exists(F + "Inter-ExtraBold.otf") else LBL, WHITE),
                                        ctext(d, (540, 570), "ORACLE ATTACK", font("Inter-ExtraBold.otf", 80) if os.path.exists(F + "Inter-ExtraBold.otf") else LBL, YEL)))),
]
def wm():
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 40)
    im = Image.new("RGBA", (260, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(14, 30), (30, 14), (46, 30), (30, 46)], fill=YEL + (170,)); d.text((62, 30), "0xLore", font=f, fill=WHITE + (170,), anchor="lm"); return im
WM = wm()

chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    if len(cur) == 3 or re.search(r"[.?!,]$", w["text"]) or i == len(words) - 1 or words[i + 1]["spk"] != w["spk"]:
        chunks.append(cur); cur = []

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def render(fi):
    t = fi / FPS
    im = BG.copy().convert("RGBA")
    ch, pos = chars_layer(t, fi); im.alpha_composite(ch, pos)
    for a, b, (lay, p) in OVER:
        if a <= t < b:
            k = ease((t - a) / 0.3); l2 = lay
            if k < 1:
                s_ = 0.8 + 0.2 * k; l2 = lay.resize((int(lay.width * s_), int(lay.height * s_)))
                al = np.array(l2); al[..., 3] = (al[..., 3] * k).astype(np.uint8); l2 = Image.fromarray(al)
            im.alpha_composite(l2, (p[0] + (lay.width - l2.width) // 2, p[1] + (lay.height - l2.height) // 2))
    # camera: drift toward whoever is speaking, punch-in on the banner
    spk = next((s for s, a, b, _ in turns if a - 0.2 <= t < b + 0.3), None)
    tx = STYLE[spk]["x"] if spk else 540
    z = 1.07 if spk else 1.03
    if t >= BANNER_T: z = 1.0 + 0.06 * ease((t - BANNER_T) / 0.4); tx = 540
    cx = 540 + (tx - 540) * 0.35
    cw, chh = int(W / z), int(H / z); x0 = int(min(max(cx - cw / 2, 0), W - cw)); y0 = int((H - chh) * 0.55)
    im = im.crop((x0, y0, x0 + cw, y0 + chh)).resize((W, H), Image.BILINEAR)
    if 0 <= t - BANNER_T < 0.3:
        amp = 12 * (1 - (t - BANNER_T) / 0.3); im = Image.fromarray(np.roll(np.array(im), int(amp * math.sin(t * 80)), 1))
    im.alpha_composite(WM, (W - WM.width - 30, 40))
    d = ImageDraw.Draw(im)
    c = next((c for c in chunks if c[0]["start"] - 0.05 <= t < c[-1]["end"] + 0.2), None)
    if c:
        texts = [w["text"].upper() for w in c]; widths = [d.textlength(s + " ", font=CAP) for s in texts]
        x = (W - sum(widths)) / 2; y = 1730
        for w, s, wd in zip(c, texts, widths):
            if t >= w["start"] - 0.05:
                pop = ease((t - w["start"] + 0.05) / 0.12)
                d.text((x, y + int(10 * (1 - pop))), s, font=CAP, fill=YEL if w["key"] else WHITE, stroke_width=8, stroke_fill=INK)
            x += wd
    return im.convert("RGB").tobytes()

if __name__ == "__main__":
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    with Pool(4) as p:
        for buf in p.imap(render, range(NF), chunksize=8): ff.stdin.write(buf)
    ff.stdin.close(); ff.wait(); print("done", OUT, NF)
