import os
import ssl
import tempfile

from src.adapters.vault.utilities.env_loader import load_env

# from utilities.load_secrets import get_aws_secret
# from utilities.env_loader import load_env
from src.adapters.vault.utilities.load_secrets import get_aws_secret


def establish_mtls_context():
    """
    3. THE mTLS FUNCTION:
       - Gets CA, Cert, and Private Key from SSM.
       - Establishes the SSL Context.
    4. RETURNS: The established SSL context back to Auth.
    """
    # 1. Determine SSM Paths from environment
    ca_path = load_env("SSM_PATH_CA_CERT")
    cert_path = load_env("SSM_PATH_CLIENT_CERT")
    key_path = load_env("SSM_PATH_CLIENT_KEY")

    # 2. Fetch the raw strings from SSM (using your plain text secret loader)
    ca_cert = get_aws_secret(ca_path)
    client_cert = get_aws_secret(cert_path)
    client_key = get_aws_secret(key_path)

    # 3. Create a standard SSL Context
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    # 4. Handle Certificate Loading into Memory
    # Using NamedTemporaryFiles allows the ssl library to read the data,
    # but we delete them immediately in the finally block.
    cert_f = tempfile.NamedTemporaryFile(delete=False)
    key_f = tempfile.NamedTemporaryFile(delete=False)
    ca_f = tempfile.NamedTemporaryFile(delete=False)

    try:
        # Write cert data to temp files
        cert_f.write(client_cert.encode())
        key_f.write(client_key.encode())
        ca_f.write(ca_cert.encode())

        # Ensure data is flushed to the files
        cert_f.close()
        key_f.close()
        ca_f.close()

        # Load the client cert and private key for the mTLS handshake
        context.load_cert_chain(certfile=cert_f.name, keyfile=key_f.name)

        # Load the CA to verify the Vault Server's certificate
        context.load_verify_locations(cafile=ca_f.name)

    finally:
        # 4. CLEANUP: Remove files from disk immediately.
        # The certificates are now safely stored in the 'context' object in RAM.
        if os.path.exists(cert_f.name):
            os.unlink(cert_f.name)
        if os.path.exists(key_f.name):
            os.unlink(key_f.name)
        if os.path.exists(ca_f.name):
            os.unlink(ca_f.name)

    return context
