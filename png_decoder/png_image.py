from zlib import decompress

from .chunks import IHDR, PLTE, IDAT
from .utils import bytes_to_int


class PNGImage:
    def __init__(self, filepath):
        self.filepath = filepath
        self.signature = None
        self.chunks = []

        self.ihdr: IHDR | None = None

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
                case b"IHDR":
                    self.ihdr = IHDR(chunk_data)
                case b"PLTE":
                    self.plte = PLTE(chunk_data)
                case b"IDAT":
                    self.data_chunks.append(IDAT(chunk_data))
                    self.data += chunk_data["data"]

        self.parse_data()

    def parse_data(self):
        if not self.ihdr:
            print("[ERROR] IHDR not present!")
            return
        
        # Step1: Decompress the data
        deflated: bytes = b''
        match self.ihdr.compression_method:
            case 0:
                deflated = decompress(self.data)
            case _:
                print("[ERROR] Unknown Compression Type defined")
                return
            
        print(deflated)

        # Step2: Undo the Filtering
        
        

    def _is_eof(self, fh) -> bool:
        current = fh.tell()
        fh.seek(0, 2)
        end = fh.tell()
        fh.seek(current)

        return current >= end
