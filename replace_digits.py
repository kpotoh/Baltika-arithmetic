#!/usr/bin/env python3
# coding: utf-8
"""
Replace digits found in an input image with custom beer bottle images.

Uses a pretrained EasyOCR model for digit/text detection and the custom
digit images from the pics/ directory as replacements.

Usage:
    python replace_digits.py INPUT_IMAGE [-o OUTPUT_IMAGE] [--pics_dir DIR]
"""

import os
import argparse
import numpy as np
from PIL import Image
import easyocr


PICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pics')


def load_custom_digits(pics_dir):
    """Load custom digit images (0-9) from the pics directory."""
    digits = {}
    for i in range(10):
        path = os.path.join(pics_dir, '{}.png'.format(i))
        if not os.path.exists(path):
            raise FileNotFoundError(
                'Custom digit image not found: {}'.format(path)
            )
        digits[str(i)] = Image.open(path).convert('RGBA')
    return digits


def replace_digits_in_image(input_path, output_path, pics_dir=PICS_DIR):
    """
    Detect digits in input_path using EasyOCR and replace them with
    custom beer bottle images from pics_dir, saving the result to output_path.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError('Input image not found: {}'.format(input_path))

    # Initialise EasyOCR reader with English (covers digit detection)
    reader = easyocr.Reader(['en'], gpu=False)

    # Open the input image; work in RGBA so transparent overlays paste cleanly
    img = Image.open(input_path).convert('RGBA')

    # Run text detection on a numpy array of the image
    results = reader.readtext(np.array(img))

    # Load the custom digit replacement images
    custom_digits = load_custom_digits(pics_dir)

    for bbox, text, confidence in results:
        # Skip regions that contain no digit characters
        if not any(c.isdigit() for c in text):
            continue

        # bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] going clockwise
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x_min = int(min(xs))
        y_min = int(min(ys))
        x_max = int(max(xs))
        y_max = int(max(ys))

        region_width = max(x_max - x_min, 1)
        region_height = max(y_max - y_min, 1)

        # Estimate each character's width by dividing the region evenly
        char_count = max(len(text), 1)
        char_width = region_width // char_count

        for char_index, c in enumerate(text):
            if not c.isdigit():
                continue

            # Horizontal slice for this character inside the detected region
            slot_x_min = x_min + char_index * char_width
            slot_width = char_width

            # Resize the custom image to fit the slot while keeping aspect ratio
            custom_img = custom_digits[c].copy()
            aspect = custom_img.size[0] / custom_img.size[1]
            target_h = region_height
            target_w = int(target_h * aspect)
            if target_w > slot_width:
                target_w = slot_width
                target_h = max(int(target_w / aspect), 1)
            target_w = max(target_w, 1)

            custom_img = custom_img.resize((target_w, target_h), Image.LANCZOS)

            # Centre the resized image within the character's slot
            paste_x = slot_x_min + (slot_width - target_w) // 2
            paste_y = y_min + (region_height - target_h) // 2

            # Paste using the alpha channel as a mask
            img.paste(custom_img, (paste_x, paste_y), custom_img)

    # Save result with high quality: prefer PNG (lossless) or, for JPEG,
    # use a high quality and disable chroma subsampling to avoid compression artifacts.
    output_dir = os.path.dirname(os.path.abspath(output_path))
    if not os.path.isdir(output_dir):
        raise OSError('Output directory does not exist: {}'.format(output_dir))

    ext = os.path.splitext(output_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        img_rgb = img.convert('RGB')
        img_rgb.save(
            output_path,
            format='JPEG',
            quality=95,
            subsampling=0,
            optimize=True,
        )
    else:
        # Default to PNG which is lossless
        img.save(output_path, format='PNG', optimize=True)

    print('Result saved to {}'.format(output_path))


def main():
    parser = argparse.ArgumentParser(
        description='Replace digits in an image with custom beer bottle images.'
    )
    parser.add_argument('input', help='Path to the input image')
    parser.add_argument(
        '-o', '--output',
        help='Path for the output image (default: <input>_replaced.<ext>)',
        default=None,
    )
    parser.add_argument(
        '--pics_dir',
        help='Directory containing custom digit images 0.png–9.png',
        default=PICS_DIR,
    )
    args = parser.parse_args()

    if args.output is None:
        base, ext = os.path.splitext(args.input)
        args.output = '{}_replaced{}'.format(base, ext if ext else '.png')

    replace_digits_in_image(args.input, args.output, args.pics_dir)


if __name__ == '__main__':
    main()
