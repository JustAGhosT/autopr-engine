"""GitHub Secrets Management.

Encrypts and sets repository secrets using GitHub's public key.
"""

import base64
import logging
import os

from github import GithubIntegration
from nacl import public

logger = logging.getLogger(__name__)


def encrypt_secret(secret_value: str, public_key: str) -> str:
    """Encrypt a secret value using GitHub's public key (libsodium sealed box).

    Args:
        secret_value: The secret value to encrypt
        public_key: GitHub's public key (base64)

    Returns:
        Encrypted secret (base64)
    """
    # Decode the public key
    public_key_bytes = base64.b64decode(public_key)

    # Create a sealed box
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))

    # Encrypt the message
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))

    # Return base64 encoded
    return base64.b64encode(encrypted).decode("utf-8")


async def configure_repository_secrets(
    installation_id: int,
    owner: str,
    repo: str,
) -> None:
    """Configure repository secrets automatically.

    Args:
        installation_id: GitHub App installation ID
        owner: Repository owner (username or org)
        repo: Repository name
    """
    github_app_id = os.getenv("GITHUB_APP_ID")
    github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")

    if not github_app_id or not github_app_private_key:
        raise ValueError("GitHub App not configured")

    try:
        # Create GitHub integration
        integration = GithubIntegration(
            github_app_id,
            github_app_private_key.replace("\\n", "\n"),
        )

        # Get installation access token
        access_token = integration.get_access_token(installation_id).token

        # Get GitHub instance
        from github import Github

        g = Github(access_token)
        repository = g.get_repo(f"{owner}/{repo}")

        # Get repository's public key
        public_key_data = repository.get_public_key()

        # Secrets to configure
        secrets = {
            "AZURE_CREDENTIALS": os.getenv("DEFAULT_AZURE_CREDENTIALS"),
            "AZURE_SUBSCRIPTION_ID": os.getenv("DEFAULT_AZURE_SUBSCRIPTION_ID"),
            "POSTGRES_ADMIN_LOGIN": os.getenv("DEFAULT_POSTGRES_ADMIN_LOGIN"),
            "POSTGRES_ADMIN_PASSWORD": os.getenv("DEFAULT_POSTGRES_ADMIN_PASSWORD"),
            "ADMIN_PASSWORD": os.getenv("DEFAULT_ADMIN_PASSWORD"),
        }

        # Set each secret
        for secret_name, secret_value in secrets.items():
            if secret_value:
                try:
                    # Encrypt the secret
                    encrypted_value = encrypt_secret(secret_value, public_key_data.key)

                    # Set the secret
                    repository.create_secret(
                        secret_name,
                        encrypted_value,
                        public_key_data.key_id,
                    )

                    logger.info(f"Set secret: {secret_name} for {owner}/{repo}")

                except Exception as e:
                    logger.error(
                        f"Failed to set secret {secret_name}: {e}",
                        exc_info=True,
                    )

        logger.info(f"Repository {owner}/{repo} configured successfully")

    except Exception as e:
        logger.error(
            f"Failed to configure repository {owner}/{repo}: {e}",
            exc_info=True,
        )
        raise

