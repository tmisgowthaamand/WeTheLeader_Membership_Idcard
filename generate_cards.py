"""
Card Generation Engine -- We The Leaders v6.0
Front template : front1.png  (generated from data/front1.html)
Back template  : black_original.png
"""
import hashlib, logging, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import config

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

MEMBER_NAME_FONT_SIZE = 26
MEMBER_NAME_LETTER_SPACING = -0.5
MEMBER_NAME_WORD_SPACING = 2


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


def get_spaced_text_width(text: str,
                          font,
                          letter_spacing: float = 0,
                          word_spacing: float = 0) -> float:
    if not text:
        return 0
    width = sum(get_text_width(ch, font) for ch in text)
    spaces = text.count(" ")
    return width + max(0, len(text) - 1) * letter_spacing + spaces * word_spacing


def draw_spaced_text(draw: ImageDraw.ImageDraw,
                     xy: tuple[int, int],
                     text: str,
                     font,
                     fill,
                     letter_spacing: float = 0,
                     word_spacing: float = 0) -> None:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += get_text_width(ch, font) + letter_spacing + (word_spacing if ch == " " else 0)


def get_text_height(text: str, font) -> int:
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def load_member_photo(*args, **kwargs):
    return None


def format_member_name(text: str) -> str:
    text = " ".join(str(text or "").split())
    return text.upper()


def member_name_font_size(text: str) -> int:
    return MEMBER_NAME_FONT_SIZE


def generate_serial_number(epic_no: str) -> str:
    h = hashlib.md5(epic_no.encode()).hexdigest().upper()
    return f"SN-{h[:1]}{h[2:3]}{h[4:5]}{h[6:7]}{h[8:9]}{h[10:11]}{h[12:13]}"


def _fit_passport_photo(photo: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Crop to box ratio then resize to fill exactly."""
    photo = photo.convert('RGB')
    iw, ih = photo.size
    target = box_w / box_h
    if iw / ih > target:
        new_w = int(ih * target)
        left  = (iw - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, ih))
    else:
        new_h = int(iw / target)
        top   = int((ih - new_h) * 0.15)
        top   = max(0, min(top, ih - new_h))
        photo = photo.crop((0, top, iw, top + new_h))
    return photo.resize((box_w, box_h), Image.LANCZOS)


def _paste_rounded_photo(card: Image.Image,
                         photo: Image.Image,
                         box: tuple[int, int, int, int],
                         radius: int) -> None:
    box_l, box_t, box_r, box_b = box
    box_w = box_r - box_l
    box_h = box_b - box_t
    fitted = _fit_passport_photo(photo, box_w, box_h).convert("RGBA")

    mask = Image.new("L", (box_w, box_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, box_w - 1, box_h - 1],
                                radius=radius, fill=255)
    card.paste(fitted, (box_l, box_t), mask)


def _sample_card_background(card: Image.Image,
                            box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    W, H = card.size
    l, t, r, b = box
    pad = max(12, int(W * 0.010))
    samples = []
    sample_boxes = (
        (max(0, l - pad), max(0, t - pad), min(W, r + pad), max(0, t)),
        (max(0, l - pad), min(H, b), min(W, r + pad), min(H, b + pad)),
        (max(0, l - pad), max(0, t), max(0, l), min(H, b)),
        (min(W, r), max(0, t), min(W, r + pad), min(H, b)),
    )
    for sx1, sy1, sx2, sy2 in sample_boxes:
        if sx2 <= sx1 or sy2 <= sy1:
            continue
        region = card.crop((sx1, sy1, sx2, sy2)).resize((1, 1), Image.LANCZOS)
        samples.append(region.getpixel((0, 0)))
    if not samples:
        return (248, 248, 248)
    return tuple(sum(pixel[i] for pixel in samples) // len(samples) for i in range(3))


def generate_card(voter: dict,
                  template: Image.Image,
                  photo_image: Image.Image = None) -> Image.Image:
    card = template.copy().convert("RGB")
    W, H = card.size
    draw = ImageDraw.Draw(card)

    def clean(val, maxlen=120):
        s = str(val or '').strip()
        s = ''.join(c for c in s if c.isprintable())
        s = s.replace('{','').replace('}','').replace('$','').replace('\\','')
        return s[:maxlen]

    name     = format_member_name(clean(voter.get('name', '')))
    epic_no  = clean(voter.get('epic_no', '')).upper()
    assembly = clean(voter.get('assembly_name','') or voter.get('assembly','')).upper()
    district = clean(voter.get('district','') or voter.get('DISTRICT_NAME','')).upper()
    ptc_code = clean(voter.get('ptc_code', ''))

    # Draw generated text once over the cleaned front template.
    F_VAL = int(H * 0.026)
    F_WTL = int(H * 0.026)
    f_wtl = load_font(F_WTL, bold=True)
    VALUE_CLR = (10, 10, 10)
    WTL_CLR   = (0, 0, 0)

    NAME_X = int(W * 0.229)
    NAME_RIGHT = int(W * 0.675)
    MAX_NAME_W = max(1, NAME_RIGHT - NAME_X)
    MIN_SIZE = max(int(H * 0.016), 14)

    ROW_STEP = int(H * 0.102)
    block_top = int(H * 0.392)
    FIELD_TOP = block_top + ROW_STEP
    LABEL_X = NAME_X
    FIELD_RIGHT = int(W * 0.695)
    COLON_X = int(W * 0.326)
    COLON_GAP = int(W * 0.010)

    def font_to_fit(text, start_size, min_size, max_width):
        size = start_size
        font = load_font(size, bold=True)
        while size > min_size and get_text_width(text, font) > max_width:
            size -= 1
            font = load_font(size, bold=True)
        return font, size

    def name_font_to_fit(text, max_width):
        size = member_name_font_size(text)
        font = load_font(size, bold=True)
        while size > 12 and get_spaced_text_width(
            text, font, MEMBER_NAME_LETTER_SPACING, MEMBER_NAME_WORD_SPACING
        ) > max_width:
            size -= 1
            font = load_font(size, bold=True)
        return font, size

    def truncate_to_width(text, font, max_width):
        if get_text_width(text, font) <= max_width:
            return text
        suffix = "..."
        available = max_width - get_text_width(suffix, font)
        clipped = ""
        for ch in text:
            if get_text_width(clipped + ch, font) > available:
                break
            clipped += ch
        return (clipped.rstrip() + suffix) if clipped else suffix

    name_font, name_size = name_font_to_fit(name, MAX_NAME_W)
    draw_spaced_text(draw, (NAME_X, block_top), name, font=name_font,
                     fill=(0, 0, 0),
                     letter_spacing=MEMBER_NAME_LETTER_SPACING,
                     word_spacing=MEMBER_NAME_WORD_SPACING)

    field_font = load_font(F_VAL, bold=True)
    field_rows = (
        ("EPIC NO", epic_no),
        ("ASSEMBLY", assembly),
        ("DISTRICT", district),
    )

    for row_index, (label, value) in enumerate(field_rows):
        y = FIELD_TOP + row_index * ROW_STEP
        value_x = COLON_X + get_text_width(":", field_font) + COLON_GAP
        max_value_w = max(1, FIELD_RIGHT - value_x)
        value_font, value_size = font_to_fit(value, F_VAL, MIN_SIZE, max_value_w)
        value = truncate_to_width(value or "", value_font, max_value_w)

        draw.text((LABEL_X, y), label, font=field_font, fill=VALUE_CLR)
        draw.text((COLON_X, y), ":", font=field_font, fill=VALUE_CLR)
        draw.text((value_x, y), value, font=value_font, fill=VALUE_CLR)

    # Clear the baked-in placeholder avatar while keeping the new rounded frame area.
    old_frame_l = int(W * 0.0525)
    old_frame_t = int(H * 0.3090)
    old_frame_r = int(W * 0.2130)
    old_frame_b = int(H * 0.7290)
    clear_box = (old_frame_l - 8, old_frame_t - 8, old_frame_r + 8, old_frame_b + 8)
    draw.rounded_rectangle(
        clear_box,
        radius=max(8, int(W * 0.012)),
        fill=_sample_card_background(card, clear_box)
    )

    old_frame_w = old_frame_r - old_frame_l
    old_frame_h = old_frame_b - old_frame_t
    photo_scale = 0.74
    frame_w = int(old_frame_w * photo_scale)
    frame_h = int(old_frame_h * photo_scale)
    frame_l = old_frame_l + (old_frame_w - frame_w) // 2
    frame_t = old_frame_t + (old_frame_h - frame_h) // 2
    frame_r = frame_l + frame_w
    frame_b = frame_t + frame_h
    radius = max(14, int(W * 0.0140))
    border_w = max(2, int(W * 0.0016))
    border_clr = (150, 150, 150)

    PHOTO_L = frame_l + border_w
    PHOTO_T = frame_t + border_w
    PHOTO_R = frame_r - border_w
    PHOTO_B = frame_b - border_w

    if photo_image:
        _paste_rounded_photo(card, photo_image,
                             (PHOTO_L, PHOTO_T, PHOTO_R, PHOTO_B),
                             max(1, radius - border_w))
        draw = ImageDraw.Draw(card)

    draw.rounded_rectangle([frame_l, frame_t, frame_r, frame_b],
                           radius=radius, outline=border_clr, width=border_w)

    # WTL code below photo frame
    if ptc_code:
        wtl_h   = get_text_height(ptc_code, f_wtl)
        wtl_gap = int(wtl_h * 1.2)
        wtl_y   = PHOTO_B + border_w + wtl_gap
        wtl_x   = PHOTO_L
        draw.text((wtl_x, wtl_y), ptc_code, font=f_wtl, fill=WTL_CLR)

    return card.convert('RGB')


def generate_back_card(voter: dict = None) -> Image.Image:
    back_path = getattr(config, 'BACK_TEMPLATE_PATH',
                        os.path.join(config.BASE_DIR, 'black_original.png'))
    if os.path.exists(back_path):
        return Image.open(back_path).convert('RGB')
    return Image.new('RGB', (1536, 1024), (255, 255, 255))


def generate_combined_card(front: Image.Image,
                            back: Image.Image,
                            gap: int = 30) -> Image.Image:
    fw, fh   = front.size
    back_eq  = back.resize((fw, fh), Image.LANCZOS)
    canvas_w = fw + gap + fw
    canvas   = Image.new('RGB', (canvas_w, fh), (255, 255, 255))
    canvas.paste(front,   (0,        0))
    canvas.paste(back_eq, (fw + gap, 0))
    return canvas
