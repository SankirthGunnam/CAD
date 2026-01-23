AUTHOR = "sankirth gunnam"
VERSION = "1.0"
LICENSE = "MIT"

import struct
import pickle
import os
from compressor import Compressor
from encrypter import Encrypter

class DatabaseMgr:
    def __init__(self):
        # Use __dict__ to avoid recursion during initialization
        self.__dict__['data'] = {}
        self.__dict__['compressor'] = Compressor()
        self.__dict__['encrypter'] = Encrypter()

    def __setattr__(self, name, value):
        self.data[name] = value

    def __getattr__(self, name):
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'DatabaseMgr' object has no attribute '{name}'")

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def save(self):
        # 3 strings of 64 bytes each = 192 bytes header
        header_format = "64s64s64s"
        # Metadata values must be encoded to bytes for struct.pack
        author_b = AUTHOR.encode('utf-8')
        version_b = VERSION.encode('utf-8')
        license_b = LICENSE.encode('utf-8')
        
        meta_b = struct.pack(header_format, author_b, version_b, license_b)
        
        # Serialize data before compression
        serialized_data = pickle.dumps(self.data)
        compressed_data = self.compressor.compress(serialized_data)
        encrypted_data = self.encrypter.encrypt(compressed_data)
        
        with open("database.bin", "wb") as f:
            f.write(meta_b)
            f.write(encrypted_data)

    def load(self):
        if not os.path.exists("database.bin"):
            return

        header_size = struct.calcsize("64s64s64s")
        with open("database.bin", "rb") as f:
            meta_b = f.read(header_size)
            encrypted_data = f.read()

        author, version, license = struct.unpack("64s64s64s", meta_b)
        
        def decode_meta(b):
            return b.decode("utf-8").rstrip('\x00')

        print('Metadata Loaded:')
        print(f'  Author: {decode_meta(author)}')
        print(f'  Version: {decode_meta(version)}')
        print(f'  License: {decode_meta(license)}')

        if encrypted_data:
            compressed_data = self.encrypter.decrypt(encrypted_data)
            serialized_data = self.compressor.decompress(compressed_data)
            self.__dict__['data'] = pickle.loads(serialized_data)

    
class App:
    def __init__(self):
        self.db = DatabaseMgr()
        self.db.load()
    
    def run(self):
        while True:
            try:
                line = input('Enter key and value (or "quit" to exit): ')
                if line.lower() == 'quit':
                    break
                parts = line.split()
                if len(parts) != 2:
                    print("Please enter exactly a key and a value.")
                    continue
                key, value = parts
                self.db[key] = value
                if input('Do you want to continue? (y/n): ').lower() != 'y':
                    break
            except EOFError:
                break
        
        self.db.save()

if __name__ == '__main__':
    app = App()
    app.run()

