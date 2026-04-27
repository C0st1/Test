"""
PHANTOM MAILER — Message Renderer
Takes a ScamTemplate and fills every variable with Faker-generated data.
Adds typos, signatures, urgency markers, and subject mutations.
"""

import random
import re
from typing import Optional, Tuple
from jinja2 import Template
from faker import Faker

from templates import ScamTemplate, get_template


class MessageRenderer:
    """Renders scam templates with realistic, randomized data."""

    # ── Typo engine ───────────────────────────────────────────
    COMMON_TYPOS = {
        "a": ["q", "s"],
        "e": ["w", "r"],
        "i": ["u", "o"],
        "o": ["i", "p"],
        "u": ["y", "i"],
        "n": ["b", "m"],
        "s": ["a", "d"],
        "t": ["r", "y"],
        "h": ["g", "j"],
        "r": ["e", "t"],
    }

    # ── Subject prefixes ──────────────────────────────────────
    URGENT_PREFIXES = [
        "URGENT:", "ACTION REQUIRED:", "IMPORTANT:",
        "TIME-SENSITIVE:", "IMMEDIATE ATTENTION:",
        "⚠️ ALERT:", "🚨 URGENT:", "CRITICAL:",
    ]

    CASUAL_PREFIXES = [
        "Re:", "FW:", "Fwd:", "Following up:",
    ]

    EMOJI_POOL = ["🚨", "⚠️", "🎉", "💰", "📧", "❗", "🔔", "✅", "📢", "⏰"]

    # ── Signatures ────────────────────────────────────────────
    SIGNATURES = [
        "\n\nSent from my iPhone",
        "\n\nSent from my Samsung Galaxy",
        "\n\nGet Outlook for iOS",
        "\n\n—\nConfidentiality Notice: This email is intended solely for the named recipient(s).",
        "\n\n—\nThis communication contains information that is legally privileged.",
        "",
        "",
        "",
    ]

    # ── Disclaimers ───────────────────────────────────────────
    DISCLAIMERS = [
        "\n\n---\nThis message was sent from an automated system. Do not reply directly to this email.",
        "\n\n---\nYou are receiving this email because you opted in to receive communications from us.",
        "\n\n---\nTo unsubscribe from these emails, click here.",
        "\n\n---\nThis email and any attachments are confidential and may be privileged.",
        "",
        "",
    ]

    def __init__(self, locale: str = "en_US", add_typo: bool = True,
                 add_signature: bool = True, add_disclaimer: bool = True,
                 add_urgency: bool = True):
        self.faker = Faker(locale)
        self.add_typo = add_typo
        self.add_signature = add_signature
        self.add_disclaimer = add_disclaimer
        self.add_urgency = add_urgency

    def render(self, template: ScamTemplate, target_email: str,
               phishing_link: str = "https://example.com/verify") -> Tuple[str, str, str]:
        """
        Render a template with random data.
        Returns: (subject, body_html, sender_email)
        """
        variables = self._generate_variables(template, target_email, phishing_link)

        # Render subject
        subject_template = Template(random.choice(template.subject_pool))
        subject = subject_template.render(**variables)
        subject = self._mutate_subject(subject, template.urgency_level)

        # Render body
        body_template = Template(template.body)
        body = body_template.render(**variables)

        # Replace link placeholders
        link_text = Template(template.link_text).render(**variables)
        link_line = f"\n{link_text}: {phishing_link}\n"
        body = body.replace("{{ link }}", link_line)

        # Add finishing touches
        if self.add_signature:
            body += random.choice(self.SIGNATURES)
        if self.add_disclaimer:
            body += random.choice(self.DISCLAIMERS)
        if self.add_typo and random.random() < 0.3:
            body = self._inject_typo(body)

        # Wrap in basic HTML
        body_html = self._wrap_html(body, subject)

        sender_name = variables.get("sender_name", self.faker.name())
        sender_email = self._make_sender_email(sender_name, template.category)

        return subject, body_html, sender_email

    def _generate_variables(self, template: ScamTemplate,
                            target_email: str, link: str) -> dict:
        """Generate all variables needed by any template."""
        f = self.faker
        recipient_name = f.first_name()
        target_local = target_email.split("@")[0] if "@" in target_email else target_email

        # Core variables used across multiple templates
        base = {
            # Recipient
            "recipient_name": recipient_name,
            "recipient_email": target_email,

            # Sender
            "sender_name": f.name(),
            "sender_title": random.choice(["Mr.", "Dr.", "Prof.", "Barr.", "Sir", ""]),
            "sender_age": random.randint(28, 45),
            "sender_location": f"{f.city()}, {f.country()}",
            "sender_origin": f.country(),
            "sender_occupation": f.job(),
            "sender_chamber": f"{f.last_name()} & Associates Legal Chambers",

            # General
            "organization": random.choice([
                "Global International Lottery", "Microsoft Promotion Board",
                "UK National Lottery", "European Gaming Commission",
                "World Bank Development Fund", "UN Grants Division",
            ]),
            "ref_number": f"REF-{random.randint(100000, 999999)}",
            "date": f.date(),
            "current_date": f.date(),
            "timestamp": f.date_time().isoformat(),
            "link": link,

            # Financial
            "prize_amount": f"${random.randint(1, 10)},{random.randint(100,999)},{random.randint(100,999)}",
            "prize_amount_words": f"{random.choice(['one','two','three','four','five'])} million dollars",
            "amount": f"${random.randint(1,25)},{random.randint(100,999)},{random.randint(100,999)}",
            "amount_words": f"{random.randint(5,25)} million {random.choice(['dollars','pounds','euros'])}",
            "small_amount": f"${random.randint(100, 500)}",
            "big_amount": f"${random.randint(50,500)},{random.randint(100,999)}",

            # Lottery-specific
            "ticket_number": f"TKT-{random.randint(10000,99999)}-{random.choice('ABCDEFGH')}",
            "lucky_numbers": f"{random.randint(1,49)}-{random.randint(1,49)}-{random.randint(1,49)}-{random.randint(1,49)}-{random.randint(1,49)}-{random.randint(1,49)}",
            "draw_date": f.date_between(start_date="-30d", end_date="today").strftime("%B %d, %Y"),
            "db_size": f"{random.randint(50,500)} million",
            "claim_deadline": random.randint(14, 30),
            "agent_name": f.name(),
            "agent_email": f"agent.{random.randint(100,999)}@{f.free_email_domain()}",

            # Bank phishing
            "bank_name": random.choice([
                "Chase Bank", "Wells Fargo", "Bank of America",
                "Citibank", "HSBC", "Barclays", "Capital One",
            ]),
            "account_last_four": f"{random.randint(1000,9999)}",
            "suspicious_date": f.date_between(start_date="-7d", end_date="today").strftime("%B %d, %Y"),
            "suspicious_time": f"{random.randint(0,23):02d}:{random.randint(0,59):02d}",
            "suspicious_location": f"{f.city()}, {f.country()}",
            "suspicious_ip": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "suspicious_device": random.choice([
                "Chrome/Windows", "Firefox/MacOS", "Safari/iPhone",
                "Chrome/Android", "Edge/Windows", "Unknown Device",
            ]),
            "verify_deadline": random.choice([24, 48, 72]),

            # Inheritance
            "deceased_name": f.name(),
            "deceased_company": f.company(),
            "deceased_location": f"{f.city()}, {f.country()}",
            "death_date": f.date_between(start_date="-365d", end_date="-30d").strftime("%B %d, %Y"),
            "your_percentage": 30,
            "my_percentage": 60,
            "other_percentage": 10,
            "position": random.choice([
                "Director", "Chief Accountant", "Auditor General",
                "Finance Minister", "Secretary", "Chairman",
            ]),
            "region": random.choice([
                "Lagos State", "Abuja Capital Territory", "Rivers State",
                "Accra Region", "Nairobi County",
            ]),
            "country": random.choice(["Nigeria", "Ghana", "Senegal", "Ivory Coast", "Kenya"]),
            "predecessor_relation": random.choice(["father", "predecessor", "late husband", "colleague"]),
            "vault_location": random.choice(["Amsterdam", "London", "Geneva", "Abidjan"]),

            # Romance
            "lost_relative": random.choice(["spouse", "parent", "sibling", "fiancé"]),

            # Tech support
            "os_name": random.choice(["Windows 11", "Windows 10", "macOS", "Android"]),
            "company_name": random.choice([
                "Microsoft Support", "Apple Security", "Google Protection",
                "Norton Security", "McAfee Total Protection",
            ]),
            "threat_type": random.choice([
                "Trojan.Win32.Generic", "Ransomware.Cryptolock",
                "Adware.BrowserHijack", "Spyware.Keylogger",
                "Malware.GenericKD", "PUP.Optional.SearchBar",
            ]),
            "infected_count": random.randint(3, 47),
            "detection_date": f.date_between(start_date="-3d", end_date="today").strftime("%B %d, %Y"),
            "device_id": f"DEV-{random.randint(10000,99999)}-{random.choice('ABCDEF')}",
            "license_key": f"{'-'.join([f'{random.randint(1000,9999)}' for _ in range(4)])}",
            "license_expiry": f.date_between(start_date="today", end_date="+365d").strftime("%B %d, %Y"),
            "support_phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",

            # Job offer
            "job_title": random.choice([
                "Data Entry Specialist", "Customer Service Representative",
                "Virtual Assistant", "Mystery Shopper",
                "Payment Processing Agent", "Administrative Coordinator",
            ]),
            "salary": f"${random.randint(500,2000)}",
            "company_name": f.company() + " " + random.choice(["Inc.", "LLC", "Corp.", "Ltd.", "Group"]),
            "job_board": random.choice(["LinkedIn", "Indeed", "Glassdoor", "ZipRecruiter", "CareerBuilder"]),
            "hours_per_week": random.randint(10, 30),
            "application_deadline": random.randint(24, 72),
            "hr_name": f.name(),
            "company_website": f"https://www.{f.domain_word()}.com",
            "responsibility_1": random.choice([
                "Processing customer payments and transactions",
                "Managing correspondence and scheduling",
                "Reviewing and verifying financial documents",
                "Coordinating logistics for product shipments",
            ]),
            "responsibility_2": random.choice([
                "Maintaining accurate records of all transactions",
                "Communicating with clients via email and phone",
                "Preparing weekly activity reports",
                "Assisting with marketing campaigns",
            ]),
            "responsibility_3": random.choice([
                "Ensuring compliance with company policies",
                "Handling confidential information with discretion",
                "Providing excellent customer support",
                "Supporting senior management with administrative tasks",
            ]),

            # PayPal
            "deadline_hours": random.choice([24, 48, 72]),

            # Crypto
            "coin_name": random.choice(["Bitcoin", "Ethereum", "Solana", "Cardano", "XRP"]),
            "platform_name": random.choice(["CryptoVault", "TradeBlade", "CoinForge", "BlockProfit", "CryptoEdge"]),
            "min_investment": f"${random.randint(250,500)}",
            "monthly_earnings": f"${random.randint(5000,50000):,}",
            "roi_percentage": random.randint(15, 85),
            "month_1": f.date_between(start_date="-90d", end_date="-60d").strftime("%b %Y"),
            "month_2": f.date_between(start_date="-60d", end_date="-30d").strftime("%b %Y"),
            "month_3": f.date_between(start_date="-30d", end_date="today").strftime("%b %Y"),
            "return_1": random.randint(12, 45),
            "return_2": random.randint(8, 65),
            "return_3": random.randint(15, 80),
            "available_spots": random.randint(3, 15),
            "trader_name": f.first_name(),
            "earnings": f"${random.randint(10000,100000):,}",

            # Government grant
            "agency_name": random.choice([
                "Federal Grant Administration", "Department of Housing and Urban Development",
                "Small Business Administration", "Department of Education",
                "Health and Human Services", "Federal Emergency Management Agency",
            ]),
            "grant_amount": f"${random.randint(5000,50000):,}",
            "program_name": random.choice([
                "Community Development Block Grant",
                "Economic Impact Payment Program",
                "Homeowner Assistance Fund",
                "Emergency Rental Assistance Program",
            ]),
            "grant_id": f"FG-{random.randint(10000,99999)}",
            "income_threshold": f"${random.randint(30000,75000):,}",
            "claim_deadline": f.date_between(start_date="today", end_date="+30d").strftime("%B %d, %Y"),
            "disbursement_days": random.randint(3, 10),
            "agency_address": f.address().replace('\n', ', '),
            "ref_number": f"REF-{random.randint(100000,999999)}",

            # Shipping
            "carrier": random.choice(["FedEx", "UPS", "USPS", "DHL", "Amazon Logistics"]),
            "tracking_number": f"{random.choice(['1Z','FDX','1H','JV'])}{random.randint(1000000000,9999999999)}",
            "failure_reason": random.choice([
                "Incorrect shipping address",
                "No one available to sign for the package",
                "Customs clearance required",
                "Address verification needed",
                "Insufficient postage",
            ]),
            "package_weight": f"{random.uniform(0.5, 15.0):.1f} kg",
            "holding_location": f.city(),
            "order_number": f"ORD-{random.randint(100000,999999)}",
            "store_name": random.choice(["Amazon", "Walmart", "Target", "Best Buy", "eBay"]),
            "hold_days": random.randint(5, 14),
            "return_fee": f"${random.randint(5,25)}.99",
            "holding_address": f.address(),
            "holding_hours": "Mon-Fri 9:00 AM - 6:00 PM",
            "support_phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",

            # Charity
            "charity_name": random.choice([
                "Children's Hope Alliance", "Global Water Initiative",
                "Mercy Without Borders", "Voices for the Vulnerable",
                "Shelter & Future Foundation",
            ]),
            "mission_description": random.choice([
                "clean water, education, and healthcare to underserved communities",
                "emergency shelter and long-term housing solutions",
                "medical aid and nutritional support to children in crisis",
            ]),
            "years_active": random.randint(8, 35),
            "crisis_name": random.choice([
                "Hurricane Relief", "Flood Recovery", "Earthquake Response",
                "Famine Emergency", "Displacement Crisis",
            ]),
            "crisis_location": random.choice([
                "Southeast Asia", "East Africa", "Central America",
                "the Caribbean", "the Middle East",
            ]),
            "affected_count": f"{random.randint(10000,500000):,}",
            "small_donation": f"${random.randint(10,25)}",
            "medium_donation": f"${random.randint(50,100)}",
            "large_donation": f"${random.randint(100,500)}",
            "donation_amount": f"${random.randint(25,100)}",
            "water_people": random.randint(5, 25),
            "family_size": random.randint(4, 7),
            "medical_patients": random.randint(2, 10),
            "director_name": f.name(),
            "ein_number": f"{random.randint(10,99)}-{random.randint(1000000,9999999)}",

            # Account recovery
            "service_name": random.choice([
                "Google", "Microsoft", "Apple", "Netflix", "Facebook",
                "Instagram", "Twitter/X", "Amazon", "Spotify",
            ]),
            "reset_expiry": random.choice([15, 30, 60]),

            # Subscription
            "plan_name": random.choice(["Premium", "Pro", "Business", "Enterprise", "Plus"]),
            "payment_method": f"Visa ending in {random.randint(1000,9999)}",
            "billing_cycle": random.choice(["Monthly", "Annual"]),
            "next_billing_date": f.date_between(start_date="+1d", end_date="+30d").strftime("%B %d, %Y"),
            "cancel_window": random.randint(12, 72),
            "support_email": f"support@{f.domain_word()}.com",

            # Health
            "health_org": random.choice([
                "National Health Institute", "CDC Prevention Services",
                "World Health Outreach", "Public Health Alert System",
            ]),
            "condition_name": random.choice([
                "Hepatitis A exposure", "respiratory infection cluster",
                "contaminated water supply effects", "seasonal influenza variant",
            ]),
            "treatment_name": random.choice([
                "vaccination", "antiviral treatment", "preventive medication", "screening program"
            ]),
            "benefit_amount": f"${random.randint(500,5000):,}",
            "affected_region": f"{f.city()}, {f.state_abbr()}",
            "enrollment_deadline": f.date_between(start_date="today", end_date="+14d").strftime("%B %d, %Y"),
            "priority_access": random.choice(["specialists", "treatment centers", "clinical trials"]),
            "org_address": f.address().replace('\n', ', '),
            "reference_number": f"PHA-{random.randint(100000,999999)}",

            # Loan
            "loan_amount": f"${random.randint(5000,50000):,}",
            "lender_name": random.choice([
                "QuickCash Financial", "GreenLight Lending",
                "SwiftLoan Direct", "TrueRate Capital", "EasyFund Loans",
            ]),
            "interest_rate": round(random.uniform(3.5, 12.9), 1),
            "loan_term": random.choice([12, 24, 36, 48, 60]),
            "monthly_payment": f"${random.randint(150,800)}",
            "funding_speed": random.choice(["24 hours", "the next business day", "48 hours"]),
            "approval_validity": random.randint(3, 14),
            "lender_address": f.address().replace('\n', ', '),
            "nmls_number": random.randint(100000, 999999),

            # Domain/SEO
            "domain_name": f"{target_local}.com",
            "competitor_domain": f"{target_local}-{random.choice(['online','site','net','org'])}.com",
            "visitor_loss": random.randint(30, 80),
            "site_name": target_local,
            "issue_count": random.randint(5, 25),
            "requester_company": f.company() + " " + random.choice(["LLC", "Inc.", "Ltd."]),
            "similar_domain_1": f"{target_local}-{random.choice(['shop','store','app','io'])}.com",
            "similar_domain_2": f"my{target_local}.com",
            "stated_purpose": random.choice([
                "e-commerce operations", "digital marketing campaigns",
                "brand development", "online service delivery",
            ]),
            "priority_window": random.randint(24, 72),
            "registry_name": random.choice(["Domain Protection Services", "Global Domain Registry", "Trademark Domain Watch"]),
            "registry_address": f.address().replace('\n', ', '),
            "case_number": f"DW-{random.randint(100000,999999)}",
        }

        return base

    def _mutate_subject(self, subject: str, urgency: int) -> str:
        """Add prefixes, emojis, and mutations to subject line."""
        # Urgency prefix
        if self.add_urgency and random.random() < (urgency / 5.0) * 0.6:
            if urgency >= 4:
                subject = f"{random.choice(self.URGENT_PREFIXES)} {subject}"
            else:
                subject = f"{random.choice(self.CASUAL_PREFIXES)} {subject}"

        # Emoji
        if random.random() < 0.3:
            subject = f"{random.choice(self.EMOJI_POOL)} {subject}"

        return subject

    def _inject_typo(self, text: str) -> str:
        """Inject a single realistic typo into the text."""
        # Pick a random word to typo-ify
        words = text.split()
        if len(words) < 10:
            return text

        # Pick a word that's at least 4 chars and contains a swappable letter
        candidates = [(i, w) for i, w in enumerate(words) if len(w) >= 4]
        if not candidates:
            return text

        idx, word = random.choice(candidates)
        for char_idx, char in enumerate(word.lower()):
            if char in self.COMMON_TYPOS and random.random() < 0.3:
                replacement = random.choice(self.COMMON_TYPOS[char])
                new_word = word[:char_idx] + replacement + word[char_idx + 1:]
                words[idx] = new_word
                break

        return " ".join(words)

    def _make_sender_email(self, name: str, category: str) -> str:
        """Generate a plausible sender email address."""
        first = name.split()[0].lower() if name else "info"
        last = name.split()[-1].lower() if name and len(name.split()) > 1 else ""

        domain_map = {
            "prize": ["lottery-intl.com", "winners-portal.net", "prize-central.org"],
            "phishing": ["secure-verify.com", "account-alert.net", "login-secure.org"],
            "financial": ["fiduciary-services.com", "private-bank.net", "global-finance.org"],
            "romance": ["heart-connect.com", "soulmates.net", "love-letters.org"],
            "employment": ["careers-hr.com", "job-connect.net", "recruit-direct.org"],
            "charity": ["hope-foundation.org", "relief-fund.net", "giving-hands.org"],
            "business": ["domain-services.com", "brand-protection.net", "registry-solutions.com"],
        }

        domains = domain_map.get(category, ["info-services.com", "secure-mail.net"])
        domain = random.choice(domains)

        patterns = [
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
            f"info@{domain}",
            f"support@{domain}",
            f"admin@{domain}",
        ]

        return random.choice(patterns)

    def _wrap_html(self, body: str, subject: str) -> str:
        """Wrap plain text body in a basic HTML email structure."""
        # Convert newlines to <br> and basic formatting
        html_body = body.replace("\n\n", "</p><p>").replace("\n", "<br>")
        html_body = f"<p>{html_body}</p>"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         font-size: 14px; line-height: 1.6; color: #333;
         max-width: 600px; margin: 0 auto; padding: 20px; }}
  a {{ color: #0066cc; text-decoration: underline; }}
  p {{ margin: 0 0 12px 0; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
