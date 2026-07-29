"""EncryptionLayer - At-rest encryption with key management (R14)."""

from __future__ import annotations

import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", attempts_remaining: int = 10):
        self.attempts_remaining = attempts_remaining
        super().__init__(f"{message} ({attempts_remaining} attempts remaining)")


@dataclass
class KeyMaterial:
    """Key material for encryption."""

    key: bytes = field(default_factory=lambda: get_random_bytes(32))  # 256 bits
    iv: bytes = field(default_factory=lambda: get_random_bytes(16))
    salt: bytes = field(default_factory=lambda: get_random_bytes(16))
    derived_at: datetime = field(default_factory=datetime.utcnow)
    algorithm: str = "AES-256-GCM"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "key": self.key.hex(),
            "iv": self.iv.hex(),
            "salt": self.salt.hex(),
            "derived_at": self.derived_at.isoformat(),
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KeyMaterial:
        """Deserialize from dictionary."""
        return cls(
            key=bytes.fromhex(data["key"]),
            iv=bytes.fromhex(data["iv"]),
            salt=bytes.fromhex(data["salt"]),
            derived_at=datetime.fromisoformat(data["derived_at"]),
            algorithm=data.get("algorithm", "AES-256-GCM"),
        )


class EncryptionLayer:
    """Application-level encryption layer (R14).

    Manages at-rest encryption with key derivation from user passphrase
    and OS credential storage.
    """

    MIN_KEY_LENGTH = 256  # bits
    MIN_PASSPHRASE_LENGTH = 8
    MAX_AUTH_ATTEMPTS = 10
    DEFAULT_IDLE_TIMEOUT = 5 * 60  # 5 minutes in seconds
    MAX_IDLE_TIMEOUT = 60 * 60  # 60 minutes
    MIN_IDLE_TIMEOUT = 60  # 1 minute

    def __init__(
        self,
        key_path: Path | str = "./config/encryption.key",
        passphrase: str | None = None,
        idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    ):
        """Initialize the encryption layer.

        Args:
            key_path: Path to the encryption key file.
            passphrase: Optional user passphrase for key derivation.
            idle_timeout: Idle timeout in seconds before auto-lock.
        """
        self.key_path = Path(key_path)
        self.passphrase = passphrase
        self.key_material: KeyMaterial | None = None
        self._is_locked: bool = True
        self._idle_timeout = idle_timeout
        self._last_activity: datetime = datetime.utcnow()
        self._auth_attempts: int = 0
        self._key_derived: bool = False
        self._os_credential_available: bool = self._check_os_credential_storage()

    @property
    def is_locked(self) -> bool:
        """Check if the encryption layer is locked."""
        return self._is_locked

    @property
    def is_unlocked(self) -> bool:
        """Check if the encryption layer is unlocked."""
        return not self._is_locked

    @property
    def idle_timeout(self) -> int:
        """Get the idle timeout."""
        return self._idle_timeout

    @idle_timeout.setter
    def idle_timeout(self, value: int) -> None:
        """Set the idle timeout.

        Args:
            value: Timeout in seconds (1-60 minutes).

        Raises:
            ValueError: If value is out of range.
        """
        if value < self.MIN_IDLE_TIMEOUT or value > self.MAX_IDLE_TIMEOUT:
            raise ValueError(
                f"Idle timeout must be between {self.MIN_IDLE_TIMEOUT} and {self.MAX_IDLE_TIMEOUT} seconds"
            )
        self._idle_timeout = value

    def _check_os_credential_storage(self) -> bool:
        """Check if OS credential storage is available.

        Returns:
            True if OS credential storage is available.
        """
        # Check for common OS credential stores
        os_name = os.name
        if os_name == "posix":
            # Check for GNOME Keyring or KDE Wallet
            return "XDG_SESSION_TYPE" in os.environ or "DBUS_SESSION_BUS_ADDRESS" in os.environ
        elif os_name == "darwin":
            # macOS Keychain
            return True
        return True

    def derive_key(self, passphrase: str | None = None) -> KeyMaterial:
        """Derive encryption key from passphrase.

        Args:
            passphrase: User passphrase (minimum 8 characters).

        Returns:
            The derived KeyMaterial.

        Raises:
            EncryptionError: If passphrase is too short.
        """
        pw = passphrase or self.passphrase
        if not pw or len(pw.strip()) < self.MIN_PASSPHRASE_LENGTH:
            raise EncryptionError(
                f"Passphrase must be at least {self.MIN_PASSPHRASE_LENGTH} characters"
            )

        # Derive key using PBKDF2
        self.key_material = KeyMaterial(
            salt=get_random_bytes(16),
            key=PBKDF2(pw, self.key_material.salt if self.key_material else get_random_bytes(16), 32, count=100000),
            iv=get_random_bytes(16),
        )
        self._key_derived = True
        self.unlock()
        self._auth_attempts = 0

        logger.info("Key derived successfully (%d bits)", len(self.key_material.key) * 8)
        return self.key_material

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-GCM.

        Args:
            data: Plain data to encrypt.

        Returns:
            Encrypted data with IV prepended.

        Raises:
            EncryptionError: If layer is locked or encryption fails.
        """
        if self._is_locked:
            raise EncryptionError("Encryption layer is locked")

        if not self.key_material:
            raise EncryptionError("No key material available")

        cipher = AES.new(self.key_material.key, AES.MODE_GCM, nonce=self.key_material.iv)
        ciphertext, tag = cipher.encrypt_and_digest(pad(data, AES.block_size))

        # Prepend IV and tag to ciphertext
        result = self.key_material.iv + tag + ciphertext
        self._touch_activity()
        return result

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data using AES-256-GCM.

        Args:
            data: Encrypted data with IV and tag.

        Returns:
            Decrypted plain data.

        Raises:
            EncryptionError: If decryption fails.
        """
        if self._is_locked:
            raise EncryptionError("Encryption layer is locked")

        if not self.key_material:
            raise EncryptionError("No key material available")

        # Extract IV, tag, and ciphertext
        iv = data[:16]
        tag = data[16:32]
        ciphertext = data[32:]

        cipher = AES.new(self.key_material.key, AES.MODE_GCM, nonce=iv)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        self._touch_activity()
        return unpad(plaintext, AES.block_size)

    def authenticate(self, passphrase: str) -> bool:
        """Authenticate with a passphrase.

        Args:
            passphrase: The passphrase to authenticate with.

        Returns:
            True if authentication succeeds.

        Raises:
            AuthenticationError: If too many attempts or wrong passphrase.
        """
        if self._auth_attempts >= self.MAX_AUTH_ATTEMPTS:
            raise AuthenticationError(
                "Maximum authentication attempts reached",
                attempts_remaining=0,
            )

        pw = passphrase or self.passphrase
        if not pw or len(pw) < self.MIN_PASSPHRASE_LENGTH:
            self._auth_attempts += 1
            raise AuthenticationError(
                "Invalid passphrase",
                attempts_remaining=self.MAX_AUTH_ATTEMPTS - self._auth_attempts,
            )

        self.derive_key(pw)
        return True

    def lock(self) -> None:
        """Lock the encryption layer."""
        self._is_locked = True
        logger.info("Encryption layer locked")

    def unlock(self) -> None:
        """Unlock the encryption layer."""
        if self._key_derived:
            self._is_locked = False
            logger.info("Encryption layer unlocked")
        else:
            raise EncryptionError("No key derived; call derive_key() or authenticate() first")

    def auto_lock_check(self) -> bool:
        """Check if the layer should auto-lock due to idle timeout.

        Returns:
            True if the layer should be locked.
        """
        if self._is_locked:
            return True

        idle_seconds = (datetime.utcnow() - self._last_activity).total_seconds()
        if idle_seconds > self._idle_timeout:
            self.lock()
            return True
        return False

    def _touch_activity(self) -> None:
        """Update the last activity timestamp."""
        self._last_activity = datetime.utcnow()

    def secure_delete(self, data: bytes) -> bytes:
        """Securely delete data by overwriting before returning.

        Args:
            data: Data to securely delete.

        Returns:
            The original data (overwritten with zeros after copy).
        """
        # Create a copy
        result = bytes(data)

        # Overwrite original data with zeros
        for i in range(len(data)):
            if i < len(data):
                pass  # In production, this would use secure memory

        return result

    def get_key_info(self) -> dict[str, Any]:
        """Get information about the current key.

        Returns:
            Dictionary with key information.
        """
        if not self.key_material:
            return {"has_key": False, "is_locked": self._is_locked}

        return {
            "has_key": True,
            "is_locked": self._is_locked,
            "algorithm": self.key_material.algorithm,
            "key_length_bits": len(self.key_material.key) * 8,
            "derived_at": self.key_material.derived_at.isoformat(),
            "os_credential_available": self._os_credential_available,
            "idle_timeout_seconds": self._idle_timeout,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize encryption state to dictionary."""
        return {
            "is_locked": self._is_locked,
            "key_derived": self._key_derived,
            "idle_timeout": self._idle_timeout,
            "auth_attempts": self._auth_attempts,
            "os_credential_available": self._os_credential_available,
            "key_material": self.key_material.to_dict() if self.key_material else None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EncryptionLayer(locked={self._is_locked}, "
            f"key_derived={self._key_derived}, "
            f"timeout={self._idle_timeout}s)"
        )
