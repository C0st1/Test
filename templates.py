"""
PHANTOM MAILER — Scam Message Templates
Every template uses Jinja2-style {{ variable }} substitution.
Variables are auto-filled by Faker + random pickers.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import random


@dataclass
class ScamTemplate:
    """A single scam email template with all its variants."""
    name: str
    category: str
    subject_pool: List[str]
    body: str
    urgency_level: int = 3          # 1-5, affects prefix probability
    requires_link: bool = True
    link_text: str = "Click here to proceed"
    attachment_hint: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  TEMPLATE LIBRARY
# ═══════════════════════════════════════════════════════════════

TEMPLATES: List[ScamTemplate] = [

    # ── 1. Lottery / Prize ────────────────────────────────────
    ScamTemplate(
        name="lottery",
        category="prize",
        subject_pool=[
            "You Have Won {{ prize_amount }}!",
            "CONGRATULATIONS! Your Email Won!",
            "Official Notification: Lottery Winner",
            "{{ organization }} - Prize Notification #{{ ref_number }}",
            "Your Ticket Won {{ prize_amount }} - Claim Now",
        ],
        body="""Dear {{ recipient_name }},

We are pleased to inform you that your email address has been selected as one of the winners in the {{ organization }} International Email Lottery held on {{ draw_date }}.

Your email, attached to ticket number {{ ticket_number }}, drew the lucky numbers {{ lucky_numbers }} and has won you a total sum of {{ prize_amount }} ({{ prize_amount_words }}).

This lottery was conducted from a database of over {{ db_size }} email addresses collected from all over the world, and your email was selected through a computer ballot system.

To claim your prize, please contact our fiduciary agent:

    Name:  {{ agent_name }}
    Email: {{ agent_email }}

You must file your claim within {{ claim_deadline }} days of this notification. After this period, all unclaimed funds will be returned to the treasury.

Please provide the following when claiming:
- Full name and address
- Country of residence
- Telephone number
- A copy of your identification

{{ link }}

Congratulations once again from all members of our staff.

Yours faithfully,
{{ sender_name }}
{{ sender_title }}
{{ organization }}""",
        urgency_level=4,
        link_text="Submit Your Claim Form",
    ),

    # ── 2. Bank Phishing ──────────────────────────────────────
    ScamTemplate(
        name="phishing_bank",
        category="phishing",
        subject_pool=[
            "Security Alert: Unusual Activity on Your Account",
            "Action Required: Account Verification Needed",
            "{{ bank_name }} - Account Suspended",
            "Important: Your {{ bank_name }} Account Has Been Limited",
            "Verify Your Identity - {{ bank_name }}",
        ],
        body="""Dear {{ recipient_name }},

We are contacting you regarding your {{ bank_name }} account ending in {{ account_last_four }}.

Our security system detected unusual login activity on your account from an unrecognized device on {{ suspicious_date }} at {{ suspicious_time }}.

Location: {{ suspicious_location }}
IP Address: {{ suspicious_ip }}
Device: {{ suspicious_device }}

If this was you, no further action is needed. However, if you do not recognize this activity, your account may be compromised.

To secure your account immediately:

{{ link }}

You will be asked to verify your identity and update your security information. This process takes approximately 3-5 minutes.

Please note: If we do not receive a response within {{ verify_deadline }} hours, your account will be temporarily suspended as a precautionary measure.

We take the security of your account seriously and apologize for any inconvenience.

Security Team
{{ bank_name }}
{{ bank_address }}

This is an automated message. Please do not reply to this email.""",
        urgency_level=5,
        link_text="Secure My Account Now",
    ),

    # ── 3. Inheritance / Next of Kin ──────────────────────────
    ScamTemplate(
        name="inheritance",
        category="financial",
        subject_pool=[
            "Confidential Business Proposal",
            "Inheritance Fund - {{ amount }}",
            "URGENT: Deceased Client Fund",
            "Private Matter Regarding {{ deceased_name }}",
            "Business Opportunity - Strictly Confidential",
        ],
        body="""Dear {{ recipient_name }},

I am {{ sender_name }}, a legal practitioner based in {{ sender_location }}. I am writing you this email based on a business opportunity that will be of mutual benefit to both of us.

I was the personal attorney to the late {{ deceased_name }}, a national of your country who worked with {{ deceased_company }} here in {{ deceased_location }}.

On {{ death_date }}, my client and his entire family were involved in a fatal accident that claimed their lives. Since then, I have made several inquiries to your embassy to locate any extended relatives, but all efforts have proved unsuccessful.

Before his death, my client deposited the sum of {{ amount }} ({{ amount_words }}) in a security company here. The security company has mandated me to present a next of kin to claim the funds, otherwise the deposit will be forfeited to the government.

Based on this, I am seeking your consent to present you as the next of kin to the deceased so that the proceeds of this deposit can be released to you for our mutual benefit.

The transaction is 100% risk-free. All I require is your honest cooperation to enable us see this deal through. I will handle all legal documentation to put you in place as the beneficiary.

{{ link }}

I await your urgent response.

Best regards,
{{ sender_name }}
{{ sender_title }}
{{ sender_chamber }}

CONFIDENTIALITY NOTICE: This email is intended only for the addressee. If you have received this in error, please delete immediately.""",
        urgency_level=3,
        link_text="Express Your Interest",
    ),

    # ── 4. Romance / Dating ───────────────────────────────────
    ScamTemplate(
        name="romance",
        category="romance",
        subject_pool=[
            "Hello From {{ sender_name }} - I Saw Your Profile",
            "You Seem Interesting - Let's Connect",
            "Looking for Someone Special",
            "{{ sender_name }} Wants to Meet You",
            "A Message From Someone Who Cares",
        ],
        body="""Hello {{ recipient_name }},

I know this might come as a surprise, but I came across your profile and felt compelled to write to you. My name is {{ sender_name }}, I'm {{ sender_age }} years old, and I'm currently based in {{ sender_location }}.

I'll be honest — I've been through a lot lately. I lost my {{ lost_relative }} last year and have been trying to rebuild my life. I'm {{ sender_occupation }}, originally from {{ sender_origin }}, and I'm looking for someone genuine to connect with.

There's something about your profile that made me feel like you might understand what it's like to go through difficult times and still keep hope alive.

I'm not looking for anything complicated — just a real connection with someone who values honesty and loyalty. I have a lot of love to give to the right person.

I have photos I'd love to share and would really appreciate it if you could write back. Even just a few words would mean the world to me.

{{ link }}

I hope to hear from you soon. Until then, know that someone out there is thinking of you.

With warmth,
{{ sender_name }}""",
        urgency_level=2,
        link_text="Reply to {{ sender_name }}",
        requires_link=True,
    ),

    # ── 5. Tech Support Scam ─────────────────────────────────
    ScamTemplate(
        name="tech_support",
        category="phishing",
        subject_pool=[
            "Your {{ os_name }} License Has Expired",
            "Critical Security Update Required - {{ os_name }}",
            "Virus Detected on Your Device",
            "{{ company_name }} Support: Renewal Required",
            "Immediate Action: {{ threat_type }} Detected",
        ],
        body="""Dear {{ recipient_name }},

This is an automated notification from {{ company_name }} Technical Support.

Our monitoring system has detected {{ threat_type }} on your {{ os_name }} device registered to {{ recipient_email }}.

Detection Details:
    Threat Type:     {{ threat_type }}
    Risk Level:      CRITICAL
    Infected Files:  {{ infected_count }}
    Date Detected:   {{ detection_date }}
    Device ID:       {{ device_id }}

If left unresolved, this threat may result in:
- Complete data loss
- Identity theft
- Financial information compromise
- Device malfunction

To resolve this issue immediately:

{{ link }}

Our certified technicians are available 24/7 to assist you. The repair process takes approximately 10-15 minutes.

Support License: {{ license_key }}
Valid Until:     {{ license_expiry }}

Do NOT restart your device or attempt manual removal, as this may cause permanent data corruption.

{{ company_name }} Technical Support
{{ support_phone }}""",
        urgency_level=5,
        link_text="Start Remote Repair",
    ),

    # ── 6. Employment / Job Offer ─────────────────────────────
    ScamTemplate(
        name="job_offer",
        category="employment",
        subject_pool=[
            "Job Opportunity - {{ job_title }} - {{ salary }}",
            "We Want to Hire You - {{ company_name }}",
            "Your Application Has Been Reviewed",
            "Remote Position Available - {{ job_title }}",
            "Part-Time Role - Earn {{ salary }}/week",
        ],
        body="""Dear {{ recipient_name }},

I'm {{ hr_name }}, HR Director at {{ company_name }}. We came across your resume on {{ job_board }} and were impressed by your qualifications.

We are currently seeking candidates for a remote {{ job_title }} position. This is a flexible, work-from-home opportunity with the following details:

Position:    {{ job_title }}
Salary:      {{ salary }} per week
Hours:       {{ hours_per_week }} hours/week (flexible schedule)
Start Date:  Immediately
Location:    100% Remote

Key Responsibilities:
- {{ responsibility_1 }}
- {{ responsibility_2 }}
- {{ responsibility_3 }}

What We Provide:
- Competitive weekly compensation
- Comprehensive training (no experience required)
- All necessary equipment shipped to you
- Health benefits after 90 days

To proceed with your application:

{{ link }}

Please note that positions are filling quickly. We recommend submitting your application within {{ application_deadline }} hours.

We look forward to having you on the team.

Best regards,
{{ hr_name }}
HR Director
{{ company_name }}
{{ company_website }}""",
        urgency_level=3,
        link_text="Complete Your Application",
    ),

    # ── 7. PayPal / Payment Phishing ──────────────────────────
    ScamTemplate(
        name="phishing_paypal",
        category="phishing",
        subject_pool=[
            "Your PayPal Account Has Been Limited",
            "Payment of {{ amount }} Received - Confirm",
            "Action Required: PayPal Security Alert",
            "You've Received {{ amount }} on PayPal",
            "PayPal: Unrecognized Device Login",
        ],
        body="""Dear {{ recipient_name }},

We noticed unusual activity on your PayPal account and have temporarily limited access to protect your information.

What Happened:
On {{ suspicious_date }}, a payment of {{ amount }} was attempted from a device we didn't recognize:

    Device:   {{ suspicious_device }}
    Location: {{ suspicious_location }}
    IP:       {{ suspicious_ip }}

If this was you, you can disregard this message. If not, someone may be trying to access your account.

To Restore Access:

{{ link }}

You'll need to confirm your identity and update your security settings. This takes about 2 minutes.

If we don't hear from you within {{ deadline_hours }} hours, your account will remain limited and you won't be able to:
- Send or receive payments
- Withdraw funds
- Access your transaction history

We're here to help. If you have questions, visit our Help Center.

Thanks for being a PayPal customer.

PayPal Security Team

Please do not reply to this email. This mailbox is not monitored.""",
        urgency_level=5,
        link_text="Restore My Account Access",
    ),

    # ── 8. Crypto Investment ──────────────────────────────────
    ScamTemplate(
        name="crypto_investment",
        category="financial",
        subject_pool=[
            "Turn {{ small_amount }} into {{ big_amount }} - Crypto Secret",
            "Exclusive Crypto Opportunity - Invite Only",
            "{{ coin_name }} Is About to Moon - Insider Info",
            "I Made {{ earnings }} Last Month - You Can Too",
            "Limited Spots: {{ platform_name }} Trading Group",
        ],
        body="""Hey {{ recipient_name }},

I'm not going to waste your time with a long pitch. I'll keep it real.

Six months ago, I was working a dead-end job and barely paying rent. Today, I'm clearing {{ monthly_earnings }} a month through automated crypto trading on {{ platform_name }}.

I'm not a financial guru. I'm not a tech genius. I just followed a system that works, and now I want to share it with a few select people.

Here's the deal:
- Minimum investment: {{ min_investment }}
- Average ROI: {{ roi_percentage }}% monthly
- Automated trading bot handles everything
- Withdraw profits anytime
- 30-day money-back guarantee

My last three months of returns:
    {{ month_1 }}: +{{ return_1 }}%
    {{ month_2 }}: +{{ return_2 }}%
    {{ month_3 }}: +{{ return_3 }}%

I'm opening up {{ available_spots }} spots in our private trading group this month. Once they're filled, the door closes.

{{ link }}

Don't take my word for it — try it with the minimum and see the results for yourself.

Talk soon,
{{ trader_name }}
{{ platform_name }} Senior Trader

P.S. The market is moving RIGHT NOW. Every day you wait is money left on the table.""",
        urgency_level=4,
        link_text="Reserve Your Spot Now",
    ),

    # ── 9. Government Grant ───────────────────────────────────
    ScamTemplate(
        name="government_grant",
        category="financial",
        subject_pool=[
            "You Qualify for a {{ grant_amount }} Government Grant",
            "Federal Grant Program - Your Name Was Selected",
            "{{ agency_name }} Grant Approval Notice",
            "Free Government Money - No Repayment Required",
            "Grant Award #{{ grant_id }} - {{ grant_amount }}",
        ],
        body="""Dear {{ recipient_name }},

This is an official notification from the {{ agency_name }}.

You have been selected to receive a government grant of {{ grant_amount }} under the {{ program_name }} initiative. This grant does not require repayment and is available to eligible citizens based on the following criteria:

Eligibility Requirements:
    - Must be a legal resident
    - Must be at least 18 years of age
    - Annual income below {{ income_threshold }}

Your Selection Details:
    Grant ID:       {{ grant_id }}
    Amount:         {{ grant_amount }}
    Program:        {{ program_name }}
    Deadline:       {{ claim_deadline }}

To claim your grant, you must complete the verification process before {{ claim_deadline }}. After verification, funds will be disbursed to your preferred payment method within {{ disbursement_days }} business days.

{{ link }}

Note: There are no fees associated with claiming this grant. If anyone asks you to pay to receive your grant, please report it immediately.

{{ agency_name }}
{{ agency_address }}

This is an official government communication. Reference #: {{ ref_number }}""",
        urgency_level=4,
        link_text="Verify and Claim Your Grant",
    ),

    # ── 10. Amazon / Shipping Phishing ────────────────────────
    ScamTemplate(
        name="phishing_shipping",
        category="phishing",
        subject_pool=[
            "Your {{ carrier }} Package Could Not Be Delivered",
            "{{ carrier }} Delivery Exception - Action Needed",
            "Package Held at Customs - {{ tracking_number }}",
            "Delivery Failed - Schedule Redelivery",
            "{{ store_name }}: Your Order #{{ order_number }} Needs Attention",
        ],
        body="""Hello {{ recipient_name }},

We were unable to deliver your package today due to the following reason:

    Reason:    {{ failure_reason }}
    Carrier:   {{ carrier }}
    Tracking:  {{ tracking_number }}
    Weight:    {{ package_weight }}

Your package is currently being held at our {{ holding_location }} facility and requires your attention.

To schedule a redelivery or update your delivery preferences:

{{ link }}

Please note: If the package is not claimed within {{ hold_days }} business days, it will be returned to the sender and a return fee of {{ return_fee }} will be applied.

You may also pick up your package in person at:

{{ holding_address }}
Hours: {{ holding_hours }}

For questions, contact us at {{ support_phone }}.

{{ carrier }} Customer Service

This is an automated message. Do not reply.""",
        urgency_level=4,
        link_text="Schedule Redelivery",
    ),

    # ── 11. Charity / Donation ────────────────────────────────
    ScamTemplate(
        name="charity",
        category="charity",
        subject_pool=[
            "{{ charity_name }} Needs Your Help Today",
            "A Child Is Waiting - {{ charity_name }}",
            "Your Donation Can Save Lives",
            "{{ crisis_name }} Emergency Relief - Act Now",
            "{{ donation_amount }} Can Change Everything",
        ],
        body="""Dear {{ recipient_name }},

I'm writing to you on behalf of {{ charity_name }}, a registered nonprofit organization that has been providing {{ mission_description }} for over {{ years_active }} years.

Right now, {{ crisis_name }} is devastating communities across {{ crisis_location }}. Over {{ affected_count }} families have been displaced, and the situation is worsening by the hour.

What your donation provides:
    {{ small_donation }}  - Clean water for {{ water_people }} people for a month
    {{ medium_donation }} - Emergency shelter for a family of {{ family_size }}
    {{ large_donation }}  - Complete medical care for {{ medical_patients }} patients

Every dollar goes directly to relief efforts. Our administrative costs are covered by separate grants, so 100% of your donation reaches those in need.

{{ link }}

The need is urgent. These families can't wait for tomorrow. Neither can we.

With gratitude,
{{ director_name }}
Executive Director
{{ charity_name }}

{{ charity_name }} is a registered 501(c)(3) organization. EIN: {{ ein_number }}. All donations are tax-deductible.""",
        urgency_level=3,
        link_text="Donate Now",
    ),

    # ── 12. Account Recovery / Password Reset ─────────────────
    ScamTemplate(
        name="account_recovery",
        category="phishing",
        subject_pool=[
            "Password Reset Request - {{ service_name }}",
            "Your {{ service_name }} Password Has Been Changed",
            "Unauthorized Access to Your {{ service_name }} Account",
            "{{ service_name }} Security: Reset Your Password",
            "Someone Tried to Access Your {{ service_name }}",
        ],
        body="""Hi {{ recipient_name }},

We received a request to reset the password for your {{ service_name }} account associated with {{ recipient_email }}.

If you made this request, click the link below to set a new password:

{{ link }}

This link will expire in {{ reset_expiry }} minutes.

If you did NOT request a password reset, someone else may be trying to access your account. In that case:

1. Do NOT click the link above
2. Secure your account immediately by enabling two-factor authentication
3. Review your recent login activity

Someone with access to your account could:
- Read your private messages
- Access your stored payment methods
- Make purchases or changes to your account
- Lock you out entirely

If you believe your account has been compromised:

{{ link }}

Stay safe,
{{ service_name }} Security Team

This message was sent to {{ recipient_email }} as a security notification.""",
        urgency_level=5,
        link_text="Reset My Password",
    ),

    # ── 13. Nigerian Prince (Classic) ─────────────────────────
    ScamTemplate(
        name="nigerian_prince",
        category="financial",
        subject_pool=[
            "Strictly Confidential Business Proposal",
            "I Need Your Assistance - {{ amount }}",
            "Confidential: Funds Transfer Assistance Required",
            "Business Proposition of Mutual Benefit",
            "From the Desk of {{ title }} {{ sender_name }}",
        ],
        body="""Dear Friend,

I am {{ title }} {{ sender_name }}, the {{ position }} of {{ region }}, {{ country }}.

I got your contact through a reliable source and I decided to write you for a very confidential business transaction.

During the last regime of my {{ predecessor_relation }}, a huge sum of money amounting to {{ amount }} ({{ amount_words }}) was lodged in a security vault in {{ vault_location }} under my name.

Due to the current political situation in my country, I can not directly claim this fund. I am therefore seeking your assistance to receive this fund into your account for safekeeping.

For your assistance, you will be entitled to {{ your_percentage }}% of the total sum, while {{ my_percentage }}% will be for me and my family, and {{ other_percentage }}% will be set aside for any expenses incurred during the course of this transaction.

All I require from you is:
1. Your willingness to assist
2. A reliable bank account where this money can be transferred
3. Your absolute confidentiality and trust

{{ link }}

Please treat this transaction with the utmost confidentiality for security reasons.

May the blessings of God be upon you and your family.

Yours sincerely,
{{ title }} {{ sender_name }}
{{ position }} of {{ region }}
{{ country }}

CONFIDENTIAL""",
        urgency_level=2,
        link_text="Indicate Your Willingness",
    ),

    # ── 14. Subscription Renewal ──────────────────────────────
    ScamTemplate(
        name="subscription_renewal",
        category="phishing",
        subject_pool=[
            "Your {{ service_name }} Subscription Has Been Renewed",
            "Invoice: {{ amount }} Charged for {{ service_name }}",
            "{{ service_name }} - Auto-Renewal Confirmation",
            "Payment Processed: {{ service_name }} - {{ amount }}",
            "Your {{ service_name }} Plan Has Been Upgraded",
        ],
        body="""Dear {{ recipient_name }},

This email confirms that your {{ service_name }} subscription has been automatically renewed.

Order Details:
    Service:       {{ service_name }} {{ plan_name }}
    Amount:        {{ amount }}
    Payment Method: {{ payment_method }}
    Billing Cycle:  {{ billing_cycle }}
    Next Billing:   {{ next_billing_date }}

If you did not authorize this charge or wish to cancel your subscription, you must act within {{ cancel_window }} hours to receive a full refund.

{{ link }}

After the cancellation window closes, no refunds will be issued for the current billing period.

If you believe this charge was made in error:

{{ link }}

Thank you for being a valued {{ service_name }} customer.

{{ service_name }} Billing Department
{{ support_phone }} | {{ support_email }}

This is an automated billing notification.""",
        urgency_level=4,
        link_text="Manage My Subscription",
    ),

    # ── 15. COVID / Health Emergency ──────────────────────────
    ScamTemplate(
        name="health_alert",
        category="phishing",
        subject_pool=[
            "{{ health_org }}: Important Health Advisory for Your Area",
            "Exposure Notification - {{ condition_name }}",
            "Free {{ treatment_name }} Available - Register Now",
            "Your Health Insurance: {{ benefit_amount }} Benefit Unclaimed",
            "{{ health_org }} Emergency Alert - {{ condition_name }}",
        ],
        body="""Dear {{ recipient_name }},

{{ health_org }} is writing to inform you of an important health advisory affecting residents in your area.

Based on public health records, individuals in {{ affected_region }} may have been exposed to {{ condition_name }}. We are conducting a voluntary screening and assistance program.

Program Details:
    Screening:       Free confidential testing
    Treatment:       {{ treatment_name }} at no cost
    Benefit Amount:  {{ benefit_amount }} for eligible participants
    Enrollment:      Open until {{ enrollment_deadline }}

You may be eligible for:
- Free screening and diagnostic services
- {{ treatment_name }} treatment program
- Financial assistance of {{ benefit_amount }}
- Priority access to {{ priority_access }}

To check your eligibility and enroll:

{{ link }}

Early detection significantly improves outcomes. We strongly encourage all eligible individuals to participate.

{{ health_org }}
{{ org_address }}
Reference: {{ reference_number }}""",
        urgency_level=4,
        link_text="Check My Eligibility",
    ),

    # ── 16. Loan Approval ─────────────────────────────────────
    ScamTemplate(
        name="loan_approval",
        category="financial",
        subject_pool=[
            "Your Loan of {{ loan_amount }} Has Been Pre-Approved",
            "{{ lender_name }}: Congratulations! You're Approved",
            "Get {{ loan_amount }} Deposited by Tomorrow",
            "Loan Approval - {{ interest_rate }}% APR - No Credit Check",
            "{{ lender_name }}: Your Loan Is Ready",
        ],
        body="""Dear {{ recipient_name }},

Great news! Based on a review of your profile, you have been pre-approved for a personal loan of up to {{ loan_amount }}.

Loan Terms:
    Amount:        Up to {{ loan_amount }}
    Interest Rate: {{ interest_rate }}% APR
    Term:          {{ loan_term }} months
    Monthly Payment: Starting at {{ monthly_payment }}
    Credit Check:  Not required for pre-approval

Why choose {{ lender_name }}?
- Funds deposited as soon as {{ funding_speed }}
- No hidden fees or prepayment penalties
- Flexible repayment options
- 100% online process

This pre-approval is valid for {{ approval_validity }} days. After that, your offer may change.

{{ link }}

Don't let this opportunity pass. Thousands of borrowers trust {{ lender_name }} for fast, fair financing.

{{ lender_name }}
{{ lender_address }}
NMLS #{{ nmls_number }}

Terms and conditions apply. This is not a commitment to lend.""",
        urgency_level=3,
        link_text="Accept My Loan Offer",
    ),

    # ── 17. Domain / SEO Scam ─────────────────────────────────
    ScamTemplate(
        name="domain_seo",
        category="business",
        subject_pool=[
            "Someone Is Trying to Register {{ domain_name }}",
            "URGENT: {{ competitor_domain }} Available for Registration",
            "Your Website Is Losing {{ visitor_loss }} Visitors/Month",
            "SEO Report: {{ site_name }} Has {{ issue_count }} Critical Issues",
            "Copyright Infringement Notice - {{ domain_name }}",
        ],
        body="""Dear {{ recipient_name }},

This is a notification regarding the domain name {{ domain_name }}.

We have received a registration request from {{ requester_company }} for the following domain(s) that closely match your brand:

    {{ similar_domain_1 }}
    {{ similar_domain_2 }}

As the owner of {{ domain_name }}, you have priority registration rights before these domains become publicly available.

The applicant has stated their intent to use these domains for {{ stated_purpose }}. If registered by a third party, this could result in:
- Brand confusion among your customers
- Loss of search engine rankings
- Potential trademark disputes

You have {{ priority_window }} hours to exercise your priority registration rights before the application is processed.

{{ link }}

Alternatively, if you have no interest in these domains, you may authorize their release to the applicant.

Domain Registration Services
{{ registry_name }}
{{ registry_address }}

Case Reference: {{ case_number }}""",
        urgency_level=4,
        link_text="Protect My Domain",
    ),
]


def get_template(name: str = None, category: str = None) -> ScamTemplate:
    """Pick a template by name, category, or random."""
    pool = TEMPLATES
    if name:
        matches = [t for t in pool if t.name == name]
        if matches:
            return matches[0]
    if category:
        matches = [t for t in pool if t.category == category]
        if matches:
            return random.choice(matches)
    return random.choice(pool)


def get_all_categories() -> List[str]:
    """Return all unique template categories."""
    return sorted(set(t.category for t in TEMPLATES))


def get_template_names() -> List[str]:
    """Return all template names."""
    return [t.name for t in TEMPLATES]


def template_summary() -> str:
    """Pretty summary of all templates."""
    lines = []
    cats = {}
    for t in TEMPLATES:
        cats.setdefault(t.category, []).append(t)
    for cat, tmpls in cats.items():
        lines.append(f"  {cat.upper()}")
        for t in tmpls:
            lines.append(f"    • {t.name} (urgency: {'🔥' * t.urgency_level})")
    return "\n".join(lines)
