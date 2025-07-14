from png_decoder import PNGImage


def main():
    filepath = "images/barrierRed.png"

    img = PNGImage(filepath)
    is_valid = img.validate_sign()

    if is_valid:
        img.parse_chunks()
        
        # print(img.pixels)


if __name__ == "__main__":
    main()
