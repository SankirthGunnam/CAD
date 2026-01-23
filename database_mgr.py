AUTHOR = "sankirth gunnam"
VERSION = "1.0"
LICENSE = "MIT"
PROJECT_NAME = "BCF Database Manager"
DESCRIPTION = "Secure binary storage with metadata"
ORGANIZATION = "Open Source"
TAGS = "database, security, bcf"

import struct
import pickle
import os
import json
import datetime
import platform
from compressor import Compressor
from encrypter import Encrypter

class DatabaseMgr:
    def __init__(self):
        # Use __dict__ to avoid recursion during initialization
        self.__dict__['data'] = {}
        self.__dict__['compressor'] = Compressor()
        self.__dict__['encrypter'] = Encrypter()
        self.header_format = "1024s"

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
        # Construct metadata lines for readability
        metadata_lines = [
            f"AUTHOR: {AUTHOR}",
            f"VERSION: {VERSION}",
            f"LICENSE: {LICENSE}",
            f"PROJECT: {PROJECT_NAME}",
            f"DESC: {DESCRIPTION}",
            f"ORG: {ORGANIZATION}",
            f"TAGS: {TAGS}",
            f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"OS: {platform.system()}",
            f"ENC: Fernet"
        ]
        
        # Combine into a single string with newlines
        metadata_text = "\n".join(metadata_lines) + "\n"
        
        # Pad with spaces to exactly 1024 bytes to keep it readable in text editors
        # Null bytes (\x00) often make editors think the file is purely binary
        header_bytes = metadata_text.encode('utf-8')
        if len(header_bytes) < 1024:
            header_bytes = header_bytes + b' ' * (1024 - len(header_bytes))
        else:
            header_bytes = header_bytes[:1024]
        
        # Serialize data before compression
        serialized_data = pickle.dumps(self.data)
        compressed_data = self.compressor.compress(serialized_data)
        encrypted_data = self.encrypter.encrypt(compressed_data)
        
        with open("database.mcf", "wb") as f:
            f.write(header_bytes)
            f.write(encrypted_data)

    def load(self):
        if not os.path.exists("database.mcf"):
            return

        with open("database.mcf", "rb") as f:
            header_bytes = f.read(1024)
            encrypted_data = f.read()

        metadata_raw = header_bytes.decode("utf-8").strip()
        
        print('Metadata Loaded:')
        for line in metadata_raw.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                print(f'  {key.strip().title()}: {val.strip()}')

        if encrypted_data:
            compressed_data = self.encrypter.decrypt(encrypted_data)
            serialized_data = self.compressor.decompress(compressed_data)
            self.__dict__['data'] = pickle.loads(serialized_data)

    @staticmethod 
    def get_header(path: str):
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                header_bytes = f.read(1024)
                if not header_bytes: return None
                metadata_raw = header_bytes.decode("utf-8").strip()
                meta_dict = {}
                for line in metadata_raw.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        meta_dict[key.strip().lower()] = val.strip()
                return meta_dict
        except:
            return None


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
