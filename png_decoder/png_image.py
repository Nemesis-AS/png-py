from zlib import decompress
from math import ceil

from .chunks import IHDR, PLTE, IDAT, tRNS
from .utils import bytes_to_int, paeth_filter


class PNGImage:
    def __init__(self, filepath):
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

            # for chunk in self.chunks:
            #     print("Chunk Type: ", chunk["type"])
            #     print("Chunk Size: ", chunk["size"])

            #     if chunk["type"] != b'IDAT':
            #         print("Chunk Data: ", chunk["data"])
            #     print("")

        for chunk_data in self.chunks:
            match chunk_data["type"]:
                # Critical Chunks
                case b"IHDR":
                    self.ihdr = IHDR(chunk_data)
                case b"PLTE":
                    self.plte = PLTE(chunk_data)
                case b"IDAT":
                    self.data_chunks.append(IDAT(chunk_data))
                    self.data += chunk_data["data"]
                
                # Ancillary Chunks
                case b"tRNS":
                    self.tRNS = tRNS(chunk_data)

        self.parse_data()

    def parse_data(self):
        if not self.ihdr:
            print("[ERROR] IHDR not present!")
            return
        
        if self.ihdr.color_type == 3 and not self.plte:
            print("[ERROR] Missing palette Chunk!")
            return
        
        # Add Transparencies to Palette if tRNS chunk is present
        if self.tRNS and self.plte:
            self.plte.add_transparency_from_tRNS(self.tRNS)

        # Step1: Decompress the data
        deflated: bytes = b''
        match self.ihdr.compression_method:
            case 0:
                deflated = decompress(self.data)
            case _:
                print("[ERROR] Unknown Compression Type defined")
                return

        # Step2: Undo the Filtering
        self.bits_per_pixel: int = 0
        match self.ihdr.color_type:
            case 0: # Greyscale (R=G=B)
                self.bits_per_pixel = self.ihdr.bit_depth
            case 2: # TrueColor (RGB)
                self.bits_per_pixel = self.ihdr.bit_depth * 3
            case 3: # Indexed Color
                self.bits_per_pixel = self.ihdr.bit_depth
            case 4: # Greyscale with alpha
                self.bits_per_pixel = self.ihdr.bit_depth * 2
            case 6: # TrueColor with alpha
                self.bits_per_pixel = self.ihdr.bit_depth * 4
            case _:
                self.bits_per_pixel = 0
        
        if self.bits_per_pixel == 0:
            print("[ERROR] Invalid Color Type")
            return

        # print("Bits per pixel: ", self.bits_per_pixel)
        # print("Deflated length: ", len(deflated))


        bytes_per_pixel = ceil(self.bits_per_pixel / 8)
        # print("Bytes per pixel: ", bytes_per_pixel)

        
        offset_b = -(self.ihdr.width + 1) * bytes_per_pixel # Offset for the top/up pixel
        offset_c = offset_b - 1 # Offset for the top left pixel

        scanline_width = self.ihdr.width + 1

        decoded_bytes = [0 for _ in range(len(deflated))]

        current_filter = -1
        for idx in range(len(deflated)):
            # The scanline filter type byte would have an index of type nx, where x is the scanline_width and n is any natural number
            if idx % scanline_width == 0:
                current_filter = deflated[idx]
                continue
            
            match current_filter:
                case 0: # None Filter
                    decoded_bytes[idx] = deflated[idx]
                case 1: # Sub Filter
                    recon_a = decoded_bytes[idx - 1] if idx % scanline_width > 1 else 0
                    decoded_bytes[idx] = deflated[idx] + recon_a
                case 2: # Up Filter
                    recon_b = decoded_bytes[idx - offset_b] if idx // scanline_width > 0 else 0
                    decoded_bytes[idx] = deflated[idx] + recon_b
                case 3: # Average Filter
                    recon_a = decoded_bytes[idx - 1] if idx % scanline_width > 1 else 0
                    recon_b = decoded_bytes[idx - offset_b] if idx // scanline_width > 0 else 0
                    decoded_bytes[idx] = deflated[idx] + ((recon_a + recon_b) // 2)
                case 4: # Paeth Filter
                    recon_a = decoded_bytes[idx - 1] if idx % scanline_width > 1 else 0
                    recon_b = decoded_bytes[idx - offset_b] if idx // scanline_width > 0 else 0
                    recon_c = decoded_bytes[idx - offset_c] if idx % scanline_width > 1 and idx // scanline_width > 0 else 0
                    decoded_bytes[idx] = paeth_filter(recon_a, recon_b, recon_c)
                case _:
                    print("[ERROR] Unknown filter type!")
    
        # Since the length of the decoded bytes is same as the deflated data, 
        # we need to remove the bytes that contained the filter type
        for idx in range((self.ihdr.height - 1) * scanline_width, -1, -scanline_width):
            decoded_bytes.pop(idx)

        # Step3: Reconstruct decoded bytes into pixels
        pixels = [(0, 0, 0, 0) for _ in range(self.ihdr.width * self.ihdr.height)]
        MAX_ALPHA = 255

        match self.ihdr.color_type:
            case 0: # Greyscale (R=G=B)
                for idx in range(len(decoded_bytes)):
                    byte = decoded_bytes[idx]
                    pixels[idx] = (byte, byte, byte, MAX_ALPHA)
            case 2: # TrueColor (RGB)
                for idx in range(0, len(decoded_bytes), bytes_per_pixel):
                    pixels[idx] = (decoded_bytes[idx], decoded_bytes[idx + 1], decoded_bytes[idx + 2], MAX_ALPHA)
            case 3: # Indexed Color
                # This is already handled above, but needs to be added due to type checking
                if not self.plte:
                    print("[ERROR] Missing palette Chunk!")
                    return

                for idx in range(0, len(decoded_bytes), bytes_per_pixel):
                    color = self.plte.colors[decoded_bytes[idx]]
                    alpha = color[3] if len(color) == 4 else MAX_ALPHA

                    pixels[idx] = (color[0], color[1], color[2], alpha)
            case 4: # Greyscale with alpha
                for idx in range(0, len(decoded_bytes), bytes_per_pixel):
                    pixels[idx] = (decoded_bytes[idx], decoded_bytes[idx], decoded_bytes[idx], decoded_bytes[idx + 1])
            case 6: # TrueColor with alpha
                for idx in range(0, len(decoded_bytes), bytes_per_pixel):
                    pixels[idx] = (decoded_bytes[idx], decoded_bytes[idx + 1], decoded_bytes[idx + 2], decoded_bytes[idx + 3])
            case _:
                self.bits_per_pixel = 0
        
        self.pixels = pixels

    def _is_eof(self, fh) -> bool:
        current = fh.tell()
        fh.seek(0, 2)
        end = fh.tell()
        fh.seek(current)

        return current >= end
