import base64
# from utilities.approle_auth import login_to_vault
# from utilities.env_loader import load_env

from src.adapters.vault.utilities.env_loader import load_env
from src.adapters.vault.utilities.approle_auth import login_to_vault

class PhoneNumberVaultService:
    def __init__(self):
        # 1. SERVICE gets Transit Key name from env
        self.key_name = load_env("VAULT_TRANSIT_PHONE_NUMBER_KEY_NAME")
        # 2. SERVICE gets its RoleID from env (to pass to Auth later)
        self.role_id = load_env("VAULT_PHONE_NUMBER_ROLE_ID")

    # --- Formatting Utilities ---
    
    def _to_base64(self, plain_text):
        return base64.b64encode(plain_text.encode()).decode()

    def _from_base64(self, base64_text):
        return base64.b64decode(base64_text).decode()

    # --- Vault Action Flow ---

    def protect_phone_number(self, phone_number):
        """
        Flow: gets role_id -> calls auth -> receives session -> performs action.
        """
        # Convert to base64
        b64_data = self._to_base64(phone_number)

        # 5. CALL AUTH with RoleID (Auth will get SecretID and mTLS certs)
        ssm_path = load_env("VAULT_PHONE_NUMBER_SSM_PATH")
        client = login_to_vault(self.role_id, ssm_path)

        # 8. PERFORM ACTION
        response = client.secrets.transit.encrypt_data(
            name=self.key_name,
            plaintext=b64_data
        )

        return response['data']['ciphertext']

    def retrieve_phone_number(self, ciphertext):
        """
        Flow: gets role_id -> calls auth -> receives session -> performs action.
        """
        # 5. CALL AUTH with RoleID
        ssm_path = load_env("VAULT_PHONE_NUMBER_SSM_PATH")
        client = login_to_vault(self.role_id, ssm_path)

        # 8. PERFORM ACTION
        response = client.secrets.transit.decrypt_data(
            name=self.key_name,
            ciphertext=ciphertext
        )

        return self._from_base64(response['data']['plaintext'])
    
# obj=PhoneNumberVaultService()
# print(obj.protect_phone_number("123-456-7890"))

# obj=PhoneNumberVaultService()
# print(obj.retrieve_phone_number("vault:v1:wGagbeT8ub9/F2AeREZ4VVR1hvxxmbSUS7SuyrbiVEpAMv6629fzCA=="))
