#data_masker.py
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
        Attempts to load the JSON configuration. 
        Raises an error if the file is not found or if the JSON is invalid.
        """
        try:
            print(f"Loading masking configuration from: {path}")
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in {path}")

    def mask_email(self, email: Optional[str]) -> Optional[str]:
        # Strictly enforce the presence of a valid email format
        if not email or "@" not in email:
            raise ValueError(f"Invalid email format provided: {email}")
            
        local_part, domain = email.split("@", 1)
        
        # Strict config lookup - will raise a KeyError if the key is missing
        visible_chars = self.config["email_visible_chars"]
        
        # 1. Mask the local part (name)
        if len(local_part) <= visible_chars:
            masked_local = self.mask_char * len(local_part)
        else:
            masked_local = local_part[:visible_chars] + (self.mask_char * (len(local_part) - visible_chars))
            
        # 2. Mask the domain part
        if len(domain) <= visible_chars:
            masked_domain = self.mask_char * len(domain)
        else:
            masked_domain = domain[:visible_chars] + (self.mask_char * (len(domain) - visible_chars))
            
        return f"{masked_local}@{masked_domain}"

    def mask_phone(self, phone: Optional[str]) -> str:
        # 1. Strict Error Handling
        if not phone:
            raise ValueError("Invalid phone number: Input cannot be empty.")
            
        digits_only = re.sub(r'\D', '', phone)
        total_digits = len(digits_only)
        
        if total_digits == 0:
            raise ValueError("Invalid phone number: No digits found.")
            
        # 2. Strict Config Lookup
        visible_digits = self.config["phone_visible_digits"]
        
        # 3. The Strict Limit: If config asks for more than 4 digits (or is negative), mask it all
        if visible_digits > 4 or visible_digits < 0:
            visible_digits = 0
            
        # 4. Iterative Masking (Preserves formatting like parentheses and dashes)
        masked_phone = []
        digit_count = 0
        
        for char in phone:
            if char.isdigit():
                # Mask if we haven't reached the allowed visible digits at the end
                if total_digits - digit_count > visible_digits:
                    masked_phone.append(self.mask_char)
                else:
                    masked_phone.append(char)
                digit_count += 1
            else:
                # Keep formatting characters untouched
                masked_phone.append(char)
                
        return "".join(masked_phone)

    def mask_ssn(self, ssn: Optional[str]) -> str:
        # 1. Error on empty input
        if not ssn:
            raise ValueError("Invalid SSN: Input cannot be empty.")
            
        clean_ssn = re.sub(r'\D', '', ssn)
        
        # 1. Error if it is not exactly 9 digits
        if len(clean_ssn) != 9:
            raise ValueError(f"Invalid SSN format: Expected 9 digits, got {len(clean_ssn)}.")
            
        # 2. Strict config lookup with no hardcoded fallbacks
        visible_digits = self.config["ssn_visible_digits"]
        
        # 3. First two parts are always completely masked
        part1 = self.mask_char * 3
        part2 = self.mask_char * 2
        
        # Isolate the final 4 digits
        last_part = clean_ssn[-4:]
        
        # 4 & 5. Handle the last part dynamically or penalize over-limits
        if visible_digits > 4 or visible_digits < 0:
            # Mask completely if the config asks for more digits than exist in this block
            masked_last_part = self.mask_char * 4
        elif visible_digits == 0:
             # Handle 0 explicitly to avoid Python slicing quirks
             masked_last_part = self.mask_char * 4
        else:
            # Mask the hidden characters and append the visible ones
            hidden_count = 4 - visible_digits
            masked_last_part = (self.mask_char * hidden_count) + last_part[hidden_count:]
            
        return f"{part1}-{part2}-{masked_last_part}"