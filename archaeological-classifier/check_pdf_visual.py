#!/usr/bin/env python3
"""Quick visual check of PDF prospetto coloring"""

import sys
from pathlib import Path

pdf_path = "/Users/enzo/.acs/reports/axe974/axe974_comprehensive_report_it.pdf"

print(f"Checking PDF: {pdf_path}")
print(f"PDF exists: {Path(pdf_path).exists()}")
print(f"PDF size: {Path(pdf_path).stat().st_size / 1024:.1f} KB")

# Try to use pdf2image if available
try:
    from pdf2image import convert_from_path
    import numpy as np
    from PIL import Image

    print("\nConverting PDF page 2 (technical drawings) to image...")
    # Page 3 is index 2 (0-indexed)
    images = convert_from_path(pdf_path, first_page=3, last_page=3)

    if len(images) > 0:
        img = images[0]
        img_array = np.array(img)

        # Check if there are significant black regions
        # Black pixels are (0, 0, 0) or very close
        grayscale = np.mean(img_array, axis=2)
        black_pixels = np.sum(grayscale < 30)  # Very dark pixels
        total_pixels = grayscale.size
        black_percentage = (black_pixels / total_pixels) * 100

        print(f"  Image size: {img.size}")
        print(f"  Black/dark pixels: {black_pixels}/{total_pixels} ({black_percentage:.2f}%)")

        if black_percentage > 20:
            print(f"  ⚠ WARNING: High percentage of black pixels detected!")
            print(f"  The prospetto interior might still be black.")
        else:
            print(f"  ✓ Looks good - low black pixel count")

        # Save a copy for manual inspection
        output_path = "/tmp/prospetto_check.png"
        img.save(output_path)
        print(f"  Saved visual check to: {output_path}")

except ImportError:
    print("\n⚠ pdf2image not available - cannot perform visual check")
    print("Install with: pip install pdf2image")
    print("\nPlease manually check:")
    print(f"  open {pdf_path}")

except Exception as e:
    print(f"\n⚠ Error during visual check: {e}")
    print("\nPlease manually check the PDF")
