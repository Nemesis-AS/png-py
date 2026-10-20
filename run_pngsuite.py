from pathlib import Path

from PIL import Image

from png_decoder import PNGDecodeError, PNGImage

PNGSUITE_DIR = Path("images/pngsuite")


def get_reference_pixels(filepath: Path, bit_depth: int) -> list:
    im = Image.open(filepath)
    transparency = im.info.get("transparency")

    if im.mode == "I;16":
        return [
            (value >> 8, value >> 8, value >> 8, 0 if value == transparency else 255)
            for value in im.getdata()
        ]

    if im.mode == "L" and isinstance(transparency, int) and bit_depth < 8:
        scaled_transparency = (transparency * 255) // ((1 << bit_depth) - 1)
        return [
            (value, value, value, 0 if value == scaled_transparency else 255)
            for value in im.getdata()
        ]

    return list(im.convert("RGBA").getdata())


def run_image(filepath: Path) -> bool:
    is_corrupt = filepath.name.startswith("x")

    img = PNGImage(str(filepath))
    if not img.validate_sign():
        return is_corrupt

    try:
        img.parse_chunks()
    except PNGDecodeError:
        return is_corrupt

    if is_corrupt or not img.ihdr:
        return False

    return img.pixels == get_reference_pixels(filepath, img.ihdr.bit_depth)


def main():
    passed = 0
    failed = 0

    for filepath in sorted(PNGSUITE_DIR.glob("*.png")):
        try:
            result = run_image(filepath)
        except Exception:
            result = False

        if result:
            passed += 1
        else:
            failed += 1

        print(f"{'PASS' if result else 'FAIL'}  {filepath.name}")

    print()
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")


if __name__ == "__main__":
    main()
