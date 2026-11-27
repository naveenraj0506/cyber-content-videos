"""Render the Invisible Salamanders Short (v2: storytelling cut).

Usage: python3 render_v2.py <dir with kokoro model files> <output.mp4>
Kokoro TTS per phrase -> proportional word timings -> PIL frames
(1080x1920, 30 fps) -> ffmpeg H.264 + AAC. Music and sound effects are
synthesised here (original audio, no third-party samples).
"""
import sys, os, re, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import soundfile as sf
from multiprocessing import Pool

WORK, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, SR = 1080, 1920, 30, 24000

BG = (8, 15, 36); GRID = (22, 36, 70); YEL = (255, 210, 40); WHITE = (245, 247, 252)
DIM = (150, 168, 200); RED = (255, 90, 90); GREEN = (90, 225, 130); PANEL = (14, 24, 52)
F = "/usr/share/fonts/opentype/inter/"
DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(name, size): return ImageFont.truetype(F + name, size)
CAP = font("Inter-ExtraBold.otf", 86) if os.path.exists(F + "Inter-ExtraBold.otf") else font("Inter-Bold.otf", 86)
LBL = font("Inter-Bold.otf", 56); LBL_S = font("Inter-SemiBold.otf", 42); TITLE = font("Inter-Bold.otf", 84)
BIG = font("Inter-Bold.otf", 120); SEALF = font("Inter-Bold.otf", 80)
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 44)

# Story. *word* = yellow keyword. "..." = dramatic pause.
# sfx: "boom" (twist/reveal, with screen shake), "riser" (builds into next scene).
# Elements: (trigger, draw-fn); trigger = 0 (scene start) or a word prefix,
# matched at/after the previous trigger.
SCENES = [
 dict(id="hook", sfx="boom", text=
  "One encrypted file. Two different keys. Two *completely* different files. "
  "And the encryption swears *both* are genuine."),
 dict(id="question", sfx="riser", text=
  "Sounds impossible, right? Encryption exists to stop *exactly* this. "
  "So how does it happen? Let's start with how it's *supposed* to work."),
 dict(id="gcm", text=
  "*AES-GCM* is everywhere. It's in *TLS*, the protocol behind HTTPS. "
  "It scrambles your data... and then stamps it with a *tag*. "
  "Think of the tag as a wax *seal* that only the key holder can make."),
 dict(id="flip", sfx="riser", text=
  "Flip a single bit... and the seal *breaks*. "
  "So we all trust one simple rule: valid seal means the message is *real*."),
 dict(id="twist", sfx="boom", text=
  "But here's the catch. That seal only stops *outsiders*, people without the key. "
  "It *never* promised a ciphertext belongs to just *one* key. "
  "Cryptographers call that missing promise *key* *commitment*. And GCM... *doesn't* have it."),
 dict(id="split", sfx="boom", text=
  "So what if the attacker picks *both* keys? "
  "They can craft *one* ciphertext whose seal is valid under key A... *and* under key B. "
  "Open it with A? A *harmless* file. Open it with B? Something *malicious*."),
 dict(id="formats", text=
  "And this isn't theory. In 2022, researchers released a tool that does exactly this. "
  "*PDFs*. Windows *programs*. Even *medical* images."),
 dict(id="stakes", sfx="riser", text=
  "Now picture a system that trusts a ciphertext as *evidence*. Like an abuse report."),
 dict(id="incident", sfx="boom", text=
  "In 2018, researchers did exactly that to *Facebook* *Messenger*. "
  "An abusive image the recipient *couldn't* *report*. Facebook paid a bug bounty."),
 dict(id="fix", text=
  "The fix? *Key-committing* encryption. Follow for more hidden gems."),
]
SAY = {"AES-GCM": "A-E-S G-C-M", "GCM": "G-C-M", "TLS": "T-L-S", "HTTPS": "H-T-T-P-S",
       "PDFs": "P-D-Fs", "2022": "twenty twenty-two", "2018": "twenty eighteen"}

def tts_text(s):
    s = s.replace("*", "").replace("...", ",")
    for k, v in sorted(SAY.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", v, s)
    return s

# ---------- 1. voice ----------
from kokoro_onnx import Kokoro
kok = Kokoro(os.path.join(WORK, "kokoro-v1.0.onnx"), os.path.join(WORK, "voices-v1.0.bin"))
VOICE = os.environ.get("VOICE", "af_heart")

def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[max(idx[0] - 240, 0): idx[-1] + 480] if len(idx) else x
def clean(w): return re.sub(r"[^\w-]", "", w.replace("*", "")).lower()

audio, words, spans = [], [], []
t = 0.15; audio.append(np.zeros(int(SR * t)))
for si, sc in enumerate(SCENES):
    start = t
    phrases = [p for p in re.split(r"(?<=[.?!])\s+", sc["text"]) if p.strip()]
    for ph in phrases:
        q = ph.rstrip().endswith("?")
        speed = 1.1 if len(ph.split()) <= 4 else 1.2   # punchy lines slightly slower
        s, _ = kok.create(tts_text(ph), voice=VOICE, speed=speed, lang="en-us")
        s = trim(np.asarray(s, dtype=np.float32)); dur = len(s) / SR
        toks = ph.split()
        wts = [len(clean(w)) + 2 + (6 if w.endswith("...") else 3 if re.search(r"[,.?!:]$", w) else 0) for w in toks]
        acc = t
        for w, wt in zip(toks, wts):
            d = dur * wt / sum(wts)
            words.append(dict(text=w.replace("*", "").replace("...", ""), key=w.startswith("*"),
                              start=acc, end=acc + d, scene=si, c=clean(w), pause=w.endswith("...")))
            acc += d
        audio.append(s); t += dur
        gap = 0.32 if q else 0.14
        audio.append(np.zeros(int(SR * gap))); t += gap
    gap = 0.2; audio.append(np.zeros(int(SR * gap))); t += gap
    spans.append((start, t))
voice = np.concatenate(audio)
TOTAL = len(voice) / SR + 0.8
print("duration", round(TOTAL, 2))

# ---------- 2. music + sfx ----------
n = int(TOTAL * SR); tt = np.arange(n) / SR
def tone(f): return np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tt)
chords = [[110.0, 130.81, 164.81], [87.31, 130.81, 174.61], [98.0, 146.83, 196.0], [82.41, 123.47, 164.81]]
pad = np.zeros(n); bar = 4.0
for ci, chd in enumerate(chords):
    env = np.zeros(n)
    for k in range(int(TOTAL / bar) + 1):
        if k % 4 != ci: continue
        a = k * bar; m = (tt >= a - 0.5) & (tt < a + bar + 0.5); x = (tt[m] - a) / bar
        env[m] = np.clip(np.minimum((x + 0.125) / 0.25, (1.125 - x) / 0.25), 0, 1)
    for f in chd: pad += env * tone(f)
pulse = np.zeros(n); beat = 60 / 100
HL = int(0.04 * SR); hat = np.random.default_rng(1).standard_normal(HL) * np.exp(-np.arange(HL) / SR * 90)
for k in range(int(TOTAL / beat)):
    i = int(k * beat * SR); L = int(0.25 * SR)
    seg = np.sin(2 * np.pi * 55 * np.arange(L) / SR) * np.exp(-np.arange(L) / SR * 14)
    pulse[i:i + L] += seg[: max(0, min(L, n - i))]
    j = int((k + 0.5) * beat * SR); pulse[j:j + HL] += 0.25 * hat[: max(0, min(HL, n - j))]
music = pad / np.max(np.abs(pad)) * 0.09 + pulse * 0.07
sfx = np.zeros(n)
def add(sig, at):
    i = int(at * SR); L = min(len(sig), n - i)
    if L > 0 and i >= 0: sfx[i:i + L] += sig[:L]
for si, sc in enumerate(SCENES):
    a, b = spans[si]
    L = int(0.35 * SR); x = np.arange(L) / SR
    wn = np.random.default_rng(si).standard_normal(L)
    add(np.convolve(wn, np.ones(30) / 30, "same") * np.sin(np.pi * x / x[-1]) * 0.25, a - 0.12)
    if sc.get("sfx") == "boom":
        L = int(1.2 * SR); x = np.arange(L) / SR; f = 70 * np.exp(-x * 2.5) + 35
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 3) * 0.55, a)
    if sc.get("sfx") == "riser":
        L = int(1.4 * SR); x = np.arange(L) / SR; f = 200 + 900 * (x / x[-1]) ** 2
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * (x / x[-1]) ** 2 * 0.07, b - 1.4)
fade = np.clip(np.minimum(tt / 0.6, (TOTAL - tt) / 1.2), 0, 1)
mix = (music + sfx) * fade; mix[: len(voice)] += voice
mix /= max(1.0, np.max(np.abs(mix)) / 0.97)
WAV = os.path.join(WORK, "mix.wav"); sf.write(WAV, mix, SR)

# ---------- 3. drawing ----------
SYMS = set("✔✘↔⇒↑")
def ctext(d, xy, s, f, fill):
    if not any(c in SYMS for c in s):
        d.text(xy, s, font=f, fill=fill, anchor="mm"); return
    fb = ImageFont.truetype(DJ, f.size); parts = [(c, fb if c in SYMS else f) for c in s]
    x = xy[0] - sum(d.textlength(c, font=ff) for c, ff in parts) / 2
    for c, ff in parts:
        d.text((x, xy[1]), c, font=ff, fill=fill, anchor="lm"); x += d.textlength(c, font=ff)
def box(d, xy, outline=YEL, fill=PANEL, w=6, r=24): d.rounded_rectangle(xy, r, fill=fill, outline=outline, width=w)
def arrow(d, a, b, col=YEL, w=8):
    d.line([a, b], fill=col, width=w); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6): d.line([b, (b[0] + 32 * math.cos(ang + s), b[1] + 32 * math.sin(ang + s))], fill=col, width=w)
def key(d, x, y, label, col=YEL):
    d.ellipse((x - 46, y - 46, x + 46, y + 46), outline=col, width=10)
    d.line([(x + 46, y), (x + 180, y)], fill=col, width=12)
    for dx in (130, 162): d.line([(x + dx, y), (x + dx, y + 36)], fill=col, width=12)
    ctext(d, (x, y), label, LBL, col)
def card(d, cx, cy, title, sub, col=YEL, w=360, h=210):
    box(d, (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), outline=col)
    ctext(d, (cx, cy - 28), title, LBL, col); ctext(d, (cx, cy + 44), sub, LBL_S, DIM)
def seal(d, cx, cy, ok=True, r=95):
    col = GREEN if ok else RED
    pts = [(cx + (r if i % 2 == 0 else r * 0.84) * math.cos(i * math.pi / 12),
            cy + (r if i % 2 == 0 else r * 0.84) * math.sin(i * math.pi / 12)) for i in range(24)]
    d.polygon(pts, outline=col, fill=PANEL, width=7)
    ctext(d, (cx, cy), "✔" if ok else "✘", ImageFont.truetype(DJ, int(r * 0.9)), col)

BITS = "1 0 1 1  0 1 1 0  1 0 0 "
BITX = 140 + int(MONO.getlength(BITS))

def elements(sid):
    if sid == "hook":
        return [(0, lambda d: card(d, 540, 520, "1 ciphertext", "encrypted file", YEL, 460)),
                ("keys", lambda d: (key(d, 150, 760, "A"), key(d, 720, 760, "B"))),
                ("completely", lambda d: (card(d, 270, 1010, "FILE A", "harmless", GREEN, 400),
                                          card(d, 810, 1010, "FILE B", "malicious", RED, 400))),
                ("genuine", lambda d: (seal(d, 270, 1240, True, 70), seal(d, 810, 1240, True, 70)))]
    if sid == "question":
        return [(0, lambda d: ctext(d, (540, 780), "?", font("Inter-Bold.otf", 420), YEL)),
                ("supposed", lambda d: ctext(d, (540, 1130), "how it's SUPPOSED to work", LBL, WHITE))]
    if sid == "gcm":
        return [(0, lambda d: (ctext(d, (540, 420), "AES-GCM", TITLE, YEL),
                               ctext(d, (540, 500), "authenticated encryption", LBL_S, DIM))),
                ("tls", lambda d: (box(d, (290, 560, 790, 660), outline=DIM), ctext(d, (540, 610), "TLS  →  HTTPS", LBL, WHITE))),
                ("scrambles", lambda d: (box(d, (40, 740, 380, 880), outline=WHITE), ctext(d, (210, 810), "plaintext", LBL, WHITE),
                                         arrow(d, (390, 810), (500, 810)), ctext(d, (445, 890), "key", LBL_S, YEL),
                                         box(d, (515, 740, 840, 880)), ctext(d, (677, 810), "ciphertext", LBL, YEL))),
                ("tag", lambda d: (box(d, (855, 740, 1040, 880), fill=(60, 50, 10)), ctext(d, (947, 810), "TAG", LBL, YEL))),
                ("seal", lambda d: (seal(d, 540, 1090), ctext(d, (540, 1250), "only the key holder can make it", LBL_S, DIM)))]
    if sid == "flip":
        return [(0, lambda d: (box(d, (100, 440, 980, 560), outline=DIM), d.text((140, 474), BITS + "1", font=MONO, fill=WHITE))),
                ("bit", lambda d: (d.rectangle((BITX - 8, 458, BITX + 36, 545), fill=(70, 20, 20), outline=RED, width=4),
                                   d.text((BITX, 474), "0", font=MONO, fill=RED), ctext(d, (540, 620), "↑ one bit flipped", LBL_S, RED))),
                ("breaks", lambda d: seal(d, 540, 800, False)),
                ("rule", lambda d: (box(d, (90, 980, 990, 1200)), ctext(d, (540, 1040), "THE RULE WE TRUST", LBL_S, DIM),
                                    ctext(d, (540, 1125), "valid seal ⇒ message is real", LBL, YEL)))]
    if sid == "twist":
        return [(0, lambda d: (ctext(d, (540, 420), "the seal stops", LBL_S, DIM),
                               ctext(d, (540, 490), "outsiders without the key ✔", LBL, GREEN))),
                ("never", lambda d: (ctext(d, (540, 620), "1 ciphertext ↔ 1 key?", LBL, WHITE),
                                     ctext(d, (540, 690), "✘ never promised", LBL, RED))),
                ("commitment", lambda d: (box(d, (70, 800, 1010, 1130)), ctext(d, (540, 870), "KEY COMMITMENT", TITLE, YEL),
                                          ctext(d, (540, 970), "a ciphertext decrypts correctly", LBL_S, WHITE),
                                          ctext(d, (540, 1030), "under only ONE key", LBL_S, WHITE))),
                ("doesnt", lambda d: ctext(d, (540, 1230), "AES-GCM: ✘ NOT key-committing", LBL, RED))]
    if sid == "split":
        return [(0, lambda d: (key(d, 120, 450, "A"), key(d, 660, 450, "B"))),
                ("craft", lambda d: (box(d, (170, 580, 910, 720)), ctext(d, (540, 650), "ONE ciphertext + seal", LBL, YEL))),
                ("valid", lambda d: (arrow(d, (420, 730), (270, 860)), arrow(d, (660, 730), (810, 860)))),
                ("a", lambda d: seal(d, 270, 940, True, 60)),
                ("b", lambda d: seal(d, 810, 940, True, 60)),
                ("harmless", lambda d: card(d, 270, 1150, "harmless", "via key A", GREEN, 420)),
                ("malicious", lambda d: card(d, 810, 1150, "malicious", "via key B", RED, 420))]
    if sid == "formats":
        return [(0, lambda d: ctext(d, (540, 450), "NOT THEORY", TITLE, YEL)),
                ("2022", lambda d: ctext(d, (540, 560), "USENIX Security 2022 · Albertini et al.", LBL_S, DIM)),
                ("pdfs", lambda d: card(d, 200, 820, "PDF", "document", WHITE, 300, 190)),
                ("programs", lambda d: card(d, 540, 820, "EXE", "Windows", WHITE, 300, 190)),
                ("medical", lambda d: card(d, 880, 820, "DICOM", "medical", WHITE, 300, 190)),
                ("medical", lambda d: ctext(d, (540, 1020), "1 AES-GCM ciphertext → 2 valid files", LBL_S, YEL))]
    if sid == "stakes":
        return [(0, lambda d: (box(d, (120, 560, 960, 800)), ctext(d, (540, 640), "ciphertext", LBL, YEL),
                               ctext(d, (540, 720), "used as EVIDENCE", LBL, WHITE))),
                ("abuse", lambda d: (box(d, (300, 900, 780, 1010), outline=RED), ctext(d, (540, 955), "ABUSE REPORT", LBL, RED)))]
    if sid == "incident":
        return [(0, lambda d: (box(d, (270, 380, 810, 1260), outline=DIM, r=56), ctext(d, (540, 450), "Messenger · 2018", LBL_S, DIM))),
                ("abusive", lambda d: (box(d, (330, 540, 750, 820), outline=RED), ctext(d, (540, 680), "abusive image", LBL_S, RED))),
                ("report", lambda d: (box(d, (340, 900, 740, 1010), outline=WHITE), ctext(d, (540, 955), "Report ✘", LBL, RED))),
                ("bounty", lambda d: ctext(d, (540, 1140), "bug bounty paid", LBL_S, YEL))]
    if sid == "fix":
        return [(0, lambda d: (box(d, (90, 520, 990, 700), outline=GREEN), ctext(d, (540, 610), "✔ key-committing AEAD", LBL, GREEN))),
                ("follow", lambda d: (ctext(d, (540, 900), "FOLLOW", BIG, YEL), ctext(d, (540, 1020), "for more hidden gems", LBL, WHITE)))]
    return []

def glow_layer(fn):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay)); bb = lay.getbbox()
    if not bb: return None
    p = 44; bb = (max(bb[0] - p, 0), max(bb[1] - p, 0), min(bb[2] + p, W), min(bb[3] + p, H))
    crop = lay.crop(bb); g = np.array(crop.filter(ImageFilter.GaussianBlur(16)))
    g[..., 3] = (g[..., 3] * 0.9).astype(np.uint8)
    return Image.alpha_composite(Image.fromarray(g), crop), bb[:2]

BASE = Image.new("RGB", (W, H), BG); _d = ImageDraw.Draw(BASE)
for x in range(0, W, 60): _d.line([(x, 0), (x, H)], fill=GRID)
for y in range(0, H, 60): _d.line([(0, y), (W, y)], fill=GRID)

ELEMS, SHAKES = [], []
for si, sc in enumerate(SCENES):
    sw = [w for w in words if w["scene"] == si]; pos = 0
    for trig, fn in elements(sc["id"]):
        if trig != 0:
            j = next((k for k in range(pos, len(sw)) if sw[k]["c"].startswith(trig)), None)
            if j is None: raise SystemExit(f"trigger {trig!r} not found in scene {sc['id']}")
            pos = j
        g = glow_layer(fn)
        if g: ELEMS.append((si, sw[pos]["start"] if trig != 0 else spans[si][0], g[0], g[1]))
    if sc.get("sfx") == "boom": SHAKES.append(spans[si][0])

chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w)
    last = i == len(words) - 1 or words[i + 1]["scene"] != w["scene"]
    if len(cur) == 3 or w["pause"] or re.search(r"[,.?!:]$", w["text"]) or last:
        chunks.append(cur); cur = []

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def render(fi):
    t = fi / FPS
    si = next((i for i, (a, b) in enumerate(spans) if t < b), len(SCENES) - 1)
    a, b = spans[si]
    im = BASE.copy()
    for (s, ta, lay, pos) in ELEMS:
        if s != si or t < ta: continue
        k = ease((t - ta) / 0.3); scl = 0.85 + 0.15 * k
        l2 = lay if k >= 1 else lay.resize((max(1, int(lay.width * scl)), max(1, int(lay.height * scl))))
        if k < 1:
            al = np.array(l2); al[..., 3] = (al[..., 3] * k).astype(np.uint8); l2 = Image.fromarray(al)
        im.paste(l2, (pos[0] + (lay.width - l2.width) // 2, pos[1] + (lay.height - l2.height) // 2), l2)
    z = 1 + 0.035 * min(1, (t - a) / max(b - a, 0.1))          # slow push-in
    cw, chh = int(W / z), int(H / z)
    im = im.crop(((W - cw) // 2, (H - chh) // 2, (W - cw) // 2 + cw, (H - chh) // 2 + chh)).resize((W, H))
    for st in SHAKES:                                           # shake on boom
        if 0 <= t - st < 0.35:
            amp = 14 * (1 - (t - st) / 0.35)
            im = Image.fromarray(np.roll(np.roll(np.array(im), int(amp * math.sin(t * 90)), 1), int(amp * math.cos(t * 77)), 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, int(W * t / TOTAL), 10), fill=YEL)      # progress bar
    ch = next((c for c in chunks if c[0]["start"] - 0.05 <= t < c[-1]["end"] + 0.2), None)
    if ch:
        texts = [w["text"].upper() for w in ch]; widths = [d.textlength(s + " ", font=CAP) for s in texts]
        lines, line, lw = [], [], 0
        for w, s, wd in zip(ch, texts, widths):
            if lw + wd > 980 and line: lines.append(line); line, lw = [], 0
            line.append((w, s, wd)); lw += wd
        lines.append(line); y = 1440
        for line in lines:
            x = (W - sum(wd for *_, wd in line)) / 2
            for w, s, wd in line:
                if t >= w["start"] - 0.05:
                    pop = ease((t - w["start"] + 0.05) / 0.12)
                    d.text((x, y + int(12 * (1 - pop))), s, font=CAP, fill=YEL if w["key"] else WHITE,
                           stroke_width=7, stroke_fill=(0, 0, 0))
                x += wd
            y += 108
    return im.tobytes()

if __name__ == "__main__":
    nf = int(TOTAL * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", WAV, "-c:v", "libx264",
                           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac",
                           "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for buf in p.imap(render, range(nf), chunksize=16): ff.stdin.write(buf)
    ff.stdin.close(); ff.wait(); print("done", OUT, nf)
