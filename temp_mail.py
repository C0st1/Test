"""
PHANTOM MAILER — Temp Mail Providers
Handles account generation from multiple temp mail APIs.
Auto-rotates providers for resilience.
"""

import random
import time
import string
import requests
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from abc import ABC, abstractmethod


@dataclass
class TempAccount:
    """A generated temporary email account."""
    email: str
    provider: str
    token: str = ""
    password: str = ""
    created_at: float = field(default_factory=time.time)
    send_count: int = 0
    max_sends: int = 5
    alive: bool = True


class TempMailProvider(ABC):
    """Base class for temp mail providers."""

    name: str = "base"

    @abstractmethod
    def generate(self) -> TempAccount:
        """Generate a new temp email account."""
        ...

    @abstractmethod
    def check_alive(self, account: TempAccount) -> bool:
        """Check if the account is still active."""
        ...

    def mark_used(self, account: TempAccount) -> None:
        """Increment send counter and check if exhausted."""
        account.send_count += 1
        if account.send_count >= account.max_sends:
            account.alive = False


class GuerrillaMailProvider(TempMailProvider):
    """Guerrilla Mail API — free, no auth needed."""

    name = "guerrilla"

    BASE_URL = "https://api.guerrillamail.com/ajax.php"

    def generate(self) -> TempAccount:
        try:
            # Get a new address
            sid = self._get_sid()
            params = {
                "f": "get_email_address",
                "sid_token": sid,
                "lang": "en",
            }
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            data = resp.json()
            email = data.get("email_addr", "")
            token = data.get("sid_token", sid)
            if email:
                return TempAccount(
                    email=email,
                    provider=self.name,
                    token=token,
                    max_sends=random.randint(3, 7),
                )
        except Exception as e:
            pass

        # Fallback: generate a plausible address
        return self._fallback_account()

    def _get_sid(self) -> str:
        try:
            resp = requests.get(
                self.BASE_URL, params={"f": "get_email_address", "lang": "en"}, timeout=10
            )
            return resp.json().get("sid_token", "")
        except Exception:
            return ""

    def check_alive(self, account: TempAccount) -> bool:
        return account.alive and account.send_count < account.max_sends

    def _fallback_account(self) -> TempAccount:
        user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return TempAccount(
            email=f"{user}@guerrillamail.com",
            provider=self.name,
            max_sends=random.randint(3, 7),
        )


class MailTmProvider(TempMailProvider):
    """Mail.tm API — RESTful, reliable."""

    name = "mail.tm"

    BASE_URL = "https://api.mail.tm"

    def generate(self) -> TempAccount:
        try:
            # Get available domains
            resp = requests.get(f"{self.BASE_URL}/domains", timeout=10)
            domains = resp.json().get("hydra:member", [])
            if not domains:
                return self._fallback_account()

            domain = random.choice(domains)["domain"]
            user = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
            email = f"{user}@{domain}"
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))

            # Create account
            resp = requests.post(
                f"{self.BASE_URL}/accounts",
                json={"address": email, "password": password},
                timeout=10,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return TempAccount(
                    email=email,
                    provider=self.name,
                    token=data.get("id", ""),
                    password=password,
                    max_sends=random.randint(3, 7),
                )
        except Exception:
            pass

        return self._fallback_account()

    def check_alive(self, account: TempAccount) -> bool:
        return account.alive and account.send_count < account.max_sends

    def _fallback_account(self) -> TempAccount:
        user = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return TempAccount(
            email=f"{user}@mail.tm",
            provider=self.name,
            max_sends=random.randint(3, 7),
        )


class OneSecMailProvider(TempMailProvider):
    """1secmail.com API — simple, fast."""

    name = "1secmail"

    BASE_URL = "https://www.1secmail.com/api/v1/"

    DOMAINS = [
        "1secmail.com", "1secmail.org", "1secmail.net",
        "esiix.com", "wwjmp.com", "xojxe.com",
        "yoggm.com", "dpptd.com",
    ]

    def generate(self) -> TempAccount:
        try:
            login = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            domain = random.choice(self.DOMAINS)
            email = f"{login}@{domain}"

            # Verify it works
            resp = requests.get(
                self.BASE_URL,
                params={"action": "getMessages", "login": login, "domain": domain},
                timeout=10,
            )
            if resp.status_code == 200:
                return TempAccount(
                    email=email,
                    provider=self.name,
                    token=login,
                    max_sends=random.randint(3, 7),
                )
        except Exception:
            pass

        return self._fallback_account()

    def check_alive(self, account: TempAccount) -> bool:
        return account.alive and account.send_count < account.max_sends

    def _fallback_account(self) -> TempAccount:
        user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = random.choice(self.DOMAINS)
        return TempAccount(
            email=f"{user}@{domain}",
            provider=self.name,
            max_sends=random.randint(3, 7),
        )


class TempMailManager:
    """Manages multiple temp mail providers with rotation and pooling."""

    PROVIDERS = {
        "guerrilla": GuerrillaMailProvider,
        "mail.tm": MailTmProvider,
        "1secmail": OneSecMailProvider,
    }

    def __init__(self, provider: str = "all", pre_generate: int = 5, rotate_every: int = 3):
        self.provider_name = provider
        self.pre_generate = pre_generate
        self.rotate_every = rotate_every
        self.pool: List[TempAccount] = []
        self.current_index = 0
        self._send_counter = 0

        # Initialize provider(s)
        if provider == "all":
            self._providers = [cls() for cls in self.PROVIDERS.values()]
        else:
            cls = self.PROVIDERS.get(provider, GuerrillaMailProvider)
            self._providers = [cls()]

    def warm_up(self, count: int = None) -> List[TempAccount]:
        """Pre-generate a pool of temp accounts."""
        n = count or self.pre_generate
        accounts = []
        for i in range(n):
            provider = random.choice(self._providers)
            try:
                account = provider.generate()
                accounts.append(account)
            except Exception:
                # If one provider fails, try another
                for p in self._providers:
                    try:
                        account = p.generate()
                        accounts.append(account)
                        break
                    except Exception:
                        continue
            time.sleep(0.3)  # Don't hammer the APIs
        self.pool.extend(accounts)
        return accounts

    def get_account(self) -> TempAccount:
        """Get the next available account, rotating as needed."""
        # Check if we need to rotate
        if self._send_counter >= self.rotate_every and self.pool:
            self.current_index = (self.current_index + 1) % len(self.pool)
            self._send_counter = 0

        # Find an alive account
        attempts = 0
        while attempts < len(self.pool) + 1:
            if self.pool:
                idx = (self.current_index + attempts) % len(self.pool)
                account = self.pool[idx]
                if account.alive:
                    self.current_index = idx
                    return account

            # Generate a new one if pool is exhausted
            provider = random.choice(self._providers)
            try:
                account = provider.generate()
                self.pool.append(account)
                self.current_index = len(self.pool) - 1
                return account
            except Exception:
                continue

            attempts += 1

        # Absolute fallback
        return TempAccount(
            email=f"phantom{''.join(random.choices(string.digits, k=6))}@temp.invalid",
            provider="fallback",
            max_sends=1,
        )

    def mark_sent(self, account: TempAccount) -> None:
        """Mark an account as used for one send."""
        self._send_counter += 1
        # Find the provider and mark
        for p in self._providers:
            if p.name == account.provider:
                p.mark_used(account)
                break

        # If account is dead, replace it
        if not account.alive:
            self._replace_account(account)

    def _replace_account(self, dead_account: TempAccount) -> None:
        """Replace a dead account with a fresh one."""
        provider = random.choice(self._providers)
        try:
            new_account = provider.generate()
            idx = self.pool.index(dead_account)
            self.pool[idx] = new_account
        except (ValueError, Exception):
            pass

    def pool_status(self) -> dict:
        """Get pool status summary."""
        alive = sum(1 for a in self.pool if a.alive)
        dead = len(self.pool) - alive
        return {
            "total": len(self.pool),
            "alive": alive,
            "dead": dead,
            "providers_used": list(set(a.provider for a in self.pool)),
        }
