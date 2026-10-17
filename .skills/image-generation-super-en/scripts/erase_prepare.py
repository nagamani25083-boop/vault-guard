#!/usr/bin/env python3
"""
Step 1 of the erase workflow (LOCAL ONLY, no network calls).

Preprocess the original image with its erase mask so that the image-edit model
sees exactly which area to repaint: the mask's WHITE region is painted over with
a flat sentinel color on a copy of the original, so the object/person/text to
erase is physically gone before the model ever sees the image.

Outputs the prepared image plus the exact English prompt and size to pass to
generate_image.py, whose output is the final deliverable. The prepared image is
an intermediate artifact only — by default it is written to a system temp
directory so it never shows up in the user's working directory.

Usage:
    python3 erase_prepare.py --image photo.png --mask photo_mask.png
    python3 erase_prepare.py --image photo.png --mask photo_mask.png \
        --extra-prompt "the red trash bin on the left" --grow 6

Exit codes:
    0 - success, prints one JSON line
    1 - file or argument error
"""

import os
import sys
import json
import tempfile
import argparse

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("Pillow is required. Install it with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# Magenta is uncommon in natural photos and clearly marks the fill region.
SENTINEL_FILL = (255, 0, 255)

SUPPORTED_SIZES = ("1024x1024", "1536x1024", "1024x1536", "2848x1152")

PROMPT_TEMPLATE = (
    "This is an inpainting task. The input image contains one solid magenta (RGB 255,0,255) patch. "
    "Return the same image with only that magenta patch replaced. "
    "Fill the patch by continuing the surface it sits on: match that surface's color, texture, "
    "lighting, shadow direction, grain and perspective, and extend only the lines, edges or patterns "
    "that already pass through the patch, so the patch disappears and nothing new takes its "
    "place.{extra} "
    "Everything outside the patch is a strict copy task: reproduce it as-is. "
    "Keep every other text block, number, table, list, logo, icon, label, illustration and graphic "
    "exactly where it is, at the same size, wording and color. Do not delete, move, resize, "
    "re-typeset, re-align or redraw any of them, even if they look decorative, repetitive or "
    "unimportant, and even if removing them would look cleaner. "
    "Do not add any new object, person, animal, text, logo, watermark or decorative pattern. "
    "Do not restyle, re-render, re-light, crop, zoom, mirror, or add a border. "
    "No magenta may remain in the output. "
    "high quality, detailed, photorealistic"
)


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(description="Preprocess an image + erase mask before calling generate_image.py.")
    p.add_argument("--image", required=True, help="Original image path")
    p.add_argument("--mask", required=True, help="Mask path: white means erase and black means preserve")
    p.add_argument("--workdir", default="",
                   help="Intermediate output directory; defaults to a temporary directory")
    p.add_argument("--extra-prompt", default="", help="Optional English description of the erased object")
    p.add_argument("--grow", type=int, default=2,
                   help="Pixels to grow the erase region (default 2; 0 disables growth)")
    p.add_argument("--threshold", type=int, default=128,
                   help="Mask threshold; grayscale above it is erase area (default 128)")
    p.add_argument("--size", default="",
                   help="Upstream output size; auto-selects the closest supported aspect ratio")
    return p.parse_args()


def fail(message):
    """Print an error and exit nonzero."""
    print(message, file=sys.stderr)
    sys.exit(1)


def load_mask(mask_path, size, threshold, grow):
    """Read and normalize the mask to a binary L image matching the source size (255=erase)."""
    mask = Image.open(mask_path)
    mask.load()
    # Treat transparent mask pixels as black (preserve).
    if mask.mode in ("RGBA", "LA"):
        background = Image.new("RGBA", mask.size, (0, 0, 0, 255))
        mask = Image.alpha_composite(background, mask.convert("RGBA"))
    mask = mask.convert("L")

    if mask.size != size:
        mask = mask.resize(size, Image.NEAREST)

    mask = mask.point(lambda v: 255 if v > threshold else 0, mode="L")

    if grow > 0:
        # MaxFilter requires an odd kernel; grow pixels map to 2*grow+1.
        mask = mask.filter(ImageFilter.MaxFilter(2 * grow + 1))

    return mask


def pick_size(width, height, explicit):
    """Choose an upstream size; explicit size takes precedence."""
    if explicit:
        return explicit
    ratio = width / height if height else 1.0
    return min(
        SUPPORTED_SIZES,
        key=lambda s: abs((int(s.split("x")[0]) / int(s.split("x")[1])) - ratio),
    )


def main():
    """Create the prepared image and erase prompt for generate_image.py."""
    args = parse_args()

    if not os.path.isfile(args.image):
        fail(f"Image not found: {args.image}")
    if not os.path.isfile(args.mask):
        fail(f"Mask not found: {args.mask}")

    original = Image.open(args.image)
    original.load()
    if original.mode not in ("RGB", "RGBA"):
        original = original.convert("RGB")

    mask = load_mask(args.mask, original.size, args.threshold, args.grow)
    white_pixels = sum(mask.histogram()[1:])
    if white_pixels == 0:
        fail("Mask has no white region — nothing to erase. Check the mask polarity "
             "(white = erase, black = keep).")
    if white_pixels == original.width * original.height:
        fail("Mask is fully white — the whole image would be erased. Check the mask polarity "
             "(white = erase, black = keep).")

    # Prepared intermediates stay in a temporary directory.
    if args.workdir:
        workdir = args.workdir
        os.makedirs(workdir, exist_ok=True)
    else:
        workdir = tempfile.mkdtemp(prefix="erase_")
    stem = os.path.splitext(os.path.basename(args.image))[0]

    # Fill the erase region with the sentinel color so the model only fills the gap.
    prepared = original.copy()
    fill = Image.new(original.mode, original.size,
                     SENTINEL_FILL + ((255,) if original.mode == "RGBA" else ()))
    prepared.paste(fill, (0, 0), mask)
    prepared_path = os.path.join(workdir, f"{stem}_prepared.png")
    prepared.save(prepared_path)

    extra = f" The content removed from that area was: {args.extra_prompt}." if args.extra_prompt else ""
    prompt = PROMPT_TEMPLATE.format(extra=extra)

    print(json.dumps({
        "prepared_image": prepared_path,
        "prompt": prompt,
        "size": pick_size(original.width, original.height, args.size),
        "erase_pixels": white_pixels,
        "original_size": f"{original.width}x{original.height}",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
