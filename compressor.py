import zlib

# Implement compressor class
class Compressor:
    def __init__(self):
        pass

    def compress(self, data):
        return zlib.compress(data)

    def decompress(self, data):
        return zlib.decompress(data)
