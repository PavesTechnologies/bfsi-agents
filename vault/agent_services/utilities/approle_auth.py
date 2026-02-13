import hvac
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from vault.agent_services.utilities.mTLS_establishment import establish_mtls_context
from utilities.load_secrets import get_aws_secret
from utilities.env_loader import load_env

class SSLContextAdapter(HTTPAdapter):
    """
    Custom adapter to inject a pre-configured SSLContext
    for true mTLS connectivity.
    """
    def __init__(self, ssl_context, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        pool_kwargs["ssl_context"] = self.ssl_context
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs
        )

def login_to_vault(role_id, ssm_path):
    """
    Auth Flow:
    2. Gets secret_id from SSM & calls mTLS context function.
    4. Receives connection (ssl_context) back.
    5. Uses secret_id and role_id to login.
    6. Returns the entire session (client) to the service.
    """
    vault_url = load_env("VAULT_ADDR")
    
    # 2a. Get SecretID from SSM (Path stored in env)
    secret_id_path = ssm_path
    secret_id = get_aws_secret(secret_id_path)

    # 2b & 3. Trigger mTLS establishment (which gets certs from SSM)
    # 4. Connection (context) passed back here
    ssl_context = establish_mtls_context()

    # Initialize Client
    client = hvac.Client(url=vault_url)

    # Inject mTLS context into the session
    adapter = SSLContextAdapter(ssl_context)
    client.adapter.session.mount("https://", adapter)

    try:
        # 5. Perform AppRole login
        client.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id
        )

        print("Successfully authenticated to Vault via mTLS and AppRole.")
        
        # 6. Pass the entire session back to the service
        return client

    except Exception as e:
        print(f"Vault login failed: {e}")
        raise