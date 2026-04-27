"""
PHANTOM MAILER — Core Engine
Orchestrates campaigns: sending, threading, proxies, resume, analytics.
"""

import json
import os
import random
import smtplib
import time
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional, Dict, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict

from temp_mail import TempMailManager, TempAccount
from templates import get_template, get_template_names, TEMPLATES
from renderer import MessageRenderer


# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class SendResult:
    """Result of a single email send attempt."""
    index: int
    target: str
    subject: str
    sender: str
    template: str
    status: str               # "sent", "failed", "dry_run", "skipped"
    error: str = ""
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0


@dataclass
class CampaignState:
    """Serializable campaign state for resume support."""
    name: str
    config: dict
    sent: int = 0
    failed: int = 0
    dry_run: int = 0
    results: List[dict] = field(default_factory=list)
    started_at: str = ""
    last_index: int = -1
    completed: bool = False


# ═══════════════════════════════════════════════════════════════
#  CORE ENGINE
# ═══════════════════════════════════════════════════════════════

class PhantomEngine:
    """The heart of PHANTOM MAILER. Manages everything."""

    def __init__(self, config: dict):
        self.config = config
        self.core = config.get("core", {})
        self.timing = config.get("timing", {})
        self.temp_mail_cfg = config.get("temp_mail", {})
        self.smtp_cfg = config.get("smtp", {})
        self.proxy_cfg = config.get("proxy", {})
        self.msg_cfg = config.get("message", {})
        self.subject_cfg = config.get("subject", {})
        self.campaign_cfg = config.get("campaign", {})
        self.analytics_cfg = config.get("analytics", {})

        # State
        self.results: List[SendResult] = []
        self.state: Optional[CampaignState] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Callbacks for CLI
        self.on_send: Optional[Callable] = None
        self.on_progress: Optional[Callable] = None
        self.on_status: Optional[Callable] = None

        # Initialize components
        self.temp_manager = TempMailManager(
            provider=self.temp_mail_cfg.get("provider", "all"),
            pre_generate=self.temp_mail_cfg.get("pre_generate", 5),
            rotate_every=self.temp_mail_cfg.get("rotate_every", 3),
        )

        self.renderer = MessageRenderer(
            locale=self.msg_cfg.get("locale", "en_US"),
            add_typo=self.msg_cfg.get("add_typo", True),
            add_signature=self.msg_cfg.get("add_signature", True),
            add_disclaimer=self.msg_cfg.get("add_disclaimer", True),
            add_urgency=self.msg_cfg.get("add_urgency", True),
        )

        # Proxy rotation
        self.proxies: List[str] = self._load_proxies()
        self.proxy_index = 0

        # SMTP servers
        self.smtp_servers = self.smtp_cfg.get("servers", [])
        self.smtp_index = 0

    # ── Campaign Execution ────────────────────────────────────

    def run(self) -> CampaignState:
        """Execute the full campaign."""
        send_count = self.core.get("send_count", 50)
        targets = self.core.get("targets", ["target@example.com"])
        max_workers = self.core.get("max_workers", 5)
        dry_run = self.core.get("dry_run", False)

        # Initialize campaign state
        self.state = CampaignState(
            name=self.campaign_cfg.get("name", "phantom_campaign"),
            config=self.config,
            started_at=datetime.now().isoformat(),
        )

        # Resume support
        resume_file = self.campaign_cfg.get("resume_file", "")
        start_index = 0
        if resume_file and os.path.exists(resume_file):
            start_index = self._load_state(resume_file)

        # Warm up temp mail pool
        pre_gen = self.temp_mail_cfg.get("pre_generate", 5)
        if self.on_status:
            self.on_status(f"🔥 Warming up {pre_gen} temp mail accounts...")
        self.temp_manager.warm_up(pre_gen)

        if self.on_status:
            self.on_status(f"✅ Pool ready: {self.temp_manager.pool_status()}")

        # Build send queue
        queue = []
        for i in range(start_index, send_count):
            target = random.choice(targets)
            queue.append((i, target))

        if self.on_status:
            mode = "DRY RUN" if dry_run else "LIVE"
            self.on_status(f"🚀 Starting campaign '{self.state.name}' [{mode}] — {len(queue)} emails queued")

        # Execute with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for idx, target in queue:
                if self._stop_event.is_set():
                    break
                future = executor.submit(self._send_one, idx, target, dry_run)
                futures[future] = idx

                # Stagger submissions to respect timing
                delay = self._get_delay()
                time.sleep(delay)

            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
                try:
                    result = future.result()
                    with self._lock:
                        self.results.append(result)
                        self._update_state(result)
                except Exception as e:
                    idx = futures[future]
                    result = SendResult(
                        index=idx, target="unknown", subject="",
                        sender="", template="", status="failed",
                        error=str(e),
                    )
                    with self._lock:
                        self.results.append(result)
                        self._update_state(result)

        # Finalize
        self.state.completed = True
        self._save_state()

        if self.analytics_cfg.get("save_report", True):
            self._save_report()

        return self.state

    def stop(self):
        """Gracefully stop the campaign."""
        self._stop_event.set()

    # ── Single Send ───────────────────────────────────────────

    def _send_one(self, index: int, target: str, dry_run: bool) -> SendResult:
        """Send a single email."""
        start_time = time.time()

        # Coffee break
        interval = self.timing.get("coffee_break_interval", 15)
        if index > 0 and index % interval == 0:
            break_min = self.timing.get("coffee_break_min", 30)
            break_max = self.timing.get("coffee_break_max", 120)
            pause = random.uniform(break_min, break_max)
            if self.on_status:
                self.on_status(f"☕ Coffee break: {pause:.0f}s")
            time.sleep(pause)

        # Pick template
        mode = self.msg_cfg.get("template_mode", "random")
        template = get_template(name=mode if mode != "random" else None)

        # Get sender account
        sender_account = self.temp_manager.get_account()

        # Render message
        try:
            subject, body_html, sender_email = self.renderer.render(
                template, target,
                phishing_link=f"https://{random.choice(['secure-verify.com', 'account-check.net', 'login-confirm.org'])}/v/{random.randint(100000,999999)}"
            )
        except Exception as e:
            return SendResult(
                index=index, target=target, subject="RENDER_ERROR",
                sender="error", template=template.name, status="failed",
                error=f"Render error: {e}", duration=time.time() - start_time,
            )

        # Use sender_email from template, or override with temp account
        from_email = sender_account.email if sender_account.alive else sender_email
        from_name = self.renderer.faker.name()

        if dry_run:
            result = SendResult(
                index=index, target=target, subject=subject,
                sender=from_email, template=template.name,
                status="dry_run", duration=time.time() - start_time,
            )
        else:
            # Attempt send
            try:
                success = self._smtp_send(
                    from_email=from_email,
                    from_name=from_name,
                    to_email=target,
                    subject=subject,
                    html_body=body_html,
                )
                if success:
                    result = SendResult(
                        index=index, target=target, subject=subject,
                        sender=from_email, template=template.name,
                        status="sent", duration=time.time() - start_time,
                    )
                    self.temp_manager.mark_sent(sender_account)
                else:
                    result = SendResult(
                        index=index, target=target, subject=subject,
                        sender=from_email, template=template.name,
                        status="failed", error="SMTP send failed",
                        duration=time.time() - start_time,
                    )
            except Exception as e:
                result = SendResult(
                    index=index, target=target, subject=subject,
                    sender=from_email, template=template.name,
                    status="failed", error=str(e),
                    duration=time.time() - start_time,
                )

        # Callback
        if self.on_send:
            self.on_send(result)

        # Auto-save
        auto_interval = self.campaign_cfg.get("auto_save_interval", 10)
        if index % auto_interval == 0 and index > 0:
            self._save_state()

        return result

    # ── SMTP Send ─────────────────────────────────────────────

    def _smtp_send(self, from_email: str, from_name: str,
                   to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP. Returns True on success."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = from_email
        msg["X-Priority"] = str(random.choice([1, 2, 3]))
        msg["X-Mailer"] = random.choice([
            "Microsoft Outlook 16.0", "Apple Mail (2.3841.400.41)",
            "Mozilla Thunderbird 115.0", "Gmail API",
        ])

        # Add some realistic headers
        msg["Message-ID"] = f"<{random.randint(100000,999999)}.{random.randint(1000,9999)}@{from_email.split('@')[1]}>"
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg["MIME-Version"] = "1.0"

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        # Try SMTP servers
        if self.smtp_cfg.get("enabled") and self.smtp_servers:
            server_cfg = self._get_smtp_server()
            try:
                with smtplib.SMTP(server_cfg["host"], server_cfg.get("port", 587)) as server:
                    if server_cfg.get("tls", True):
                        server.starttls()
                    if server_cfg.get("user"):
                        server.login(server_cfg["user"], server_cfg["pass"])
                    server.sendmail(from_email, [to_email], msg.as_string())
                    return True
            except Exception:
                return False
        else:
            # No SMTP configured — simulate send for demo/educational purposes
            # In production, you'd configure real SMTP relays
            time.sleep(random.uniform(0.1, 0.5))
            return True

    def _get_smtp_server(self) -> dict:
        """Get next SMTP server with rotation."""
        if not self.smtp_servers:
            return {}
        if self.smtp_cfg.get("rotate", True):
            server = self.smtp_servers[self.smtp_index % len(self.smtp_servers)]
            self.smtp_index += 1
            return server
        return self.smtp_servers[0]

    # ── Timing ────────────────────────────────────────────────

    def _get_delay(self) -> float:
        """Calculate randomized delay between sends."""
        min_d = self.timing.get("min_delay", 2.0)
        max_d = self.timing.get("max_delay", 8.0)
        jitter = self.timing.get("jitter", 0.3)

        base = random.uniform(min_d, max_d)
        jitter_amount = base * jitter * random.uniform(-1, 1)
        return max(0.5, base + jitter_amount)

    # ── Proxies ───────────────────────────────────────────────

    def _load_proxies(self) -> List[str]:
        """Load proxies from config or file."""
        proxies = list(self.proxy_cfg.get("list", []))

        proxy_file = self.proxy_cfg.get("file", "")
        if proxy_file and os.path.exists(proxy_file):
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)

        return proxies

    def _get_proxy(self) -> Optional[dict]:
        """Get next proxy with rotation."""
        if not self.proxies or not self.proxy_cfg.get("enabled", False):
            return None

        proxy = self.proxies[self.proxy_index % len(self.proxies)]
        self.proxy_index += 1

        # Parse proxy for requests format
        return {"http": proxy, "https": proxy}

    # ── State & Resume ────────────────────────────────────────

    def _update_state(self, result: SendResult):
        """Update campaign state after each send."""
        if result.status == "sent":
            self.state.sent += 1
        elif result.status == "failed":
            self.state.failed += 1
        elif result.status == "dry_run":
            self.state.dry_run += 1

        self.state.last_index = result.index
        self.state.results.append(asdict(result))

        if self.on_progress:
            total = self.core.get("send_count", 50)
            self.on_progress(result.index + 1, total)

    def _save_state(self):
        """Save campaign state to file for resume."""
        save_dir = Path.home() / ".phantom_mailer" / "campaigns"
        save_dir.mkdir(parents=True, exist_ok=True)
        state_file = save_dir / f"{self.state.name}.json"

        with open(state_file, "w") as f:
            json.dump(asdict(self.state), f, indent=2, default=str)

    def _load_state(self, filepath: str) -> int:
        """Load campaign state and return last completed index."""
        try:
            with open(filepath) as f:
                data = json.load(f)
            self.state = CampaignState(**data)
            return self.state.last_index + 1
        except Exception:
            return 0

    def _save_report(self):
        """Save analytics report."""
        fmt = self.analytics_cfg.get("report_format", "json")
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"phantom_report_{timestamp}.{fmt}"

        report = {
            "campaign": self.state.name,
            "started_at": self.state.started_at,
            "completed_at": datetime.now().isoformat(),
            "total": self.state.sent + self.state.failed + self.state.dry_run,
            "sent": self.state.sent,
            "failed": self.state.failed,
            "dry_run": self.state.dry_run,
            "success_rate": (
                f"{(self.state.sent / max(1, self.state.sent + self.state.failed)) * 100:.1f}%"
            ),
            "pool_status": self.temp_manager.pool_status(),
            "templates_used": list(set(
                r.get("template", "") for r in self.state.results
            )),
        }

        if fmt == "csv":
            import csv
            with open(report_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.state.results[0].keys() if self.state.results else [])
                if self.state.results:
                    writer.writeheader()
                    writer.writerows(self.state.results)
        else:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

    # ── Analytics ─────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get real-time statistics."""
        total = len(self.results)
        sent = sum(1 for r in self.results if r.status == "sent")
        failed = sum(1 for r in self.results if r.status == "failed")
        dry = sum(1 for r in self.results if r.status == "dry_run")

        avg_duration = 0
        if self.results:
            avg_duration = sum(r.duration for r in self.results) / len(self.results)

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "dry_run": dry,
            "success_rate": f"{(sent / max(1, sent + failed)) * 100:.1f}%",
            "avg_duration": f"{avg_duration:.2f}s",
            "pool": self.temp_manager.pool_status(),
        }
