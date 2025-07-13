from abc import ABC, abstractmethod

from .utils import bytes_to_int


class ImageChunk(ABC):
    def __init__(self, chunk_data):
        self.size: int = chunk_data["size"]
        self.type: bytes = chunk_data["type"]
        self.data: bytes = chunk_data["data"]
        self.crc: bytes = chunk_data["crc"]

        self._initialize()

    @abstractmethod
    def _initialize(self):
        pass


class IHDR(ImageChunk):
    def _initialize(self):
        self.width = bytes_to_int(self.data[0:4])
        self.height = bytes_to_int(self.data[4:8])
        self.bit_depth = self.data[8]
        self.color_type = self.data[9]
        self.compression_method = self.data[10]
        self.filter_method = self.data[11]
        self.interlace_method = self.data[12]


class PLTE(ImageChunk):
    def _initialize(self):
        color_count = len(self.data)
        self.colors = []
        for idx in range(color_count // 3):
            red = self.data[idx * 3]
            green = self.data[(idx * 3) + 1]
            blue = self.data[(idx * 3) + 2]
            self.colors.append((red, green, blue))


class IDAT(ImageChunk):
    def _initialize(self):
        pass  # self.data is already set
