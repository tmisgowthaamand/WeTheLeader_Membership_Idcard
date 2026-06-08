"""
Card Generation Engine — We The Leaders v6.0
=============================================
Front template : front.png  (1575x998)
  - Labels (Name, EPIC No, Assembly, District) are pre-baked into the template
  - Values are drawn to the RIGHT of the colons at runtime
  - Passport photo is pasted into the black frame (left side)
Back template  : black.png  (1536x1024)
"""
import hashlib, logging, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import config

# ── Logging ───────────────────────────────────────────────────────
def setup_logging():
    logger = logging.getLogger('card_generator')
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)
    return logger

logger = setup_logging()


# ── Font utilities ────────────────────────────────────────────────
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = (
        getattr(config, 'FONT_BOLD_PATHS', ['C:/Windows/Fonts/arialbd.ttf'])
        if bold else
        getattr(config, 'FONT_PATHS', ['C:/Windows/Fonts/arial.ttf'])
    )
    for path in paths:
        if path and os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def load_bold_font(size: int) -> ImageFont.FreeTypeFont:
    return load_font(size, bold=True)


def get_text_width(text: str, font) -> int:
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def get_text_height(text: str, font) -> int:
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def load_member_photo(*args, **kwargs):
    """Stub kept for API compatibility."""
    return None


def generate_serial_number(epic_no: str) -> str:
    h = hashlib.md5(epic_no.encode()).hexdigest().upper()
    return f"SN-{h[:1]}{h[2:3]}{h[4:5]}{h[6:7]}{h[8:9]}{h[10:11]}{h[12:13]}"


# ── Passport photo helper ─────────────────────────────────────────
def _fit_passport_photo(photo: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """
    Crop & resize photo to exactly box_w x box_h.
    Enforces 3:4 ratio crop first (face centred, slight top bias),
    then resizes to the target box.
    """
    photo = photo.convert('RGB')
    img_w, img_h = photo.size

    # Step 1 — crop source to 3:4 ratio (face centred, top-biased)
    target_ratio = 3 / 4
    src_ratio    = img_w / img_h
    if src_ratio > target_ratio:
        # Too wide — crop sides
        new_w = int(img_h * target_ratio)
        left  = (img_w - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, img_h))
    else:
        # Too tall — crop bottom (keep head at top)
        new_h = int(img_w / target_ratio)
        top   = int((img_h - new_h) * 0.15)   # slight top bias to keep face
        top   = max(0, min(top, img_h - new_h))
        photo = photo.crop((0, top, img_w, top + new_h))

    # Step 2 — resize to exact box
    return photo.resize((box_w, box_h), Image.LANCZOS)


# ══════════════════════════════════════════════════════════════════
#  FRONT CARD GENERATOR
# ══════════════════════════════════════════════════════════════════

def generate_card(voter: dict,
                  template: Image.Image,
                  photo_image: Image.Image = None) -> Image.Image:
    """
    Generate the FRONT membership ID card using front.png as template.

    front.png already has the labels (Name, EPIC No, Assembly, District)
    baked in. This function:
      1. Pastes the passport photo into the black frame (left side)
      2. Draws the voter values to the right of the pre-baked colons

    Args:
        voter       – dict with epic_no, name, assembly_name, district, ptc_code
        template    – PIL Image of front.png
        photo_image – PIL Image (passport photo, optional)

    Returns: PIL RGB Image
    """
    card = template.copy().convert("RGB")
    W, H = card.size          # 1575 x 998
    draw = ImageDraw.Draw(card)

    # ── Sanitize input ────────────────────────────────────────────
    def clean(val, maxlen=120):
        s = str(val or '').strip()
        s = ''.join(c for c in s if c.isprintable())
        s = s.replace('{','').replace('}','').replace('$','').replace('\\','')
        return s[:maxlen]

    name     = clean(voter.get('name', '')).upper()
    epic_no  = clean(voter.get('epic_no', '')).upper()
    assembly = clean(voter.get('assembly_name','') or voter.get('assembly','')).upper()
    district = clean(voter.get('district','') or voter.get('DISTRICT_NAME','')).upper()
    ptc_code = clean(voter.get('ptc_code', ''))

    # ── Fonts ─────────────────────────────────────────────────────
    F_LBL = int(H * 0.042)
    F_WTL = int(H * 0.030)

    f_val = load_font(F_LBL, bold=True)
    f_wtl = load_font(F_WTL, bold=True)

    VALUE_CLR = (5,  5,  5)
    WTL_CLR   = (0,  0,  0)

    # ── Layout ────────────────────────────────────────────────────
    LABELS    = ["Name", "EPIC No", "Assembly", "District"]
    FIELD_X   = int(W * 0.31) + int(W * 0.015)
    max_lbl_w = max(get_text_width(lbl, f_val) for lbl in LABELS)
    COLON_X   = FIELD_X + max_lbl_w + 10
    VALUE_X   = COLON_X + get_text_width(": ", f_val) + 6
    MAX_VAL_W = int(W * 0.62) - VALUE_X - int(W * 0.01)

    # ── Vertical positions ────────────────────────────────────────
    FRAME_TOP = int(H * 0.22)
    FRAME_BOT = int(H * 0.74)
    row_h_ref = get_text_height("Ag", f_val)
    ROW_GAP   = int(H * 0.060)
    ROW_STEP  = row_h_ref + ROW_GAP
    block_h   = len(LABELS) * ROW_STEP - ROW_GAP
    block_top = FRAME_TOP + (FRAME_BOT - FRAME_TOP - block_h) // 2

    # ── Values ────────────────────────────────────────────────────
    VALUES = [name, epic_no, assembly, district]
    for i, value in enumerate(VALUES):
        y   = block_top + i * ROW_STEP
        fv, size = f_val, F_LBL
        while get_text_width(value, fv) > MAX_VAL_W and size > int(H * 0.024):
            size -= 1
            fv = load_font(size, bold=True)
        val_h = get_text_height(value, fv)
        val_y = y + (row_h_ref - val_h) // 2
        draw.text((VALUE_X, val_y), value, font=fv, fill=VALUE_CLR)

    # ── Passport photo — 3:4 ratio, pixel-perfect inside black frame ─
    # Frame inner box: L=86 R=467 T=257 B=759  (381×502px)
    # Force 3:4 ratio within that box — centred
    BORDER_W   = 3
    BORDER_CLR = (40, 40, 40)

    # Frame inner bounds
    F_L = int(W * 0.0546)
    F_T = int(H * 0.2575)
    F_R = int(W * 0.2965)
    F_B = int(H * 0.7605)
    F_W = F_R - F_L   # ~381px
    F_H = F_B - F_T   # ~502px

    # Compute largest 3:4 box that fits inside the frame
    if F_W * 4 <= F_H * 3:
        PHOTO_W = F_W
        PHOTO_H = (F_W * 4) // 3
    else:
        PHOTO_H = F_H
        PHOTO_W = (F_H * 3) // 4

    # Centre the 3:4 box inside the frame
    PHOTO_L = F_L + (F_W - PHOTO_W) // 2
    PHOTO_T = F_T + (F_H - PHOTO_H) // 2
    PHOTO_R = PHOTO_L + PHOTO_W
    PHOTO_B = PHOTO_T + PHOTO_H

    if photo_image:
        fitted = _fit_passport_photo(photo_image, PHOTO_W, PHOTO_H)
        card.paste(fitted, (PHOTO_L, PHOTO_T))
        draw.rectangle(
            [PHOTO_L - BORDER_W, PHOTO_T - BORDER_W,
             PHOTO_R + BORDER_W - 1, PHOTO_B + BORDER_W - 1],
            outline=BORDER_CLR, width=BORDER_W
        )

    # ── WTL code — BELOW the photo frame, 1.5x line-height gap ───
    if ptc_code:
        wtl_h = get_text_height(ptc_code, f_wtl)
        wtl_gap = int(wtl_h * 1.5)                    # 1.5x the text height
        wtl_y = PHOTO_B + BORDER_W + wtl_gap
        wtl_x = PHOTO_L                               # left-aligned to frame
        draw.text((wtl_x, wtl_y), ptc_code, font=f_wtl, fill=WTL_CLR)

    return card.convert('RGB')


# ══════════════════════════════════════════════════════════════════
#  BACK CARD GENERATOR  — same alignment as front
# ══════════════════════════════════════════════════════════════════

def generate_back_card(voter: dict = None) -> Image.Image:
    """
    Return black_original.png as-is — no text, no labels, no overlay.
    The back card is purely the static template image.
    """
    back_path = getattr(config, 'BACK_TEMPLATE_PATH',
                        os.path.join(config.BASE_DIR, 'black_original.png'))
    if os.path.exists(back_path):
        return Image.open(back_path).convert('RGB')
    return Image.new('RGB', (1536, 1024), (255, 255, 255))


# ══════════════════════════════════════════════════════════════════
#  COMBINED FRONT + BACK
# ══════════════════════════════════════════════════════════════════

def generate_combined_card(front: Image.Image,
                            back: Image.Image,
                            gap: int = 30) -> Image.Image:
    """
    Place front and back side-by-side on a white canvas.
    Both cards are resized to the SAME dimensions (front size is master)
    so left and right are perfectly equal in size and ratio.
    """
    fw, fh = front.size

    # Resize back to EXACT same width and height as front
    back_eq = back.resize((fw, fh), Image.LANCZOS)

    canvas_w = fw + gap + fw
    canvas   = Image.new('RGB', (canvas_w, fh), (255, 255, 255))
    canvas.paste(front,    (0,          0))
    canvas.paste(back_eq,  (fw + gap,   0))
    return canvas
