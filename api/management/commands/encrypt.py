from django.core.management import BaseCommand

from api.common.encryption_service import EncryptionService


class Command(BaseCommand):
    help = """Generate a new key, decrypt, or encrypt data"""

    def add_arguments(self, parser):
        parser.add_argument("--mode", type=str, help="One of {encrypt, decrypt, generate}")
        parser.add_argument("--key", type=str, help="Encryption key name to use for encrypt and decrypt")
        parser.add_argument("--data", type=str, help="Data to encrypt or decrypt")

    def handle(self, *args, **options):
        handlers = {
            "encrypt": lambda: encrypt(options),
            "decrypt": lambda: decrypt(options),
            "generate": generate,
        }

        mode = options.get("mode").lower()
        handlers.get(mode)()


def generate():
    print(EncryptionService.generate_encryption_key())


def encrypt(options):
    encryption_key = options.get("key")
    encryption_service = EncryptionService(encryption_key=encryption_key)
    print("Crypted Text: " + encryption_service.encrypt(options.get("data")))


def decrypt(options):
    encryption_key = options.get("key")
    encryption_service = EncryptionService(encryption_key=encryption_key)
    print(encryption_service.decrypt(options.get("data")))
