from cryptography.fernet import Fernet
secret_key = b"XC-O5ojdVONOnSEfvTSKq0Ib_KBFf6PCc0jAkYAgr0M="

class Encrypter:
    def __init__(self):
        self.key = secret_key
        self.cipher_suite = Fernet(self.key)

    def encrypt(self, data):
        return self.cipher_suite.encrypt(data)

    def decrypt(self, data):
        return self.cipher_suite.decrypt(data)
