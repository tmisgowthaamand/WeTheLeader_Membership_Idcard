"""
Add LABELS ONLY (no values) onto front.png
Labels: Name, EPIC No, Assembly, District
Placed to the right of the black photo frame.
Reads from front_original.png, writes to front.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, 'front_original.png')   # always read from clean original
OUTPUT     = os.path.join(BASE_DIR, 'front.png')

# ── Open original ─────────────────────────────────────────────────
img  = Image.open(INPUT_PATH).convert('RGB')
W, H = img.size          # 1575 x 998
draw = ImageDraw.Draw(img)

# ── Font loader ───────────────────────────────────────────────────
def load_font(size, bold=False):
    paths = (
        ['C:/Windows/Fonts/arialbd.ttf']
        if bold else
        ['C:/Windows/Fonts/arial.ttf']
    )
    for p in paths:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def text_w(txt, font):
    bb = draw.textbbox((0, 0), txt, font=font)
    return bb[2] - bb[0]

def text_h(txt, font):
    bb = draw.textbbox((0, 0), txt, font=font)
    return bb[3] - bb[1]

# ── Font sizes ────────────────────────────────────────────────────
F_LBL = int(H * 0.042)    # label size (~42px at 998h) — larger & bold
f_lbl = load_font(F_LBL, bold=True)

LABEL_CLR = (20, 20, 20)   # near-black — clearly visible

# ── Labels only (no sample values) ───────────────────────────────
LABELS = ["Name", "EPIC No", "Assembly", "District"]

# ── Horizontal layout ─────────────────────────────────────────────
# Black frame right edge ~34% of width; shift labels a bit left (~31%)
FRAME_RIGHT_X   = int(W * 0.31)    # shifted left to give name more room
GAP_AFTER_FRAME = int(W * 0.015)   # ~24px gap after frame

FIELD_X   = FRAME_RIGHT_X + GAP_AFTER_FRAME   # label starts here
COLON_GAP = 10
max_lbl_w = max(text_w(lbl, f_lbl) for lbl in LABELS)
COLON_X   = FIELD_X + max_lbl_w + COLON_GAP   # colon aligned for all rows

# ── Vertical layout ───────────────────────────────────────────────
# Frame vertical span ~22%–74% of height
FRAME_TOP = int(H * 0.22)
FRAME_BOT = int(H * 0.74)

row_h    = text_h("Ag", f_lbl)
ROW_GAP  = int(H * 0.060)          # spacing between rows
ROW_STEP = row_h + ROW_GAP
block_h  = len(LABELS) * ROW_STEP - ROW_GAP

# vertically centre within frame span
block_top = FRAME_TOP + (FRAME_BOT - FRAME_TOP - block_h) // 2

# ── Draw labels + colons only ─────────────────────────────────────
for i, label in enumerate(LABELS):
    y = block_top + i * ROW_STEP

    # Label text
    draw.text((FIELD_X, y), label, font=f_lbl, fill=LABEL_CLR)

    # Colon — vertically centred with label
    col_y = y + (row_h - text_h(":", f_lbl)) // 2
    draw.text((COLON_X, col_y), ":", font=f_lbl, fill=LABEL_CLR)

# ── Save ──────────────────────────────────────────────────────────
img.save(OUTPUT, format='PNG', optimize=True)
print(f"Saved: {OUTPUT}  ({W}x{H})")
print(f"Labels at x={FIELD_X}, colon at x={COLON_X}")
print("Labels placed (no values):", LABELS)
