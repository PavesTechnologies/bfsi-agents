import base64
from utilities.approle_auth import login_to_vault
from utilities.env_loader import load_env

class SSNVaultService:
    def __init__(self):
        """
        7. SERVICE gets transit key name from the env.
        1. SERVICE gets roleid from env.
        """
        # Load the Transit Key Name specifically for the SSN context
        self.key_name = load_env("VAULT_TRANSIT_SSN_KEY_NAME")
        
        # Get the RoleID to be passed for authentication
        self.role_id = load_env("VAULT_SSN_ROLE_ID")

    # --- Formatting Utilities ---
    
    def _to_base64(self, plain_text):
        return base64.b64encode(plain_text.encode()).decode()

    def _from_base64(self, base64_text):
        return base64.b64decode(base64_text).decode()

    # --- SSN Functionalities ---

    def protect_ssn(self, ssn_text):
        """
        Flow: gets role_id -> calls auth -> receives session -> 8. performs action.
        """
        # 1. Convert to base64
        b64_data = self._to_base64(ssn_text)

        # 1 & 5. Call Auth with the RoleID (Initiates SecretID & mTLS flow)
        # 6. Auth passes back the entire authenticated session
        ssm_path = load_env("VAULT_SSN_SSM_PATH")
        client = login_to_vault(self.role_id, ssm_path)

        # 8. Perform encryption using the SSN-specific transit key
        response = client.secrets.transit.encrypt_data(
            name=self.key_name,
            plaintext=b64_data
        )

        return response['data']['ciphertext']

    def retrieve_ssn(self, ciphertext):
        """
        Flow: gets role_id -> calls auth -> receives session -> 8. performs action.
        """
        # 1 & 5. Call Auth with the RoleID
        # 6. Auth passes back the entire authenticated session
        ssm_path = load_env("VAULT_SSN_SSM_PATH")
        client = login_to_vault(self.role_id, ssm_path)

        # 8. Perform decryption using the SSN-specific transit key
        response = client.secrets.transit.decrypt_data(
            name=self.key_name,
            ciphertext=ciphertext
        )

        # Convert from base64 and return
        return self._from_base64(response['data']['plaintext'])
    

obj=SSNVaultService()
print(obj.retrieve_ssn("vault:v1:ju+mCD860XqM4CgD85FJQC6kBjaPoQTz75Y8I7FOfXneaH4qPFch"))