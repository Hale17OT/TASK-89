"""
Media processing service: hashing, originality checks, watermarking,
file-type validation, and EXIF metadata extraction.
"""
import hashlib
import logging
import math

from PIL import Image, ImageDraw, ImageFont, ExifTags

# Cap decompression bomb threshold before any image is opened.
Image.MAX_IMAGE_PIXELS = 25_000_000

logger = logging.getLogger("medrights.media")

# MIME types accepted by the system (matched via python-magic).
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
}


# ---------------------------------------------------------------------------
# Pixel hash
# ---------------------------------------------------------------------------

def compute_pixel_hash(file_obj) -> str:
    """
    Open the image with Pillow, load raw pixel data (stripping EXIF),
    and return the SHA-256 hex digest of Image.tobytes().

    Raises ValueError for corrupt / unreadable images.
    """
    try:
        file_obj.seek(0)
        img = Image.open(file_obj)
        img.load()  # force full decode, strips lazy loading
    except Exception as exc:
        raise ValueError(
            f"Unable to decode image file: {exc}"
        ) from exc

    # Convert to RGB to normalise colour space (handles RGBA, P, etc.)
    img = img.convert("RGB")

    pixel_data = img.tobytes()
    return hashlib.sha256(pixel_data).hexdigest()


# ---------------------------------------------------------------------------
# File hash
# ---------------------------------------------------------------------------

def compute_file_hash(file_obj) -> str:
    """Return the SHA-256 hex digest of the entire file contents."""
    file_obj.seek(0)
    h = hashlib.sha256()
    while True:
        chunk = file_obj.read(65_536)
        if not chunk:
            break
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        h.update(chunk)
    file_obj.seek(0)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Originality check
# ---------------------------------------------------------------------------

def check_originality(pixel_hash: str):
    """
    Query MediaAsset by pixel_hash.

    Returns:
        (status, matching_asset_or_None)
        - ("original", None) when no match is found
        - ("reposted", <MediaAsset>) when a match exists
    """
    from apps.media_engine.models import MediaAsset

    existing = (
        MediaAsset.objects
        .filter(pixel_hash=pixel_hash, is_deleted=False)
        .first()
    )
    if existing:
        return ("reposted", existing)
    return ("original", None)


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------

def apply_watermark(image_path: str, output_path: str, config: dict) -> str:
    """
    Burn a diagonal text watermark onto the image at *image_path* and
    write the result to *output_path*.

    config keys:
        clinic_name : str   -- text line 1
        date_stamp  : bool  -- if True, append today's date
        opacity     : float -- 0.0 .. 1.0

    Returns the output_path on success.
    """
    from datetime import date as _date

    img = Image.open(image_path).convert("RGBA")
    width, height = img.size

    # Build watermark text
    text = config.get("clinic_name", "")
    if config.get("date_stamp"):
        text += f"  {_date.today().isoformat()}"

    # Create transparent overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Attempt to load a reasonable font size; fall back to default
    font_size = max(20, min(width, height) // 20)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    # Measure text for tiling
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    if text_width == 0 or text_height == 0:
        # Nothing to draw
        img.save(output_path)
        return output_path

    # Compute opacity as an alpha value 0-255
    alpha = int(255 * max(0.0, min(1.0, config.get("opacity", 0.35))))

    # Create a single text tile rotated -45 degrees
    diagonal = int(math.sqrt(width ** 2 + height ** 2))
    txt_layer = Image.new("RGBA", (diagonal, diagonal), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_layer)

    # Tile the text across the diagonal canvas
    y = 0
    spacing_y = text_height * 3
    spacing_x = text_width + 60
    while y < diagonal:
        x = 0
        while x < diagonal:
            txt_draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha))
            x += spacing_x
        y += spacing_y

    # Rotate and crop to original size
    txt_layer = txt_layer.rotate(45, resample=Image.BICUBIC, expand=False)

    # Center-crop the rotated overlay to match original image size
    cx, cy = txt_layer.size[0] // 2, txt_layer.size[1] // 2
    left = cx - width // 2
    top = cy - height // 2
    txt_layer = txt_layer.crop((left, top, left + width, top + height))

    # Composite
    result = Image.alpha_composite(img, txt_layer)
    result = result.convert("RGB")
    result.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# File-type validation via magic bytes
# ---------------------------------------------------------------------------

def validate_file_type(file_obj) -> str:
    """
    Check magic bytes of *file_obj* using python-magic.

    Returns the detected MIME type if it is JPEG or PNG.
    Raises ValueError for anything else.
    """
    import magic

    file_obj.seek(0)
    header = file_obj.read(8192)
    file_obj.seek(0)

    detected = magic.from_buffer(header, mime=True)

    if detected not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported file type '{detected}'. Only JPEG and PNG are accepted."
        )

    return detected


# ---------------------------------------------------------------------------
# Evidence metadata extraction
# ---------------------------------------------------------------------------

def extract_evidence_metadata(file_obj) -> dict:
    """
    Extract available EXIF / image metadata into a plain dict.
    This is stored immutably at upload time.
    """
    metadata: dict = {}

    try:
        file_obj.seek(0)
        img = Image.open(file_obj)

        metadata["width"] = img.width
        metadata["height"] = img.height
        metadata["format"] = img.format
        metadata["mode"] = img.mode

        exif_data = img.getexif()
        if exif_data:
            tag_map = {v: k for k, v in ExifTags.TAGS.items()}

            for tag_name in (
                "Make",
                "Model",
                "DateTime",
                "DateTimeOriginal",
                "Software",
                "ImageWidth",
                "ImageLength",
                "ExifImageWidth",
                "ExifImageHeight",
                "Orientation",
                "XResolution",
                "YResolution",
            ):
                tag_id = tag_map.get(tag_name)
                if tag_id is not None and tag_id in exif_data:
                    value = exif_data[tag_id]
                    # Convert IFDRational / tuple to string for JSON serialisation
                    if hasattr(value, "numerator"):
                        value = float(value)
                    elif isinstance(value, bytes):
                        value = value.decode("utf-8", errors="replace")
                    elif isinstance(value, tuple):
                        value = str(value)
                    metadata[f"exif_{tag_name}"] = value

    except Exception:
        # If we cannot read metadata that is not a fatal error;
        # the image itself was already validated earlier.
        logger.debug("Could not extract EXIF metadata", exc_info=True)

    file_obj.seek(0)
    return metadata
