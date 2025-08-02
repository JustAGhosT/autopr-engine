import base64
import os
from typing import bytes, str

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger(__name__)


class EnterpriseEncryptionManager:
    """Enterprise-grade encryption and key management"""

    def __init__(self, master_key: str | None = None):
        if master_key:
            self.key = self._derive_key_from_password(master_key.encode())
        else:
            self.key = Fernet.generate_key()

        self.cipher_suite = Fernet(self.key)
        logger.info("Encryption manager initialized with secure key derivation")

    def _derive_key_from_password(self, password: bytes, salt: bytes | None = None) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )

        key = base64.urlsafe_b64encode(kdf.derive(password))
        logger.debug("Key derived using PBKDF2 with 100k iterations")
        return key

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data with AES-256"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            logger.debug("Data encrypted successfully", data_length=len(data))
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            logger.debug("Data decrypted successfully")
            return decrypted_data.decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise

    def encrypt_file(self, file_path: str, output_path: str) -> None:
        """Encrypt file contents"""
        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            encrypted_data = self.cipher_suite.encrypt(file_data)

            with open(output_path, "wb") as encrypted_file:
                encrypted_file.write(encrypted_data)

            logger.info("File encrypted successfully", source=file_path, destination=output_path)
        except Exception as e:
            logger.error("File encryption failed", file_path=file_path, error=str(e))
            raise

    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> None:
        """Decrypt file contents"""
        try:
            with open(encrypted_file_path, "rb") as encrypted_file:
                encrypted_data = encrypted_file.read()

            decrypted_data = self.cipher_suite.decrypt(encrypted_data)

            with open(output_path, "wb") as file:
                file.write(decrypted_data)

            logger.info(
                "File decrypted successfully", source=encrypted_file_path, destination=output_path
            )
        except Exception as e:
            logger.error("File decryption failed", file_path=encrypted_file_path, error=str(e))
            raise
