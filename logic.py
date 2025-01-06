# logic.py
import json
import pyotp
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import base64
import random

class AuthenticatorLogic:
    def __init__(self):
        self.secrets_file = Path("auth_secrets.json")
        self.secrets: Dict[str, str] = {}
        self.load_secrets()

    def load_secrets(self) -> Dict[str, str]:
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    self.secrets = json.load(f)
                    return self.secrets
            except Exception:
                return {}
        return {}

    def save_secrets(self) -> bool:
        try:
            with open(self.secrets_file, 'w') as f:
                json.dump(self.secrets, f, indent=2, sort_keys=True)
            return True
        except Exception:
            return False

    def add_account(self, name: str, secret: str) -> Tuple[bool, str]:
        try:
            pyotp.TOTP(secret).now()
            self.secrets[name] = secret
            success = self.save_secrets()
            if success:
                return True, "account added successfully"
            return False, "failed to save account"
        except Exception:
            return False, "invalid secret key format"

    def add_test_account(self) -> Tuple[bool, str]:
        try:
            random_bytes = random.randbytes(20)
            secret = base64.b32encode(random_bytes).decode('utf-8')

            test_num = 1
            while f"test account {test_num}" in self.secrets:
                test_num += 1

            name = f"test account {test_num}"
            return self.add_account(name, secret)
        except Exception:
            return False, "failed to create test account"

    def remove_account(self, account: str) -> bool:
        try:
            del self.secrets[account]
            return self.save_secrets()
        except Exception:
            return False

    def get_code(self, secret: str) -> Optional[str]:
        try:
            code = pyotp.TOTP(secret).now()
            return f"{int(code):06d}"
        except Exception:
            return None

    def reorder_accounts(self, accounts: list) -> bool:
        try:
            new_secrets = {}
            for acc in accounts:
                new_secrets[acc] = self.secrets[acc]
            self.secrets = new_secrets
            success = self.save_secrets()
            return success
        except Exception:
            return False

    def get_all_codes(self) -> List[Tuple[str, str]]:
        codes = []
        for name, secret in self.secrets.items():
            code = self.get_code(secret)
            if code:
                codes.append((name, code))
        return codes

    def get_time_remaining(self) -> int:
        return 30 - int(time.time()) % 30