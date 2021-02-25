import os
import unittest
from unittest.mock import patch

import pytest

from api.common.encryption_service import EncryptionService


class TestEncryptionService(unittest.TestCase):
    def test_generate_key(self):
        encryption_service = EncryptionService()
        encoded_key = encryption_service.generate_encryption_key()

        self.assertEqual(32, len(encoded_key))

    def test_encrypt_decrypt_test_mode(self):
        encryption_service = EncryptionService()
        clear_text = "This is a test"
        crypt_text = encryption_service.encrypt(clear_text)

        self.assertIsNot(clear_text, crypt_text)
        self.assertEqual(14, len(clear_text))

        decrypted_text = encryption_service.decrypt(crypt_text)
        self.assertEqual(clear_text, decrypted_text)

    def test_encrypt_passed_in_key(self):
        encryption_key = EncryptionService.generate_encryption_key()
        encryption_service1 = EncryptionService(encryption_key=encryption_key)
        clear_text = "This is a test"
        crypt_text = encryption_service1.encrypt(clear_text)

        encryption_service2 = EncryptionService()
        with pytest.raises(ValueError):
            encryption_service2.decrypt(crypt_text)

        self.assertEqual(clear_text, encryption_service1.decrypt(crypt_text))

    def test_encryption_key_from_env(self):
        encryption_key = EncryptionService.generate_encryption_key()
        encryption_service1 = EncryptionService(encryption_key=encryption_key)
        clear_text = "This is a test"
        crypt_text = encryption_service1.encrypt(clear_text)

        with patch.dict(os.environ, {"ENCRYPTION_KEY": encryption_key}):
            encryption_service2 = EncryptionService()
            self.assertEqual(clear_text, encryption_service2.decrypt(crypt_text))
