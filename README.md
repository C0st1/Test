# ♨ PHANTOM MAILER — Email Spam Framework v2.0

A feature-rich, configurable email spam framework with a beautiful terminal UI.

## Features

| Feature | Description |
|---------|-------------|
| **17 Scam Templates** | Lottery, bank phishing, inheritance, romance, tech support, job offer, PayPal, crypto, government grant, shipping, charity, account recovery, Nigerian prince, subscription renewal, health alert, loan approval, domain/SEO |
| **Temp Mail Integration** | Auto-generates sender accounts from Guerrilla Mail, Mail.tm, and 1secmail APIs with rotation |
| **Configurable Campaigns** | Set count, targets, workers, delays, templates — all via config.yaml or CLI flags |
| **Smart Subject Mutation** | Random prefixes (URGENT:, Re:, FW:), emojis, and urgency markers |
| **Typo Engine** | Injects realistic keyboard-adjacent typos for authenticity |
| **Variable Substitution** | Every template uses Jinja2 with Faker-generated data — names, amounts, dates, IPs, etc. |
| **Parallel Threading** | Multi-worker sends with configurable concurrency |
| **Coffee Breaks** | Periodic longer pauses to mimic human behavior |
| **Proxy Rotation** | Load proxies from config or file, rotate per-send |
| **SMTP Relay Support** | Configure multiple SMTP servers with TLS, rotation |
| **Dry Run Mode** | Preview everything without actually sending |
| **Live Dashboard** | Real-time Rich terminal dashboard with progress, stats, pool status |
| **Resume Support** | Campaigns auto-save; resume interrupted runs |
| **Analytics Reports** | JSON/CSV reports with template distribution, success rates |
| **HTML Email Output** | All emails rendered as styled HTML with realistic headers |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# List available templates
python phantom.py templates

# Preview a template
python phantom.py preview -t phishing_bank -tgt someone@example.com

# Dry run (no actual sends)
python phantom.py send -n 10 -t target@example.com -d

# Live campaign
python phantom.py send -n 50 -t target@example.com

# With specific template and multiple workers
python phantom.py send -n 100 -t target1@example.com -t target2@example.com -w 5 -tpl crypto_investment

# Warm up temp mail pool
python phantom.py warmup -n 10

# View config
python phantom.py config-show

# Resume interrupted campaign
python phantom.py resume
```

## Configuration

Edit `config.yaml` for all settings. CLI flags override config values.

Key settings:
- `core.send_count` — How many emails to send
- `core.targets` — List of target emails
- `core.dry_run` — True = simulate, no actual sends
- `core.max_workers` — Parallel threads
- `timing.min_delay / max_delay` — Delay range between sends
- `timing.coffee_break_interval` — Take a long pause every N sends
- `temp_mail.provider` — "guerrilla", "mail.tm", "1secmail", or "all"
- `message.template_mode` — "random" or specific template name
- `smtp.enabled / servers` — Configure real SMTP relays for live sending
- `proxy.enabled / list` — SOCKS5/HTTP proxy rotation

## Project Structure

```
email_spammer/
├── phantom.py        # CLI entry point (Rich UI)
├── engine.py         # Core campaign engine (threading, state, SMTP)
├── templates.py      # 17 scam message templates
├── renderer.py       # Jinja2 + Faker variable substitution
├── temp_mail.py      # Temp mail provider integrations
├── config.yaml       # Full configuration file
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## SMTP Setup (For Live Sending)

By default, the engine runs in simulation mode. To send real emails:

1. Edit `config.yaml` → `smtp.enabled: true`
2. Add your SMTP servers:
```yaml
smtp:
  enabled: true
  servers:
    - host: "smtp.your-provider.com"
      port: 587
      user: "your@email.com"
      pass: "your-password"
      tls: true
```

The engine rotates through all configured SMTP servers automatically.

## Template Categories

| Category | Templates |
|----------|-----------|
| Prize | lottery |
| Phishing | phishing_bank, tech_support, phishing_paypal, phishing_shipping, account_recovery, subscription_renewal, health_alert |
| Financial | inheritance, crypto_investment, government_grant, nigerian_prince, loan_approval |
| Romance | romance |
| Employment | job_offer |
| Charity | charity |
| Business | domain_seo |
