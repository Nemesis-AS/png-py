from math import ceil
from zlib import crc32, decompress
from zlib import error as zliberror

from .chunks import IDAT, IHDR, PLTE, tRNS
from .png_error import PNGDecodeError
from .utils import bytes_to_int, paeth_filter, scale_sample


class PNGImage:
    def __init__(self, filepath, debug=False):
        self.filepath = filepath
        self.signature = None
        self.chunks = []

        self.ihdr: IHDR | None = None
        self.plte: PLTE | None = None

        # Ancillary Chunks
        self.tRNS: tRNS | None = None

        self.PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10]

        self.data_chunks = []
        self.data: bytes = b""

        self.color_data = []

        # For debugging purposes
        self.debug = debug

    def validate_sign(self) -> bool:
        with open(self.filepath, "rb") as fh:
            sign = fh.read(8)
            self.signature = sign

            for idx in range(len(self.PNG_SIGNATURE)):
                if self.signature[idx] != self.PNG_SIGNATURE[idx]:
                    return False

            return True
        return False

    def parse_chunks(self):
        with open(self.filepath, "rb") as fh:
            fh.read(8)  # Seek through the PNG Signature

            while not self._is_eof(fh):
                chunk_size = bytes_to_int(fh.read(4))
                chunk_type = fh.read(4)
                chunk_data = fh.read(chunk_size)
                chunk_crc = fh.read(4)

                if crc32(chunk_type + chunk_data) != bytes_to_int(chunk_crc):
                    raise PNGDecodeError(f"CRC mismatch in {chunk_type.decode('latin-1')} chunk")

                self.chunks.append(
                    {
                        "size": chunk_size,
                        "type": chunk_type,
                        "data": chunk_data,
                        "crc": chunk_crc,
                    }
                )

                if chunk_type == b"IEND":
                    # print("End of Image reached!")
                    break

            if self.debug:
                for chunk in self.chunks:
                    print("Chunk Type: ", chunk["type"])
                    print("Chunk Size: ", chunk["size"])

                    if chunk["type"] != b"IDAT":
                        print("Chunk Data: ", chunk["data"])

        for chunk_data in self.chunks:
            match chunk_data["type"]:
                # Critical Chunks
                case b"IHDR":
                    self.ihdr = IHDR(chunk_data)
                    if self.debug:
                        print("[Width]:", self.ihdr.width)
                        print("[Height]:", self.ihdr.height)
                        print("[Bit Depth]:", self.ihdr.bit_depth)
                        print("[Color Type]:", self.ihdr.color_type)
                        print("[Compression Method]:", self.ihdr.compression_method)
                        print("[Filter Method]:", self.ihdr.filter_method)
                        print("[Interlace Method]:", self.ihdr.interlace_method)
                case b"PLTE":
                    self.plte = PLTE(chunk_data)
                    if self.debug:
                        print("[PLTE]:", len(self.plte.colors), "colors")
                case b"IDAT":
                    self.data_chunks.append(IDAT(chunk_data))
                    self.data += chunk_data["data"]

                # Ancillary Chunks
                case b"tRNS":
                    self.tRNS = tRNS(chunk_data)
                    if self.debug:
                        print("[tRNS]:", len(self.tRNS.transparencies), "colors")

        self.parse_data()

    def parse_data(self):
        if not self.ihdr:
            raise PNGDecodeError("IHDR not present")

        VALID_BIT_DEPTHS = {
            0: [1, 2, 4, 8, 16],
            2: [8, 16],
            3: [1, 2, 4, 8],
            4: [8, 16],
            6: [8, 16],
        }

        if self.ihdr.color_type not in VALID_BIT_DEPTHS:
            raise PNGDecodeError(f"Invalid Color Type: {self.ihdr.color_type}")

        if self.ihdr.bit_depth not in VALID_BIT_DEPTHS[self.ihdr.color_type]:
            raise PNGDecodeError(
                f"Invalid Bit Depth {self.ihdr.bit_depth} for Color Type {self.ihdr.color_type}"
            )

        if self.ihdr.color_type == 3 and not self.plte:
            raise PNGDecodeError("Missing palette Chunk")

        # Add Transparencies to Palette if tRNS chunk is present
        if self.tRNS and self.plte and self.ihdr.color_type == 3:
            self.plte.add_transparency_from_tRNS(self.tRNS)

        # Step1: Decompress the data
        deflated: bytes = b""
        match self.ihdr.compression_method:
            case 0:
                try:
                    deflated = decompress(self.data)
                except zliberror as e:
                    raise PNGDecodeError("An error occurred while decompressing the IHDR chunk") from e
            case _:
                raise PNGDecodeError("[ERROR] Unknown Compression Type defined")

        # Step2: Undo the Filtering
        self.bits_per_pixel: int = 0
        match self.ihdr.color_type:
            case 0:  # Greyscale (R=G=B)
                self.bits_per_pixel = self.ihdr.bit_depth
            case 2:  # TrueColor (RGB)
                self.bits_per_pixel = self.ihdr.bit_depth * 3
            case 3:  # Indexed Color
                self.bits_per_pixel = self.ihdr.bit_depth
            case 4:  # Greyscale with alpha
                self.bits_per_pixel = self.ihdr.bit_depth * 2
            case 6:  # TrueColor with alpha
                self.bits_per_pixel = self.ihdr.bit_depth * 4

        bytes_per_pixel = ceil(self.bits_per_pixel / 8)

        if self.debug:
            print("Bits per pixel: ", self.bits_per_pixel)
            print("Deflated length: ", len(deflated))
            print("Bytes per pixel: ", bytes_per_pixel)

        scanline_bytes = ceil((self.ihdr.width * self.bits_per_pixel) / 8) + 1
        decoded_bytes = [0 for _ in range(len(deflated))]

        current_filter = -1
        for idx in range(len(deflated)):
            # The scanline filter type byte would have an index of type nx, where x is the scanline_width and n is any natural number
            if idx % scanline_bytes == 0:
                current_filter = deflated[idx]
                continue

            match current_filter:
                case 0:  # None Filter
                    decoded_bytes[idx] = deflated[idx] % 256
                case 1:  # Sub Filter
                    recon_a = (
                        decoded_bytes[idx - bytes_per_pixel]
                        if idx % scanline_bytes > bytes_per_pixel
                        else 0
                    )
                    decoded_bytes[idx] = (deflated[idx] + recon_a) % 256
                case 2:  # Up Filter
                    recon_b = (
                        decoded_bytes[idx - scanline_bytes]
                        if idx // scanline_bytes > 0
                        else 0
                    )
                    decoded_bytes[idx] = (deflated[idx] + recon_b) % 256
                case 3:  # Average Filter
                    recon_a = (
                        decoded_bytes[idx - bytes_per_pixel]
                        if idx % scanline_bytes > bytes_per_pixel
                        else 0
                    )
                    recon_b = (
                        decoded_bytes[idx - scanline_bytes]
                        if idx // scanline_bytes > 0
                        else 0
                    )
                    decoded_bytes[idx] = (
                        deflated[idx] + ((recon_a + recon_b) // 2)
                    ) % 256
                case 4:  # Paeth Filter
                    recon_a = (
                        decoded_bytes[idx - bytes_per_pixel]
                        if idx % scanline_bytes > bytes_per_pixel
                        else 0
                    )
                    recon_b = (
                        decoded_bytes[idx - scanline_bytes]
                        if idx // scanline_bytes > 0
                        else 0
                    )
                    recon_c = (
                        decoded_bytes[idx - scanline_bytes - bytes_per_pixel]
                        if idx % scanline_bytes > bytes_per_pixel
                        and idx // scanline_bytes > 0
                        else 0
                    )
                    decoded_bytes[idx] = (
                        deflated[idx] + paeth_filter(recon_a, recon_b, recon_c)
                    ) % 256
                case _:
                    raise PNGDecodeError(f"Unknown filter type: {current_filter}")

        # Since the length of the decoded bytes is same as the deflated data,
        # we need to remove the bytes that contained the filter type
        for idx in range((self.ihdr.height - 1) * scanline_bytes, -1, -scanline_bytes):
            decoded_bytes.pop(idx)

        # Step3: Reconstruct decoded bytes into pixels
        pixels = [(0, 0, 0, 0) for _ in range(self.ihdr.width * self.ihdr.height)]
        MAX_ALPHA = 255

        bit_depth = self.ihdr.bit_depth
        samples_per_pixel = self.bits_per_pixel // bit_depth
        samples = self._unpack_samples(self.ihdr, decoded_bytes, samples_per_pixel)
        color_key = self.tRNS.color_key if self.tRNS else None

        match self.ihdr.color_type:
            case 0:  # Greyscale (R=G=B)
                for pixel_idx in range(len(pixels)):
                    grey = samples[pixel_idx]
                    alpha = 0 if color_key == (grey,) else MAX_ALPHA
                    value = scale_sample(grey, bit_depth)

                    pixels[pixel_idx] = (value, value, value, alpha)
            case 2:  # TrueColor (RGB)
                for pixel_idx in range(len(pixels)):
                    idx = pixel_idx * samples_per_pixel
                    rgb = (samples[idx], samples[idx + 1], samples[idx + 2])
                    alpha = 0 if color_key == rgb else MAX_ALPHA

                    pixels[pixel_idx] = (
                        scale_sample(rgb[0], bit_depth),
                        scale_sample(rgb[1], bit_depth),
                        scale_sample(rgb[2], bit_depth),
                        alpha,
                    )
            case 3:  # Indexed Color
                # This is already handled above, but needs to be added due to type checking
                if not self.plte:
                    raise PNGDecodeError("Missing palette Chunk")

                for pixel_idx in range(len(pixels)):
                    color = self.plte.colors[samples[pixel_idx]]
                    alpha = color[3] if len(color) == 4 else MAX_ALPHA

                    pixels[pixel_idx] = (color[0], color[1], color[2], alpha)
            case 4:  # Greyscale with alpha
                for pixel_idx in range(len(pixels)):
                    idx = pixel_idx * samples_per_pixel
                    grey = scale_sample(samples[idx], bit_depth)

                    pixels[pixel_idx] = (
                        grey,
                        grey,
                        grey,
                        scale_sample(samples[idx + 1], bit_depth),
                    )
            case 6:  # TrueColor with alpha
                for pixel_idx in range(len(pixels)):
                    idx = pixel_idx * samples_per_pixel

                    pixels[pixel_idx] = (
                        scale_sample(samples[idx], bit_depth),
                        scale_sample(samples[idx + 1], bit_depth),
                        scale_sample(samples[idx + 2], bit_depth),
                        scale_sample(samples[idx + 3], bit_depth),
                    )

        self.pixels = pixels

    def _unpack_samples(
        self, ihdr: IHDR, decoded_bytes: list[int], samples_per_pixel: int
    ) -> list[int]:
        bit_depth = ihdr.bit_depth
        row_bytes = ceil((ihdr.width * samples_per_pixel * bit_depth) / 8)
        row_samples = ihdr.width * samples_per_pixel
        sample_mask = (1 << bit_depth) - 1

        samples = []
        for row in range(ihdr.height):
            row_start = row * row_bytes
            for sample_idx in range(row_samples):
                match bit_depth:
                    case 16:
                        idx = row_start + (sample_idx * 2)
                        samples.append(
                            (decoded_bytes[idx] << 8) | decoded_bytes[idx + 1]
                        )
                    case 8:
                        samples.append(decoded_bytes[row_start + sample_idx])
                    case _:
                        bit_offset = sample_idx * bit_depth
                        byte = decoded_bytes[row_start + (bit_offset // 8)]
                        shift = 8 - bit_depth - (bit_offset % 8)
                        samples.append((byte >> shift) & sample_mask)

        return samples

    def _is_eof(self, fh) -> bool:
        current = fh.tell()
        fh.seek(0, 2)
        end = fh.tell()
        fh.seek(current)

        return current >= end
