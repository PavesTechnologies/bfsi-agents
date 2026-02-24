import json
import re
from typing import Optional

class SupportDataMasker:
    """
    A utility class for masking sensitive PII for support visibility.
    Automatically loads configuration rules from the utilities directory.
    """
    def __init__(self, config_path: str = "vault/agent_services/utilities/masking_config.json"):
        # Load the config internally, keeping the service layer clean
        self.config = self._load_config(config_path)
        self.mask_char = self.config.get("mask_char", "*")

    def _load_config(self, path: str) -> dict:
        """
        Attempts to load the JSON configuration. Falls back to safe 
        default rules if the file is not found.
        """
        try:
            with open(path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            # Safe default fallback 
            return {
                "mask_char": "*",
                "email_visible_chars": 2,
                "phone_visible_digits": 4,
                "ssn_visible_digits": 4
            }
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in {path}")

    def mask_email(self, email: Optional[str]) -> Optional[str]:
        if not email or "@" not in email:
            return email
            
        local_part, domain = email.split("@", 1)
        visible_chars = self.config.get("email_visible_chars", 2)
        
        if len(local_part) <= visible_chars:
            masked_local = self.mask_char * len(local_part)
        else:
            masked_local = local_part[:visible_chars] + (self.mask_char * (len(local_part) - visible_chars))
            
        return f"{masked_local}@{domain}"

    def mask_phone(self, phone: Optional[str]) -> Optional[str]:
        if not phone:
            return phone
            
        digits_only = re.sub(r'\D', '', phone)
        visible_digits = self.config.get("phone_visible_digits", 4)
        
        if len(digits_only) <= visible_digits:
            return self.mask_char * len(digits_only)
            
        masked_phone = []
        digit_count = 0
        total_digits = len(digits_only)
        
        for char in phone:
            if char.isdigit():
                if total_digits - digit_count > visible_digits:
                    masked_phone.append(self.mask_char)
                else:
                    masked_phone.append(char)
                digit_count += 1
            else:
                masked_phone.append(char)
                
        return "".join(masked_phone)

    def mask_ssn(self, ssn: Optional[str]) -> Optional[str]:
        if not ssn:
            return ssn
            
        visible_digits = self.config.get("ssn_visible_digits", 4)
        clean_ssn = re.sub(r'\D', '', ssn)
        
        if len(clean_ssn) != 9:
            return self.mask_char * len(clean_ssn)
            
        hidden_part = self.mask_char * (9 - visible_digits)
        visible_part = clean_ssn[-visible_digits:]
        
        return f"{hidden_part[:3]}-{hidden_part[3:5]}-{visible_part}"