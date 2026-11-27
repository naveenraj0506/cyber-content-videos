"""Cover image (1080x1920 JPG) for the Invisible Salamanders Short."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
W, H = 1080, 1920
BG = (8, 15, 36); GRID = (22, 36, 70); YEL = (255, 210, 40); WHITE = (245, 247, 252)
DIM = (150, 168, 200); RED = (255, 90, 90); GREEN = (90, 225, 130); PANEL = (14, 24, 52)
F = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(F + n, s)
XB = "Inter-ExtraBold.otf"

im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=GRID)
for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=GRID)

lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
def c(xy, s, f, col): g.text(xy, s, font=f, fill=col, anchor="mm")
def box(xy, col, r=28, w=8): g.rounded_rectangle(xy, r, fill=PANEL, outline=col, width=w)

# headline
c((540, 330), "ONE FILE.", font(XB, 150), WHITE)
c((540, 490), "TWO SECRETS.", font(XB, 122), YEL)
# diagram: one ciphertext -> two files
box((240, 640, 840, 820), YEL); c((540, 730), "1 ciphertext", font("Inter-Bold.otf", 70), YEL)
for a, b in (((440, 830), (250, 1010)), ((640, 830), (830, 1010))):
    g.line([a, b], fill=YEL, width=10)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (2.6, -2.6): g.line([b, (b[0] + 40 * math.cos(ang + s), b[1] + 40 * math.sin(ang + s))], fill=YEL, width=10)
box((40, 1040, 520, 1300), RED); c((280, 1130), "SALAMANDER", font("Inter-Bold.otf", 62), RED)
c((280, 1220), "key B", font("Inter-SemiBold.otf", 46), DIM)
box((560, 1040, 1040, 1300), GREEN); c((800, 1130), "KITTEN", font("Inter-Bold.otf", 62), GREEN)
c((800, 1220), "key A", font("Inter-SemiBold.otf", 46), DIM)
c((540, 1440), "and the encryption says", font("Inter-SemiBold.otf", 52), WHITE)
c((540, 1520), "BOTH ARE REAL", font(XB, 96), YEL)
# brand
MONO = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 64)
g.polygon([(390, 1760), (414, 1736), (438, 1760), (414, 1784)], fill=YEL)
g.text((460, 1760), "0xLore", font=MONO, fill=WHITE, anchor="lm")

glow = np.array(lay.filter(ImageFilter.GaussianBlur(18))); glow[..., 3] = (glow[..., 3] * 0.8).astype(np.uint8)
im = Image.alpha_composite(Image.alpha_composite(im.convert("RGBA"), Image.fromarray(glow)), lay).convert("RGB")
im.save(OUT, quality=92)
