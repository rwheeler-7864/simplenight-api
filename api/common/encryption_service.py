import os
import secrets
from base64 import b64encode, b64decode
from typing import Optional

# noinspection PyPackageRequirements
from Crypto.Cipher import AES
# noinspection PyPackageRequirements
from Crypto.Util import Padding
from django.core.exceptions import ImproperlyConfigured

try:
    from api.models.models import Feature
    from api.common.request_context import get_request_context
except ImproperlyConfigured:
    pass  # Ignore in tests


class EncryptionService:
    TEST_MODE_KEY = b"ABCDEFG012345678"

    def __init__(self, encryption_key=None):
        if encryption_key is not None:
            self.encryption_key = bytes.fromhex(encryption_key)
        else:
            self.encryption_key = self._get_encryption_key()

    def encrypt(self, clear_text: str) -> Optional[str]:
        if clear_text is None:
            return None

        padded_clear_text = Padding.pad(clear_text.encode("utf-8"), AES.block_size)
        return b64encode(self._get_cipher().encrypt(padded_clear_text)).decode("utf-8")

    def decrypt(self, crypt_text: str) -> Optional[str]:
        if crypt_text is None:
            return None

        clear_text = Padding.unpad(self._get_cipher().decrypt(b64decode(crypt_text)), AES.block_size)
        return clear_text.decode("utf-8")

    @staticmethod
    def generate_encryption_key():
        return secrets.token_bytes(16).hex()

    def _get_cipher(self):
        key = self.encryption_key
        return AES.new(key, AES.MODE_CBC, key)

    def _get_encryption_key(self):
        encoded_key = os.getenv("ENCRYPTION_KEY")
        if not encoded_key:
            return self.TEST_MODE_KEY

        return bytes.fromhex(encoded_key)
