import winreg
from cryptography.fernet import Fernet

class Encrypter:
    def __init__(self):
        self.registry_path = r"Software\BCFApp"
        self.value_name = "SecretKey"
        self.key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.key)

    def _get_or_create_key(self):
        try:
            # Try to open the key
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, self.value_name)
                # Fernet keys need to be bytes, registry strings are returned as strings if stored as REG_SZ
                # But we store as bytes (REG_BINARY)
                return value
        except (FileNotFoundError, OSError):
            # Key or value doesn't exist, create it
            new_key = Fernet.generate_key()
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_path) as key:
                winreg.SetValueEx(key, self.value_name, 0, winreg.REG_BINARY, new_key)
            return new_key

    def encrypt(self, data):
        return self.cipher_suite.encrypt(data)

    def decrypt(self, data):
        return self.cipher_suite.decrypt(data)



