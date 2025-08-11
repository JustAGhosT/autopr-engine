"""
Security Generator Module

Handles generation of security-related configurations and implementations.
"""

import os
import secrets
import string
from pathlib import Path
from typing import Any

from .base_generator import BaseGenerator


class SecurityGenerator(BaseGenerator):
    """Generates security-related configurations and implementations."""

    def generate(self, output_dir: str, **kwargs) -> list[str]:
        """Generate security-related files and configurations."""
        generated_files = []
        language = kwargs.get("language", "").lower()
        framework = kwargs.get("framework", "").lower()

        # Common variables for security templates
        template_vars = {
            "language": language,
            "framework": framework,
            "jwt_secret": self._generate_random_secret(64),
            "session_secret": self._generate_random_secret(32),
            "api_key_secret": self._generate_random_secret(48),
            "encryption_key": self._generate_random_secret(32),
            **self._get_platform_variables(),
        }

        # Generate .env.example with security variables
        generated_files.extend(self._generate_env_example(output_dir, template_vars))

        # Generate security middleware/config
        generated_files.extend(self._generate_security_config(output_dir, template_vars))

        # Generate security.txt
        generated_files.extend(self._generate_security_txt(output_dir, template_vars))

        return generated_files

    def _generate_random_secret(self, length: int = 32) -> str:
        """Generate a random secret string."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_env_example(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate .env.example file with security variables."""
        env_vars = {
            "NODE_ENV": "development",
            "PORT": "3000",
            "JWT_SECRET": variables["jwt_secret"],
            "SESSION_SECRET": variables["session_secret"],
            "ENCRYPTION_KEY": variables["encryption_key"],
            "DATABASE_URL": "postgresql://user:password@localhost:5432/your_db_name",
            "CORS_ORIGIN": "http://localhost:3000",
            "RATE_LIMIT_WINDOW_MS": "900000",
            "RATE_LIMIT_MAX": "100",
        }

        content = "# Security Environment Variables\n# =========================\n"
        content += "\n".join(f"{k}={v}" for k, v in env_vars.items())

        file_path = str(Path(output_dir) / ".env.example")
        self._write_file(file_path, content)

        return [file_path]

    def _generate_security_config(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate security configuration files."""
        generated_files = []
        language = variables.get("language", "")

        # Generate security middleware based on language
        if language == "typescript":
            security_config = """// Security middleware configuration
export const securityConfig = {
  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
  },
  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'),
    max: parseInt(process.env.RATE_LIMIT_MAX || '100')
  },
  helmet: {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'"],
        imgSrc: ["'self'"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
        frameAncestors: ["'none'"],
        formAction: ["'self'"],
        baseUri: ["'self'"],
      },
    },
  }
};
"""
            file_path = str(Path(output_dir) / "src" / "config" / "security.ts")
            os.makedirs(Path(file_path).parent, exist_ok=True)
            self._write_file(file_path, security_config)
            generated_files.append(file_path)

        return generated_files

    def _generate_security_txt(self, output_dir: str, variables: dict[str, Any]) -> list[str]:
        """Generate security.txt file."""
        content = """# Security contact information
Contact: security@example.com
Encryption: https://example.com/security-pgp-key.txt
Acknowledgments: https://example.com/security-hall-of-fame.html
Policy: https://example.com/security-policy.html
"""
        # Create .well-known directory if it doesn't exist
        well_known_dir = Path(output_dir) / ".well-known"
        well_known_dir.mkdir(exist_ok=True)

        # Write to both locations
        well_known_path = well_known_dir / "security.txt"
        root_path = Path(output_dir) / "security.txt"

        self._write_file(str(well_known_path), content)
        self._write_file(str(root_path), content)

        return [str(well_known_path), str(root_path)]
