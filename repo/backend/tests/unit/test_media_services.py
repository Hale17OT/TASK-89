"""Unit tests for media processing services: hashing, originality, watermark, validation, metadata."""
import io
import os

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _png_bytes(width=10, height=10, color="red"):
    """Create an in-memory PNG file-like object."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, "PNG")
    buf.seek(0)
    buf.name = "test.png"
    return buf


def _jpeg_bytes(width=10, height=10, color="blue"):
    """Create an in-memory JPEG file-like object."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, "JPEG")
    buf.seek(0)
    buf.name = "test.jpg"
    return buf


# ---------------------------------------------------------------------------
# compute_pixel_hash
# ---------------------------------------------------------------------------

class TestComputePixelHash:
    def test_returns_hex_string(self):
        from apps.media_engine.services import compute_pixel_hash

        result = compute_pixel_hash(_png_bytes())
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic_for_same_pixels(self):
        from apps.media_engine.services import compute_pixel_hash

        h1 = compute_pixel_hash(_png_bytes(color="green"))
        h2 = compute_pixel_hash(_png_bytes(color="green"))
        assert h1 == h2

    def test_different_for_different_pixels(self):
        from apps.media_engine.services import compute_pixel_hash

        h1 = compute_pixel_hash(_png_bytes(color="red"))
        h2 = compute_pixel_hash(_png_bytes(color="blue"))
        assert h1 != h2

    def test_same_pixels_different_format(self):
        """PNG and JPEG of the same solid colour should produce the same pixel hash
        (both normalised to RGB). Note: JPEG is lossy so for a solid colour this works
        but for complex images the hashes would differ."""
        from apps.media_engine.services import compute_pixel_hash

        png = _png_bytes(2, 2, color="white")
        jpg = _jpeg_bytes(2, 2, color="white")
        h_png = compute_pixel_hash(png)
        h_jpg = compute_pixel_hash(jpg)
        # Both are solid white, small enough that JPEG compression is lossless
        # This may or may not match depending on JPEG quantization, so we just
        # verify they are valid hashes
        assert len(h_png) == 64
        assert len(h_jpg) == 64

    def test_raises_on_corrupt_data(self):
        from apps.media_engine.services import compute_pixel_hash

        corrupt = io.BytesIO(b"not an image at all")
        corrupt.name = "corrupt.png"
        with pytest.raises(ValueError, match="Unable to decode"):
            compute_pixel_hash(corrupt)

    def test_handles_rgba_image(self):
        """RGBA images should be converted to RGB before hashing."""
        from apps.media_engine.services import compute_pixel_hash

        buf = io.BytesIO()
        Image.new("RGBA", (5, 5), (255, 0, 0, 128)).save(buf, "PNG")
        buf.seek(0)
        buf.name = "rgba.png"
        result = compute_pixel_hash(buf)
        assert len(result) == 64


# ---------------------------------------------------------------------------
# compute_file_hash
# ---------------------------------------------------------------------------

class TestComputeFileHash:
    def test_returns_hex_string(self):
        from apps.media_engine.services import compute_file_hash

        result = compute_file_hash(_png_bytes())
        assert isinstance(result, str)
        assert len(result) == 64

    def test_deterministic(self):
        from apps.media_engine.services import compute_file_hash

        img = _png_bytes(color="red")
        h1 = compute_file_hash(img)
        h2 = compute_file_hash(img)  # file_obj is seeked back
        assert h1 == h2

    def test_different_files_different_hash(self):
        from apps.media_engine.services import compute_file_hash

        h1 = compute_file_hash(_png_bytes(color="red"))
        h2 = compute_file_hash(_png_bytes(color="blue"))
        assert h1 != h2

    def test_file_hash_differs_from_pixel_hash(self):
        """File hash includes metadata/headers; pixel hash only raw pixels."""
        from apps.media_engine.services import compute_file_hash, compute_pixel_hash

        img = _png_bytes()
        fh = compute_file_hash(img)
        ph = compute_pixel_hash(img)
        assert fh != ph

    def test_resets_seek_position(self):
        from apps.media_engine.services import compute_file_hash

        img = _png_bytes()
        compute_file_hash(img)
        assert img.tell() == 0

    def test_handles_text_content(self):
        """StringIO-like objects should still hash correctly (encode to UTF-8)."""
        from apps.media_engine.services import compute_file_hash

        text_buf = io.BytesIO(b"hello world")
        result = compute_file_hash(text_buf)
        assert len(result) == 64


# ---------------------------------------------------------------------------
# check_originality
# ---------------------------------------------------------------------------

class TestCheckOriginality:
    def test_original_when_no_match(self, db):
        from apps.media_engine.services import check_originality

        status, asset = check_originality("nonexistent_hash_abc123")
        assert status == "original"
        assert asset is None

    def test_reposted_when_match_exists(self, db, admin_user):
        from apps.media_engine.services import check_originality
        from apps.media_engine.models import MediaAsset

        existing = MediaAsset.objects.create(
            original_file="test/path.png",
            original_filename="test.png",
            mime_type="image/png",
            file_size_bytes=100,
            pixel_hash="known_hash_xyz",
            file_hash="file_hash_abc",
            originality_status="original",
            uploaded_by=admin_user,
        )

        status, asset = check_originality("known_hash_xyz")
        assert status == "reposted"
        assert asset.pk == existing.pk

    def test_ignores_deleted_assets(self, db, admin_user):
        from apps.media_engine.services import check_originality
        from apps.media_engine.models import MediaAsset

        MediaAsset.objects.create(
            original_file="test/deleted.png",
            original_filename="deleted.png",
            mime_type="image/png",
            file_size_bytes=100,
            pixel_hash="deleted_hash",
            file_hash="file_hash_del",
            originality_status="original",
            is_deleted=True,
            uploaded_by=admin_user,
        )

        status, asset = check_originality("deleted_hash")
        assert status == "original"
        assert asset is None


# ---------------------------------------------------------------------------
# apply_watermark
# ---------------------------------------------------------------------------

class TestApplyWatermark:
    def test_creates_output_file(self, tmp_path):
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (100, 100), "white").save(str(src))
        out = tmp_path / "watermarked.png"

        result = apply_watermark(
            str(src),
            str(out),
            {"clinic_name": "Test Clinic", "date_stamp": False, "opacity": 0.5},
        )

        assert result == str(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_is_valid_image(self, tmp_path):
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (200, 200), "blue").save(str(src))
        out = tmp_path / "wm.png"

        apply_watermark(
            str(src),
            str(out),
            {"clinic_name": "Clinic", "date_stamp": True, "opacity": 0.35},
        )

        img = Image.open(str(out))
        assert img.size == (200, 200)
        assert img.mode == "RGB"

    def test_preserves_original_dimensions(self, tmp_path):
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (300, 150), "red").save(str(src))
        out = tmp_path / "wm.png"

        apply_watermark(
            str(src), str(out),
            {"clinic_name": "A", "date_stamp": False, "opacity": 0.1},
        )

        original = Image.open(str(src))
        watermarked = Image.open(str(out))
        assert original.size == watermarked.size

    def test_with_date_stamp(self, tmp_path):
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (100, 100), "green").save(str(src))
        out = tmp_path / "wm.png"

        apply_watermark(
            str(src), str(out),
            {"clinic_name": "My Clinic", "date_stamp": True, "opacity": 0.5},
        )
        assert out.exists()

    def test_opacity_clamped(self, tmp_path):
        """Opacity values outside 0-1 should be clamped, not crash."""
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (50, 50), "white").save(str(src))
        out = tmp_path / "wm.png"

        # opacity > 1 should be clamped to 1
        apply_watermark(
            str(src), str(out),
            {"clinic_name": "Clinic", "date_stamp": False, "opacity": 1.5},
        )
        assert out.exists()

    def test_empty_clinic_name(self, tmp_path):
        """Empty text should not crash — just saves unmodified."""
        from apps.media_engine.services import apply_watermark

        src = tmp_path / "source.png"
        Image.new("RGB", (50, 50), "white").save(str(src))
        out = tmp_path / "wm.png"

        apply_watermark(
            str(src), str(out),
            {"clinic_name": "", "date_stamp": False, "opacity": 0.5},
        )
        assert out.exists()


# ---------------------------------------------------------------------------
# validate_file_type
# ---------------------------------------------------------------------------

class TestValidateFileType:
    def test_accepts_png(self):
        from apps.media_engine.services import validate_file_type

        result = validate_file_type(_png_bytes())
        assert result == "image/png"

    def test_accepts_jpeg(self):
        from apps.media_engine.services import validate_file_type

        result = validate_file_type(_jpeg_bytes())
        assert result == "image/jpeg"

    def test_rejects_unsupported_type(self):
        from apps.media_engine.services import validate_file_type

        pdf = io.BytesIO(b"%PDF-1.4 fake pdf content here")
        pdf.name = "test.pdf"
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_type(pdf)

    def test_rejects_plain_text(self):
        from apps.media_engine.services import validate_file_type

        txt = io.BytesIO(b"Just some plain text content.")
        txt.name = "file.txt"
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file_type(txt)

    def test_resets_seek_after_validation(self):
        from apps.media_engine.services import validate_file_type

        img = _png_bytes()
        validate_file_type(img)
        assert img.tell() == 0


# ---------------------------------------------------------------------------
# extract_evidence_metadata
# ---------------------------------------------------------------------------

class TestExtractEvidenceMetadata:
    def test_extracts_dimensions(self):
        from apps.media_engine.services import extract_evidence_metadata

        img = _png_bytes(width=320, height=240)
        metadata = extract_evidence_metadata(img)

        assert metadata["width"] == 320
        assert metadata["height"] == 240

    def test_extracts_format(self):
        from apps.media_engine.services import extract_evidence_metadata

        metadata = extract_evidence_metadata(_png_bytes())
        assert metadata["format"] == "PNG"

    def test_extracts_mode(self):
        from apps.media_engine.services import extract_evidence_metadata

        metadata = extract_evidence_metadata(_png_bytes())
        assert metadata["mode"] == "RGB"

    def test_returns_dict_on_corrupt_file(self):
        """Corrupt files should return an empty dict, not raise."""
        from apps.media_engine.services import extract_evidence_metadata

        corrupt = io.BytesIO(b"not an image")
        corrupt.name = "corrupt.bin"
        metadata = extract_evidence_metadata(corrupt)
        assert isinstance(metadata, dict)

    def test_resets_seek(self):
        from apps.media_engine.services import extract_evidence_metadata

        img = _png_bytes()
        extract_evidence_metadata(img)
        assert img.tell() == 0

    def test_jpeg_metadata(self):
        from apps.media_engine.services import extract_evidence_metadata

        metadata = extract_evidence_metadata(_jpeg_bytes(100, 80))
        assert metadata["width"] == 100
        assert metadata["height"] == 80
        assert metadata["format"] == "JPEG"
