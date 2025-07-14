# To run this script, ensure that you have pillow installed
# If not, run the following command
# uv pip install pillow
# If you don't have uv, then install it using pip
# WINDOWS
# python -m pip install pillow
# LINUX/MACOS
# python3 -m pip install pillow

from png_decoder import PNGImage

from PIL import Image


def main():
    filepath = "images/barrierRed.png"

    img = PNGImage(filepath)
    is_valid = img.validate_sign()

    if is_valid:
        img.parse_chunks()

        if not img.ihdr:
            return

        im = Image.new("RGBA", (img.ihdr.width, img.ihdr.height), (0, 0, 0, 0))

        for idx in range(len(img.pixels)):
            y = idx // img.ihdr.width
            x = idx % img.ihdr.width

            im.putpixel((x, y), img.pixels[idx])

        im.show()


if __name__ == "__main__":
    main()
