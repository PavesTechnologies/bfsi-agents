"""
Generates two RAG-optimised policy template PDFs:

  1. RBI_Master_Direction_Template.pdf
     - Styled as an actual RBI Master Direction circular
     - Covers every regulatory concern that maps to a decisioning node
     - Example values are labelled [TEMPLATE VALUE] so banks can substitute their own

  2. Bank_Lending_Policy_Template.pdf
     - Styled as an internal bank Credit & Underwriting Policy manual
     - Contains specific thresholds, weights, rates — all marked [TEMPLATE VALUE]
     - Designed so RAG retrieval returns actionable guidance directly into the nodes

Run:  python generate_policy_pdfs.py
"""

import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY      = date.today().strftime("%d %B %Y")
YEAR       = date.today().year

# ── Palette ──────────────────────────────────────────────────────
RBI_DARK   = colors.HexColor("#1A237E")
RBI_MID    = colors.HexColor("#283593")
RBI_LIGHT  = colors.HexColor("#E8EAF6")
RBI_ACCENT = colors.HexColor("#F57F17")
RBI_WARN   = colors.HexColor("#B71C1C")
LIGHT_WARN = colors.HexColor("#FFEBEE")

BP_DARK    = colors.HexColor("#004D40")
BP_MID     = colors.HexColor("#00695C")
BP_LIGHT   = colors.HexColor("#E0F2F1")
BP_ACCENT  = colors.HexColor("#E65100")

GREY_LINE  = colors.HexColor("#BDBDBD")
GREY_TEXT  = colors.HexColor("#212121")
MID_TEXT   = colors.HexColor("#424242")
WHITE      = colors.white


# ── Style builders ────────────────────────────────────────────────
def rbi_styles():
    s = getSampleStyleSheet()
    def add(name, **kw): s.add(ParagraphStyle(name=name, **kw))

    add("RBI_Cover_Title",  fontName="Helvetica-Bold", fontSize=16,
        textColor=WHITE, alignment=TA_CENTER, leading=22, spaceAfter=4)
    add("RBI_Cover_Sub",    fontName="Helvetica",      fontSize=10,
        textColor=RBI_LIGHT, alignment=TA_CENTER, leading=15, spaceAfter=2)
    add("RBI_Cover_Meta",   fontName="Helvetica",      fontSize=8,
        textColor=RBI_LIGHT, alignment=TA_CENTER, spaceAfter=0)
    add("RBI_Chapter",      fontName="Helvetica-Bold", fontSize=12,
        textColor=WHITE, alignment=TA_LEFT, leading=18,
        spaceBefore=4, spaceAfter=4)
    add("RBI_Section",      fontName="Helvetica-Bold", fontSize=10,
        textColor=RBI_DARK, spaceBefore=10, spaceAfter=3)
    add("RBI_Sub",          fontName="Helvetica-Bold", fontSize=9,
        textColor=RBI_MID, spaceBefore=6, spaceAfter=2)
    add("RBI_Body",         fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, alignment=TA_JUSTIFY, leading=14, spaceAfter=5)
    add("RBI_BulletItem",   fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, leftIndent=16, spaceAfter=3, leading=13)
    add("RBI_Directive",    fontName="Helvetica-BoldOblique", fontSize=9,
        textColor=RBI_DARK, alignment=TA_JUSTIFY, leading=14, spaceAfter=4)
    add("RBI_Tpl",          fontName="Helvetica-Bold", fontSize=8,
        textColor=RBI_ACCENT, spaceAfter=2)
    add("RBI_Note",         fontName="Helvetica-Oblique", fontSize=8,
        textColor=RBI_WARN, spaceAfter=3)
    add("RBI_TOC",          fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, leading=14, spaceAfter=1)
    return s


def bp_styles():
    s = getSampleStyleSheet()
    def add(name, **kw): s.add(ParagraphStyle(name=name, **kw))

    add("BP_Cover_Title",   fontName="Helvetica-Bold", fontSize=16,
        textColor=WHITE, alignment=TA_CENTER, leading=22, spaceAfter=4)
    add("BP_Cover_Sub",     fontName="Helvetica",      fontSize=10,
        textColor=BP_LIGHT, alignment=TA_CENTER, leading=15, spaceAfter=2)
    add("BP_Cover_Meta",    fontName="Helvetica",      fontSize=8,
        textColor=BP_LIGHT, alignment=TA_CENTER, spaceAfter=0)
    add("BP_Chapter",       fontName="Helvetica-Bold", fontSize=12,
        textColor=WHITE, alignment=TA_LEFT, leading=18,
        spaceBefore=4, spaceAfter=4)
    add("BP_Section",       fontName="Helvetica-Bold", fontSize=10,
        textColor=BP_DARK, spaceBefore=10, spaceAfter=3)
    add("BP_Sub",           fontName="Helvetica-Bold", fontSize=9,
        textColor=BP_MID, spaceBefore=6, spaceAfter=2)
    add("BP_Body",          fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, alignment=TA_JUSTIFY, leading=14, spaceAfter=5)
    add("BP_BulletItem",    fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, leftIndent=16, spaceAfter=3, leading=13)
    add("BP_Directive",     fontName="Helvetica-BoldOblique", fontSize=9,
        textColor=BP_DARK, alignment=TA_JUSTIFY, leading=14, spaceAfter=4)
    add("BP_Tpl",           fontName="Helvetica-Bold", fontSize=8,
        textColor=BP_ACCENT, spaceAfter=2)
    add("BP_Note",          fontName="Helvetica-Oblique", fontSize=8,
        textColor=RBI_WARN, spaceAfter=3)
    add("BP_TOC",           fontName="Helvetica",      fontSize=9,
        textColor=GREY_TEXT, leading=14, spaceAfter=1)
    return s


# ── Shared flowable helpers ───────────────────────────────────────
def sp(n=1):  return Spacer(1, n * 0.25 * cm)


def chap_hdr(title, style_name, s, bg):
    t = Table([[Paragraph(title, s[style_name])]], colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def cover(title_style, sub_style, meta_style, s, bg,
          title, subtitle, doc_no, version, effective, issuer):
    rows = [
        [Paragraph(title,    s[title_style])],
        [sp()],
        [Paragraph(subtitle, s[sub_style])],
        [Paragraph(f"Document No: {doc_no}   |   Version: {version}   |   Effective Date: {effective}",
                   s[meta_style])],
        [Paragraph(f"Issued by: {issuer}", s[meta_style])],
    ]
    t = Table(rows, colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("LEFTPADDING",   (0, 0), (-1, -1), 24),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 24),
        ("TOPPADDING",    (0, 0), (-1, 0),  28),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 24),
    ]))
    return t


def data_table(rows, widths, hdr_bg, alt=None):
    if alt is None: alt = RBI_LIGHT
    t = Table(rows, colWidths=widths)
    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0),  hdr_bg),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, GREY_LINE),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, alt]),
    ]
    t.setStyle(TableStyle(ts))
    return t


def tpl_box(label, value_text, s, tpl_style, body_style, bg, border):
    rows = [
        [Paragraph(f"[TEMPLATE VALUE]  {label}", s[tpl_style])],
        [Paragraph(value_text, s[body_style])],
    ]
    t = Table(rows, colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.0, border),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ]))
    return t


def warn_box(text, s, note_style):
    rows = [[Paragraph(f"IMPORTANT: {text}", s[note_style])]]
    t = Table(rows, colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_WARN),
        ("BOX",           (0, 0), (-1, -1), 0.8, RBI_WARN),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════════════
#  PDF 1 — RBI Master Direction Template
# ═══════════════════════════════════════════════════════════════════════
def build_rbi(path):
    s   = rbi_styles()
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm,  bottomMargin=2 * cm,
        title="RBI Master Direction – Automated Credit Assessment",
    )
    story = []

    # ─── Cover page ────────────────────────────────────────────
    story += [
        cover(
            "RBI_Cover_Title", "RBI_Cover_Sub", "RBI_Cover_Meta", s, RBI_DARK,
            "RESERVE BANK OF INDIA",
            "Master Direction on Automated Credit Assessment and Risk-Based Lending\n"
            "A Template for Regulated Entities Operating AI-Driven Decisioning Systems",
            "RBI/MD/ACR/TEMPLATE-01", "1.0 (Template)", TODAY,
            "Department of Regulation, Reserve Bank of India"
        ),
        sp(2),
        Table([[Paragraph(
            "This document is a <b>template Master Direction</b>. Regulated Entities (REs) — "
            "Scheduled Commercial Banks, NBFCs, and Housing Finance Companies — must "
            "review every section marked <b>[TEMPLATE VALUE]</b> and replace the example "
            "figures with institution-specific parameters approved by their Credit Risk "
            "Committee and Board. The completed document becomes the authoritative policy "
            "source ingested into the RE's AI decisioning knowledge base (RAG store).",
            s["RBI_Body"]
        )]], colWidths=[17.5 * cm], style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), RBI_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 0.8, RBI_DARK),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
        sp(2),
        PageBreak(),
    ]

    # ─── Table of Contents ──────────────────────────────────────
    story += [chap_hdr("Table of Contents", "RBI_Chapter", s, RBI_DARK), sp()]
    toc = [
        ("1.",  "Definitions and Scope"),
        ("2.",  "Data Privacy and PII Masking Obligations"),
        ("3.",  "Credit Information Bureau Usage and Score Band Classification"),
        ("4.",  "Treatment of Public Records and Bankruptcy Events"),
        ("5.",  "Credit Utilisation Assessment Standards"),
        ("6.",  "Debt Exposure and Leverage Norms"),
        ("7.",  "Credit Inquiry Velocity Governance"),
        ("8.",  "Payment History and NPA Classification"),
        ("9.",  "Income Verification and Debt-to-Income Limits"),
        ("10.", "Risk Aggregation and Composite Scoring"),
        ("11.", "Lending Decision Criteria and Interest Rate Framework"),
        ("12.", "Counter-Offer and Loan Restructuring Requirements"),
        ("13.", "Audit Trail, Explainability and Reporting Obligations"),
    ]
    for num, title in toc:
        story.append(Paragraph(f"<b>{num}</b>  {title}", s["RBI_TOC"]))
    story.append(PageBreak())

    # ─── Section 1: Definitions ─────────────────────────────────
    story += [
        chap_hdr("1.  Definitions and Scope", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("1.1  Purpose", s["RBI_Section"]),
        Paragraph(
            "This Master Direction prescribes the minimum standards that Regulated "
            "Entities (REs) must embed into automated loan origination and credit "
            "decisioning systems. It covers the complete decisioning pipeline: "
            "data ingestion, individual risk signal analysis, risk aggregation, "
            "final lending decision, and adverse action communication.",
            s["RBI_Body"]
        ),
        Paragraph("1.2  Key Terms", s["RBI_Section"]),
    ]
    defn_rows = [
        ["Term", "Definition"],
        ["Regulated Entity (RE)",
         "Any Scheduled Commercial Bank, NBFC, or Housing Finance Company using "
         "an automated AI/ML system for credit decisioning."],
        ["Automated Decisioning System (ADS)",
         "A software pipeline that accepts bureau data and applicant inputs and "
         "produces a loan approval, counter-offer, or decline without mandatory "
         "human review at each step."],
        ["Credit Bureau Payload",
         "The full structured JSON or XML response received from a Credit "
         "Information Company (CIBIL, Experian, Equifax, CRIF) for a specific "
         "applicant."],
        ["Risk Signal",
         "A discrete output produced by one analytical module within the ADS "
         "(e.g., credit score band, utilisation ratio, DTI ratio)."],
        ["RAG Knowledge Base",
         "A vector store containing chunked policy documents. The ADS queries "
         "this store at runtime to retrieve applicable thresholds."],
        ["Hard Decline",
         "An irrevocable rejection triggered by a statutory event (e.g., active "
         "insolvency) that no downstream process may reverse."],
        ["Template Value",
         "A placeholder numerical threshold in this document. REs MUST replace "
         "every [TEMPLATE VALUE] with their own board-approved figures."],
    ]
    story += [
        data_table(defn_rows, [4 * cm, 13.5 * cm], RBI_DARK),
        sp(),
        Paragraph("1.3  Applicability", s["RBI_Section"]),
        Paragraph(
            "These directions apply to all REs that deploy an ADS for retail "
            "or MSME credit products with a per-account exposure exceeding "
            "INR 50,000. REs with aggregate ADS-processed portfolio above "
            "INR 500 crore must obtain annual third-party model audits.",
            s["RBI_Body"]
        ),
        PageBreak(),
    ]

    # ─── Section 2: PII ─────────────────────────────────────────
    story += [
        chap_hdr("2.  Data Privacy and PII Masking Obligations", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph(
            "Reference: RBI Digital Lending Guidelines (Sept 2022), IT Act 2000 S.43A, DPDP Act 2023.",
            s["RBI_Sub"]
        ),
        Paragraph("2.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall ensure that Personally Identifiable Information (PII) is "
            "removed from any bureau payload before that payload is processed by "
            "any machine-learning model, language model, or rule-based scorer. "
            "The sanitisation step must be the first operation in the ADS pipeline. "
            "A boolean flag confirming sanitisation must be set and validated by "
            "every downstream module before consuming bureau data.",
            s["RBI_Directive"]
        ),
        Paragraph("2.2  Fields That Must Be Masked", s["RBI_Section"]),
    ]
    pii_rows = [
        ["Data Category",       "Field Names",                                  "Masking Method"],
        ["Consumer Identity",   "firstName, middleName, surname",               "Remove key entirely"],
        ["Residential Address", "streetPrefix, streetName, streetSuffix,\n"
                                "unitType, unitId, city, state, zipCode",       "Remove key entirely"],
        ["Employment",          "employer name field in tradeline",              "Remove key entirely"],
        ["Account Numbers",     "accountNumber on all tradeline records",        "Remove key entirely"],
        ["Court Records",       "courtName, referenceNumber in public records",  "Remove key entirely"],
    ]
    story += [
        data_table(pii_rows, [3.5 * cm, 8 * cm, 6 * cm], RBI_DARK),
        sp(),
        Paragraph("2.3  Processing Rules", s["RBI_Section"]),
        Paragraph("(a) The original bureau payload must never be mutated in place. "
                  "A deep copy must be created before masking.", s["RBI_BulletItem"]),
        Paragraph("(b) The sanitised payload and the original must be stored in "
                  "logically separate stores with separate access controls.", s["RBI_BulletItem"]),
        Paragraph("(c) Any failure in the PII masking step must halt the pipeline "
                  "and generate an alert; the application must not proceed.", s["RBI_BulletItem"]),
        sp(),
        warn_box(
            "Processing bureau data containing PII through an AI/ML model without prior masking "
            "constitutes a data breach under DPDP Act 2023 and attracts penalties up to INR 250 crore.",
            s, "RBI_Note"
        ),
        PageBreak(),
    ]

    # ─── Section 3: Credit Score ─────────────────────────────────
    story += [
        chap_hdr("3.  Credit Information Bureau Usage and Score Band Classification",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: CIC Regulation Act 2005, RBI CIC Master Direction 2023.", s["RBI_Sub"]),
        Paragraph("3.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall classify every credit applicant into a documented score band "
            "derived from a bureau-sourced credit score. Each score band shall carry "
            "a defined maximum base lending limit, a risk flag (LOW / MODERATE / HIGH), "
            "and a fixed weight in the composite risk score. The ADS must log the "
            "score band assigned, the score used, and the policy source (RAG-retrieved "
            "or hardcoded fallback) for every application.",
            s["RBI_Directive"]
        ),
        Paragraph("3.2  Score Band Thresholds", s["RBI_Section"]),
        Paragraph(
            "REs must define at least four score bands. Replace all [TEMPLATE VALUE] "
            "entries with board-approved figures before ingesting into the RAG store.",
            s["RBI_Body"]
        ),
    ]
    sb_rows = [
        ["Band Name",  "Score Range\n[TEMPLATE VALUE]", "Max Base Limit\n[TEMPLATE VALUE]",
         "Risk Flag",  "Aggregation Weight\n[TEMPLATE VALUE]"],
        ["PRIME",      "750 to 900",  "INR 75,00,000",  "LOW",      "0.25"],
        ["NEAR_PRIME", "700 to 749",  "INR 50,00,000",  "MODERATE", "0.25"],
        ["FAIR",       "650 to 699",  "INR 35,00,000",  "MODERATE", "0.25"],
        ["SUBPRIME",   "Below 650",   "INR 20,00,000",  "HIGH",     "0.25"],
    ]
    story += [
        data_table(sb_rows, [3 * cm, 3.5 * cm, 4 * cm, 2.5 * cm, 4.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Score Band Thresholds",
            "PRIME: score greater than or equal to 750 — base_limit_band = INR 75,00,000 — score_risk_flag = LOW — score_weight = 0.25. "
            "NEAR_PRIME: score 700 to 749 — base_limit_band = INR 50,00,000 — score_risk_flag = MODERATE — score_weight = 0.25. "
            "FAIR: score 650 to 699 — base_limit_band = INR 35,00,000 — score_risk_flag = MODERATE — score_weight = 0.25. "
            "SUBPRIME: score below 650 — base_limit_band = INR 20,00,000 — score_risk_flag = HIGH — score_weight = 0.25.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        sp(),
        Paragraph("3.3  Additional Requirements", s["RBI_Section"]),
        Paragraph("(a) The bureau model used must be disclosed to the applicant on request.", s["RBI_BulletItem"]),
        Paragraph("(b) Score extracted from primary risk model field: riskModel[0].score or equivalent.", s["RBI_BulletItem"]),
        Paragraph("(c) When RAG retrieval returns policy guidance, the ADS must prefer the RAG-sourced "
                  "threshold over hardcoded defaults and set llm_response_type = RAG.", s["RBI_BulletItem"]),
        PageBreak(),
    ]

    # ─── Section 4: Public Records ───────────────────────────────
    story += [
        chap_hdr("4.  Treatment of Public Records and Bankruptcy Events",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: Insolvency and Bankruptcy Code 2016, SARFAESI Act 2002, "
                  "RBI Prudential Framework for Stressed Assets 2019.", s["RBI_Sub"]),
        Paragraph("4.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall analyse all public record events in the bureau payload — "
            "bankruptcies, court judgments, liens, written-off accounts — and classify "
            "them into a severity tier. Each severity tier carries an adjustment factor "
            "that reduces the base lending limit. Severe events must trigger a Hard "
            "Decline that no downstream process may override.",
            s["RBI_Directive"]
        ),
        Paragraph("4.2  Severity Classification and Adjustment Factors", s["RBI_Section"]),
    ]
    pr_rows = [
        ["Severity", "Trigger Conditions\n[TEMPLATE VALUE]",
         "Limit Adjustment\n[TEMPLATE VALUE]", "Hard Decline", "Statutory Basis"],
        ["NONE",
         "No public records on file",
         "1.00 (no reduction)",
         "No",
         "Not applicable"],
        ["LOW",
         "Non-bankruptcy records only: liens, minor court judgments without default finding",
         "0.90",
         "No",
         "RBI FPC 2019"],
        ["MODERATE",
         "Bankruptcy discharged 5 or more years ago; single satisfied judgment",
         "0.75",
         "No",
         "IBC 2016 Sec 178"],
        ["SEVERE",
         "Bankruptcy discharged less than 5 years ago; multiple unsatisfied judgments; "
         "active insolvency proceedings; wilful defaulter listing",
         "0.50",
         "YES",
         "IBC 2016 Sec 14; SARFAESI"],
    ]
    story += [
        data_table(pr_rows, [2 * cm, 5.5 * cm, 3.5 * cm, 2.5 * cm, 4 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Public Record Severity Rules and Adjustment Factors",
            "NONE: no public records — public_record_adjustment_factor = 1.00, hard_decline_flag = False. "
            "LOW: non-bankruptcy adverse records — public_record_adjustment_factor = 0.90, hard_decline_flag = False. "
            "MODERATE: bankruptcy discharged 5 or more years ago — public_record_adjustment_factor = 0.75, hard_decline_flag = False. "
            "SEVERE: bankruptcy within 5 years OR multiple judgments OR active insolvency — "
            "public_record_adjustment_factor = 0.50, hard_decline_flag = True. "
            "Hard decline rules: bankruptcy filed within 24 months triggers hard_decline_flag = True. "
            "Active insolvency proceedings under IBC Section 14 triggers hard_decline_flag = True. "
            "Wilful defaulter classification triggers hard_decline_flag = True.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        sp(),
        Paragraph("4.3  Hard Decline Conditions (Non-Negotiable)", s["RBI_Section"]),
        Paragraph("(a) Bankruptcy filed within the preceding 24 months.", s["RBI_BulletItem"]),
        Paragraph("(b) Active insolvency proceedings in progress under IBC 2016, Section 14.", s["RBI_BulletItem"]),
        Paragraph("(c) Applicant appears on RBI Wilful Defaulter or Fraud list.", s["RBI_BulletItem"]),
        Paragraph("(d) Severity classification = SEVERE as defined in clause 4.2.", s["RBI_BulletItem"]),
        sp(),
        warn_box(
            "Hard Decline flags are statutory obligations. Any system design that allows "
            "a Hard Decline to be overridden by scoring, business rules, or human intervention "
            "contravenes IBC 2016 and RBI norms.",
            s, "RBI_Note"
        ),
        PageBreak(),
    ]

    # ─── Section 5: Utilisation ──────────────────────────────────
    story += [
        chap_hdr("5.  Credit Utilisation Assessment Standards", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Internal Rating-Based (IRB) Guidance, Basel III Capital Framework.", s["RBI_Sub"]),
        Paragraph("5.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall compute the revolving credit utilisation ratio for every applicant "
            "using only revolving credit accounts. Instalment loans must be excluded. "
            "The ratio must be mapped to a risk level and an adjustment factor that reduces "
            "the base lending limit proportionally.",
            s["RBI_Directive"]
        ),
    ]
    ut_rows = [
        ["Ratio Range\n[TEMPLATE VALUE]", "Risk Level",   "Adjustment Factor\n[TEMPLATE VALUE]",
         "Interpretation"],
        ["0% to 30%",  "EXCELLENT", "0.95 to 1.00",  "Low revolving burden; strong cash-flow management"],
        ["31% to 50%", "GOOD",      "0.80 to 0.95",  "Moderate utilisation; acceptable"],
        ["51% to 75%", "MODERATE",  "0.65 to 0.80",  "Elevated; approaching stress territory"],
        ["Above 75%",  "CRITICAL",  "0.50 to 0.65",  "Near-maxed revolving lines; high financial stress signal"],
    ]
    story += [
        data_table(ut_rows, [3.5 * cm, 2.5 * cm, 4 * cm, 7.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Revolving Utilisation Thresholds and Adjustment Factors",
            "EXCELLENT: utilisation_ratio 0.00 to 0.30 — utilisation_adjustment_factor = 0.975. "
            "GOOD: utilisation_ratio 0.31 to 0.50 — utilisation_adjustment_factor = 0.875. "
            "MODERATE: utilisation_ratio 0.51 to 0.75 — utilisation_adjustment_factor = 0.725. "
            "CRITICAL: utilisation_ratio above 0.75 — utilisation_adjustment_factor = 0.575. "
            "Formula: utilisation_ratio = total_revolving_balance divided by total_revolving_credit_limit. "
            "Only accounts with revolvingOrInstallment = R are included.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        sp(),
        Paragraph("(a) Include only revolving accounts (revolvingOrInstallment = R).", s["RBI_BulletItem"]),
        Paragraph("(b) The adjustment factor multiplies the credit-score-derived base lending limit.", s["RBI_BulletItem"]),
        PageBreak(),
    ]

    # ─── Section 6: Debt Exposure ────────────────────────────────
    story += [
        chap_hdr("6.  Debt Exposure and Leverage Norms", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Financial Stability Report, Household Debt Guidelines.", s["RBI_Sub"]),
        Paragraph("6.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall assess total outstanding indebtedness across all open tradelines "
            "before extending additional credit. Only open accounts (openOrClosed = O) "
            "shall be included. Monthly obligations from this node feed the income "
            "analysis node's DTI calculation.",
            s["RBI_Directive"]
        ),
    ]
    ex_rows = [
        ["Exposure Risk",  "Debt Multiple\n[TEMPLATE VALUE]",
         "Monthly Obligation\n[TEMPLATE VALUE]",  "Lending Impact"],
        ["LOW",     "Below 2 times gross annual income",   "Below 15% of gross monthly income",  "Full lending capacity available"],
        ["MODERATE","2 to 4 times gross annual income",    "15% to 30% of gross monthly income", "Moderate capacity reduction"],
        ["HIGH",    "4 to 6 times gross annual income",    "30% to 45% of gross monthly income", "Significant capacity reduction"],
        ["EXTREME", "Above 6 times gross annual income",   "Above 45% of gross monthly income",  "Counter-offer with reduced principal required"],
    ]
    story += [
        data_table(ex_rows, [2.5 * cm, 4 * cm, 4.5 * cm, 6.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Debt Exposure Risk Bands",
            "LOW: total_existing_debt below 2 times gross annual income — exposure_risk = LOW. "
            "MODERATE: total debt 2 to 4 times annual income — exposure_risk = MODERATE. "
            "HIGH: total debt 4 to 6 times annual income — exposure_risk = HIGH. "
            "EXTREME: total debt above 6 times annual income — exposure_risk = EXTREME. "
            "total_existing_debt = sum of outstanding balances on all open tradelines (openOrClosed = O). "
            "monthly_obligation_estimate = sum of monthlyPaymentAmount across open accounts.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 7: Inquiry ──────────────────────────────────────
    story += [
        chap_hdr("7.  Credit Inquiry Velocity Governance", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI CIC Regulations 2006, KYC/AML Master Direction 2016.", s["RBI_Sub"]),
        Paragraph("7.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall monitor the number of hard credit inquiries made against an applicant "
            "over a rolling 12-month window. High inquiry velocity is a recognised indicator "
            "of financial distress and potential fraud. A penalty factor derived from "
            "inquiry velocity must be applied multiplicatively to the approved lending limit.",
            s["RBI_Directive"]
        ),
    ]
    inq_rows = [
        ["Inquiry Count\n(12 months)\n[TEMPLATE VALUE]", "Velocity Risk", "Penalty Factor\n[TEMPLATE VALUE]",
         "Required Action"],
        ["0 or 1",    "LOW",      "1.00 (no penalty)", "Normal processing"],
        ["2 to 3",    "MODERATE", "0.90",               "Document inquiry sources; note in file"],
        ["4 to 6",    "HIGH",     "0.70",               "Enhanced due diligence; flag for senior review"],
        ["7 or more", "CRITICAL", "0.50",                "Fraud screening mandatory; referral to Risk team"],
    ]
    story += [
        data_table(inq_rows, [3.5 * cm, 2.5 * cm, 3.5 * cm, 8 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Inquiry Velocity Thresholds and Penalty Factors",
            "LOW: 0 to 1 hard inquiries in last 12 months — inquiry_penalty_factor = 1.00. "
            "MODERATE: 2 to 3 inquiries — inquiry_penalty_factor = 0.90. "
            "HIGH: 4 to 6 inquiries — inquiry_penalty_factor = 0.70. "
            "CRITICAL: 7 or more inquiries — inquiry_penalty_factor = 0.50. "
            "Only hard inquiries (credit-seeking applications) count; soft inquiries are excluded. "
            "Penalty factor applied multiplicatively to lending capacity after other adjustment factors.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 8: Payment Behaviour ───────────────────────────
    story += [
        chap_hdr("8.  Payment History and NPA Classification", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI IRACP Master Circular DBR.BP.BC.No.1/21.04.048.", s["RBI_Sub"]),
        Paragraph("8.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall evaluate the full payment history across all tradelines. "
            "The evaluation must count delinquency events (30 or more Days Past Due), "
            "identify chargeoff history, and produce a behaviour score on a 0 to 100 scale. "
            "The behaviour score feeds directly into the composite risk aggregation.",
            s["RBI_Directive"]
        ),
    ]
    beh_rows = [
        ["Behaviour Band", "30+ DPD Count\n[TEMPLATE VALUE]", "Chargeoff History\n[TEMPLATE VALUE]",
         "Behaviour Score\n[TEMPLATE VALUE]", "IRACP Asset Class"],
        ["EXCELLENT",    "0",              "None",                  "90 to 100",  "Standard"],
        ["GOOD",         "1 to 2",         "None",                  "75 to 89",   "Standard / Special Mention"],
        ["FAIR",         "3 to 5",         "Older than 2 years",    "50 to 74",   "Sub-Standard"],
        ["POOR",         "6 or more",      "Within past 2 years",   "25 to 49",   "Doubtful"],
        ["UNACCEPTABLE", "Multiple events","Active collections",     "5 to 24",    "Loss"],
    ]
    story += [
        data_table(beh_rows, [2.8 * cm, 3.2 * cm, 4 * cm, 3.5 * cm, 4 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Payment Behaviour Scoring Bands",
            "EXCELLENT: 0 delinquencies, no chargeoffs — behaviour_score range 90 to 100 — aggregation sub-score = 90. "
            "GOOD: 1 to 2 delinquencies, no chargeoffs — behaviour_score range 75 to 89 — aggregation sub-score = 80. "
            "FAIR: 3 to 5 delinquencies OR chargeoff older than 2 years — behaviour_score range 50 to 74 — aggregation sub-score = 65. "
            "POOR: 6 or more delinquencies OR chargeoff within past 2 years — behaviour_score range 25 to 49 — aggregation sub-score = 30. "
            "UNACCEPTABLE: multiple chargeoffs or active collections — behaviour_score range 5 to 24 — aggregation sub-score = 5. "
            "Delinquency = account 30 or more days past due. "
            "chargeoff_history = True if any tradeline has been written off.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 9: Income / DTI ─────────────────────────────────
    story += [
        chap_hdr("9.  Income Verification and Debt-to-Income Limits",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Digital Lending Guidelines Sept 2022, Fair Practices Code 2016.", s["RBI_Sub"]),
        Paragraph("9.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs must assess every applicant's repayment capacity through verifiable "
            "income evidence before disbursement. The Debt-to-Income (DTI) ratio is "
            "the primary affordability metric. Applications where DTI exceeds the "
            "maximum permissible limit must be declined or restructured.",
            s["RBI_Directive"]
        ),
        Paragraph("9.2  DTI Calculation", s["RBI_Section"]),
        Paragraph(
            "DTI = (sum of all monthly obligations on open accounts plus proposed new EMI) "
            "divided by verified gross monthly income. Income must be sourced from bank "
            "statements, ITR, or authenticated salary slips. If income cannot be verified, "
            "DTI must be treated as UNACCEPTABLE.",
            s["RBI_Body"]
        ),
    ]
    dti_rows = [
        ["DTI Range\n[TEMPLATE VALUE]", "Income Risk",   "Affordability Flag",
         "Required Policy Action"],
        ["0% to 30%",   "LOW",           "True",   "Approve at full requested amount if capacity permits"],
        ["31% to 40%",  "MODERATE",      "True",   "Approve with income documentation on file"],
        ["41% to 50%",  "HIGH",          "True",   "Approve with enhanced post-disbursement monitoring"],
        ["Above 50%",   "UNACCEPTABLE",  "False",  "Immediate decline or counter-offer with reduced principal"],
    ]
    story += [
        data_table(dti_rows, [3 * cm, 2.5 * cm, 3.5 * cm, 8.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "DTI Thresholds and Affordability Rules",
            "DTI formula: (total_monthly_obligations + proposed_new_EMI) / verified_gross_monthly_income. "
            "LOW: DTI 0 to 0.30 — income_risk = LOW, affordability_flag = True. "
            "MODERATE: DTI 0.31 to 0.40 — income_risk = MODERATE, affordability_flag = True. "
            "HIGH: DTI 0.41 to 0.50 — income_risk = HIGH, affordability_flag = True. "
            "UNACCEPTABLE: DTI above 0.50 — income_risk = UNACCEPTABLE, affordability_flag = False, triggers DECLINE. "
            "Missing income rule: if monthly_income is None or zero then income_missing_flag = True "
            "and DTI is classified as UNACCEPTABLE. "
            "Maximum DTI for any counter-offer option = 0.40.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 10: Aggregation ─────────────────────────────────
    story += [
        chap_hdr("10.  Risk Aggregation and Composite Scoring", "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Model Risk Management Guidelines 2024 (draft), Basel III IRB Approach.", s["RBI_Sub"]),
        Paragraph("10.1  Directive", s["RBI_Section"]),
        Paragraph(
            "REs shall aggregate individual risk signals into a composite score on a "
            "scale of 0 to 100 using a documented, board-approved weighting scheme. "
            "The composite score determines the risk tier and, together with the Hard "
            "Decline flag, drives the final lending decision.",
            s["RBI_Directive"]
        ),
    ]
    wt_rows = [
        ["Risk Factor",        "Weight\n[TEMPLATE VALUE]",
         "Source Signal",      "Normalisation Rule"],
        ["Credit Score",        "0.25",  "bureau riskModel score",
         "(score minus 300) divided by 5.5, clamped 0 to 100"],
        ["Payment Behaviour",   "0.15",  "behaviour_score (0 to 100)",
         "Use raw value directly; no normalisation needed"],
        ["Public Records",      "0.15",  "public_record_severity",
         "NONE = 100, LOW = 90, MODERATE = 60, SEVERE = 30"],
        ["Credit Utilisation",  "0.15",  "utilisation_risk",
         "EXCELLENT = 90, GOOD = 60, MODERATE = 65, CRITICAL = 10"],
        ["Income and DTI",      "0.15",  "income_risk",
         "LOW = 90, MODERATE = 60, HIGH = 65, UNACCEPTABLE = 5"],
        ["Debt Exposure",       "0.10",  "exposure_risk",
         "LOW = 90, MODERATE = 60, HIGH = 65, EXTREME = 5"],
        ["Inquiry Velocity",    "0.05",  "velocity_risk",
         "LOW = 90, MODERATE = 60, HIGH = 65, CRITICAL = 10"],
    ]
    story += [
        data_table(wt_rows, [3.5 * cm, 2 * cm, 4 * cm, 8 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Aggregation Formula and Risk Tier Bands",
            "Composite formula: aggregated_risk_score = sum of (normalised_sub_score multiplied by weight) for all 7 factors. "
            "All weights must sum to 1.00. "
            "Hard-decline override: if hard_decline_flag is True then set aggregated_risk_score = 0.0. "
            "Risk tier A: aggregated_risk_score >= 80 — disposition APPROVE. "
            "Risk tier B: aggregated_risk_score 65 to 79 — disposition APPROVE with conditions. "
            "Risk tier C: aggregated_risk_score 50 to 64 — disposition COUNTER_OFFER likely. "
            "Risk tier D: aggregated_risk_score 35 to 49 — disposition COUNTER_OFFER or DECLINE. "
            "Risk tier F: aggregated_risk_score below 35 — disposition DECLINE.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 11: Decision ────────────────────────────────────
    story += [
        chap_hdr("11.  Lending Decision Criteria and Interest Rate Framework",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Master Direction on Interest Rate on Advances 2016 (updated 2023), "
                  "Fair Practices Code.", s["RBI_Sub"]),
        Paragraph("11.1  Decision Protocol", s["RBI_Section"]),
        Paragraph(
            "The ADS must follow a deterministic decision protocol in the sequence below. "
            "No step may be skipped. Each step and its outcome must be logged in reasoning_steps.",
            s["RBI_Body"]
        ),
    ]
    dec_rows = [
        ["Step", "Condition Evaluated",                            "Outcome if Condition Met"],
        ["1", "Risk Tier = F  OR  hard_decline_flag = True",       "Output DECLINE immediately. Log reason."],
        ["2", "Assign interest rate per tier (see 11.2)",          "Set interest_rate for application."],
        ["3", "Calculate maximum lending capacity",
         "max_approved = base_limit_band x public_record_adjustment_factor "
         "x utilisation_adjustment_factor x inquiry_penalty_factor"],
        ["4", "affordability_flag = False",                        "Output DECLINE. Log income constraint."],
        ["5", "Requested amount <= max_approved",                  "Output APPROVE at requested amount and tenure."],
        ["6", "Requested > max_approved AND max_approved > 0",     "Output COUNTER_OFFER."],
        ["7", "max_approved = 0",                                  "Output DECLINE."],
        ["8", "APPROVE path only: calculate disbursement",
         "disbursement_amount = approved_amount multiplied by (1 minus origination_fee_rate)"],
    ]
    story += [
        data_table(dec_rows, [1 * cm, 6 * cm, 10.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Interest Rate Schedule and Origination Fee",
            "Tier A (PRIME) interest rate = 7.5% per annum. "
            "Tier B (NEAR_PRIME) interest rate = 10.0% per annum. "
            "Tier C (FAIR) interest rate = 13.5% per annum. "
            "Tier D (SUBPRIME) interest rate = 18.0% per annum. "
            "Tier F (DECLINE): no rate applicable. "
            "Origination fee rate = 0.02 (2%). "
            "disbursement_amount = approved_amount multiplied by 0.98.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 12: Counter-Offer ───────────────────────────────
    story += [
        chap_hdr("12.  Counter-Offer and Loan Restructuring Requirements",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Guidelines on Restructuring of Advances 2021, Fair Practices Code.", s["RBI_Sub"]),
        Paragraph("12.1  Directive", s["RBI_Section"]),
        Paragraph(
            "When an applicant's requested loan amount exceeds assessed lending capacity, "
            "the ADS must not issue an outright decline. It must generate a minimum of "
            "two restructured loan options that bring DTI within acceptable bounds. "
            "All options must be communicated to the applicant in writing.",
            s["RBI_Directive"]
        ),
    ]
    co_rows = [
        ["Option ID",          "Description",                               "Principal Reduction\n[TEMPLATE VALUE]",
         "Tenure Change\n[TEMPLATE VALUE]", "Min Tenure"],
        ["OPT_REDUCED_AMOUNT", "Reduce principal; keep original tenure",    "15% reduction (multiply by 0.85)",
         "No change",                       "12 months"],
        ["OPT_EXTENDED_TERM",  "Reduce principal; extend repayment tenure", "30% reduction (multiply by 0.70)",
         "Add 12 months to original tenure","36 months"],
    ]
    story += [
        data_table(co_rows, [4 * cm, 4 * cm, 4 * cm, 3 * cm, 2.5 * cm], RBI_DARK),
        sp(),
        tpl_box(
            "Counter-Offer Generation Rules",
            "max_affordable_emi = verified_monthly_income multiplied by 0.35. "
            "OPT_REDUCED_AMOUNT: proposed_amount = requested_amount multiplied by 0.85, proposed_tenure = requested_tenure. "
            "OPT_EXTENDED_TERM: proposed_amount = requested_amount multiplied by 0.70, "
            "proposed_tenure = requested_tenure plus 12 months. "
            "Origination fee of 2% applies to disbursement on all counter-offer options. "
            "counter_offer_logic must explain why original amount was not sanctioned. "
            "original_request_dti must be logged. "
            "If no viable option can be structured (max_approved = 0), issue DECLINE instead.",
            s, "RBI_Tpl", "RBI_Body",
            colors.HexColor("#FFFDE7"), RBI_ACCENT
        ),
        PageBreak(),
    ]

    # ─── Section 13: Audit ───────────────────────────────────────
    story += [
        chap_hdr("13.  Audit Trail, Explainability and Reporting Obligations",
                 "RBI_Chapter", s, RBI_DARK), sp(),
        Paragraph("Reference: RBI Responsible AI Guidelines 2024 (draft), IT Framework for Banks.", s["RBI_Sub"]),
        Paragraph("13.1  Mandatory Audit Fields", s["RBI_Section"]),
    ]
    aud_rows = [
        ["Field",                  "Description",                                        "Retention"],
        ["application_id",         "Unique identifier for the loan application",          "Permanent"],
        ["correlation_id",         "Request traceability identifier",                     "Permanent"],
        ["node_execution_times",   "Duration of each pipeline node in milliseconds",      "90 days"],
        ["model_reasoning",        "Natural-language explanation of each classification", "7 years"],
        ["llm_response_type",      "RAG (policy-retrieved) or FALLBACK (hardcoded)",      "7 years"],
        ["confidence_score",       "Model confidence 0 to 1 per node output",            "7 years"],
        ["reasoning_trace",        "Aggregator sub-scores, weights, hard-decline flag",   "7 years"],
        ["reasoning_steps",        "Step-by-step decision node logic",                   "7 years"],
        ["rag_pool",               "Source documents and chunk IDs used in decision",    "7 years"],
        ["decision",               "APPROVE, COUNTER_OFFER, or DECLINE",                 "7 years"],
        ["decline_reason",         "Written explanation for any adverse decision",        "7 years"],
    ]
    story += [
        data_table(aud_rows, [4 * cm, 9 * cm, 4.5 * cm], RBI_DARK),
        sp(),
        Paragraph("13.2  Adverse Action Notice", s["RBI_Section"]),
        Paragraph(
            "REs must communicate the reason for every DECLINE or COUNTER_OFFER to "
            "the applicant in writing within 7 working days. The explanation and "
            "decline_reason fields in the ADS output fulfil this requirement when "
            "transmitted to the applicant-facing communication layer.",
            s["RBI_Body"]
        ),
        Paragraph("13.3  FALLBACK Path Monitoring", s["RBI_Section"]),
        Paragraph(
            "When any node activates the FALLBACK path (hardcoded defaults used instead "
            "of RAG-retrieved policy), the event must be logged. If FALLBACK decisions "
            "exceed 5% of daily application volume, Technology Risk must be escalated.",
            s["RBI_Body"]
        ),
        sp(),
        warn_box(
            "Audit records must be stored in an immutable, tamper-proof system. "
            "RBI may request access to audit logs with 48 hours notice. "
            "Non-compliance attracts penalties under IT Act 2000 and RBI enforcement powers.",
            s, "RBI_Note"
        ),
    ]

    doc.build(story)
    print(f"  Generated: {path}")


# ═══════════════════════════════════════════════════════════════════════
#  PDF 2 — Internal Bank Lending Policy Template
# ═══════════════════════════════════════════════════════════════════════
def build_bank(path):
    s   = bp_styles()
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm,  bottomMargin=2 * cm,
        title="Internal Bank Lending Policy – AI Decisioning",
    )
    story = []

    # ─── Cover ──────────────────────────────────────────────────
    story += [
        cover(
            "BP_Cover_Title", "BP_Cover_Sub", "BP_Cover_Meta", s, BP_DARK,
            "[BANK NAME]\nCredit and Underwriting Policy Manual",
            "Section 7: Automated Lending Decisioning Standards\n"
            "A Customisable Template for AI-Driven Loan Origination Systems",
            "BP-ADS-TEMPLATE-01", "1.0 (Template)", TODAY,
            "Credit Risk Division | Approved by: Chief Credit Officer [SIGNATURE REQUIRED]"
        ),
        sp(2),
        Table([[Paragraph(
            "This is a <b>policy template</b>. Every field marked <b>[TEMPLATE VALUE]</b> "
            "must be replaced with this institution's board-approved figures before this "
            "document is published internally or ingested into the AI decisioning RAG "
            "knowledge base. Changes to any threshold require sign-off from the Chief "
            "Credit Officer and notification to the Board Risk Committee.",
            s["BP_Body"]
        )]], colWidths=[17.5 * cm], style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BP_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 0.8, BP_DARK),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
        sp(2),
        PageBreak(),
    ]

    # ─── TOC ────────────────────────────────────────────────────
    story += [chap_hdr("Contents", "BP_Chapter", s, BP_DARK), sp()]
    toc = [
        ("7.1",  "Policy Scope and Governance"),
        ("7.2",  "Data Handling and PII Masking Policy"),
        ("7.3",  "Credit Score Band and Base Limit Policy"),
        ("7.4",  "Public Record Severity and Hard-Decline Policy"),
        ("7.5",  "Credit Utilisation Adjustment Policy"),
        ("7.6",  "Debt Exposure and Leverage Policy"),
        ("7.7",  "Inquiry Velocity and Fraud Control Policy"),
        ("7.8",  "Payment Behaviour Scoring Policy"),
        ("7.9",  "Income Verification and DTI Policy"),
        ("7.10", "RAG Knowledge Base Maintenance Policy"),
        ("7.11", "Risk Aggregation Weights and Tier Policy"),
        ("7.12", "Lending Decision and Pricing Policy"),
        ("7.13", "Counter-Offer Generation Policy"),
        ("7.14", "Model Fallback and Human Override Policy"),
        ("7.15", "Audit, Reporting and Compliance"),
    ]
    for num, title in toc:
        story.append(Paragraph(f"<b>{num}</b>   {title}", s["BP_TOC"]))
    story.append(PageBreak())

    # ─── 7.1 Governance ─────────────────────────────────────────
    story += [
        chap_hdr("7.1  Policy Scope and Governance", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph(
            "This section governs the operation of the bank's Automated Decisioning "
            "System (ADS). The ADS processes retail and MSME credit applications using "
            "a multi-node AI pipeline that analyses bureau data, income information, and "
            "behavioural signals to produce an APPROVE, COUNTER_OFFER, or DECLINE output.",
            s["BP_Body"]
        ),
        Paragraph("7.1.1  Governance Structure", s["BP_Section"]),
    ]
    gov_rows = [
        ["Role",                    "Responsibility"],
        ["Chief Credit Officer",    "Owns this policy; approves all threshold changes; signs model governance reviews"],
        ["Board Risk Committee",    "Receives quarterly model performance reports; approves major policy revisions"],
        ["Technology Risk Team",    "Monitors FALLBACK rate, model drift, and RAG retrieval quality"],
        ["Compliance Officer",      "Ensures RBI obligations are met; manages audit log access"],
        ["Credit Operations Team",  "Reviews FALLBACK-path decisions within 24 hours; processes human overrides"],
    ]
    story += [
        data_table(gov_rows, [4.5 * cm, 13 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph(
            "Policy Version: [TEMPLATE VALUE]  |  Effective Date: [TEMPLATE VALUE]  |  "
            "Next Review Date: [TEMPLATE VALUE — recommend annual]",
            s["BP_Sub"]
        ),
        PageBreak(),
    ]

    # ─── 7.2 PII ────────────────────────────────────────────────
    story += [
        chap_hdr("7.2  Data Handling and PII Masking Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: pi_deletion_node (mandatory pipeline entry point).", s["BP_Sub"]),
        Paragraph("7.2.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "All credit bureau payloads must be sanitised of Personally Identifiable "
            "Information before entering any AI or ML processing step. The pi_deletion_node "
            "is the mandatory first step. No downstream node may access the raw bureau payload. "
            "A deep copy must be created before masking — in-place mutation is prohibited.",
            s["BP_Directive"]
        ),
    ]
    pii_rows = [
        ["Data Category",    "Fields to Remove",                                       "Method"],
        ["Consumer Names",   "firstName, middleName, surname",                         "Delete key from payload"],
        ["Address",          "streetPrefix, streetName, streetSuffix, unitType, "
                             "unitId, city, state, zipCode",                           "Delete key from payload"],
        ["Employment",       "Employer name in tradeline",                              "Delete key from payload"],
        ["Account Numbers",  "accountNumber on all tradelines",                         "Delete key from payload"],
        ["Court Records",    "courtName, referenceNumber in public records",            "Delete key from payload"],
    ]
    story += [
        data_table(pii_rows, [3.5 * cm, 9 * cm, 5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "PII Masking Confirmation",
            "State variable name that confirms masking is complete. "
            "Example: is_pii_masked = True must be set in pipeline state before any downstream node reads bureau data.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.3 Credit Score ───────────────────────────────────────
    story += [
        chap_hdr("7.3  Credit Score Band and Base Limit Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: credit_score_node.", s["BP_Sub"]),
        Paragraph("7.3.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Every applicant must be classified into a credit score band. The band "
            "determines the maximum base lending limit before any adjustment factors "
            "are applied. All thresholds below are template values and must be replaced "
            "with board-approved figures before ingesting into the RAG store.",
            s["BP_Directive"]
        ),
    ]
    sb_rows = [
        ["Band",       "Score Range\n[TEMPLATE VALUE]", "Max Base Limit\n[TEMPLATE VALUE]",
         "Risk Flag",  "Aggregation Weight\n[TEMPLATE VALUE]"],
        ["PRIME",      "750 or above",  "INR 75,00,000",   "LOW",      "0.25"],
        ["NEAR_PRIME", "700 to 749",    "INR 50,00,000",   "MODERATE", "0.25"],
        ["FAIR",       "650 to 699",    "INR 35,00,000",   "MODERATE", "0.25"],
        ["SUBPRIME",   "Below 650",     "INR 20,00,000",   "HIGH",     "0.25"],
    ]
    story += [
        data_table(sb_rows, [3 * cm, 3.5 * cm, 4 * cm, 2.5 * cm, 4.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Score Band Thresholds and Base Limits",
            "PRIME: score_band = PRIME when score >= 750 — base_limit_band = INR 75,00,000 — score_risk_flag = LOW — score_weight = 0.25. "
            "NEAR_PRIME: score_band = NEAR_PRIME when score 700 to 749 — base_limit_band = INR 50,00,000 — score_risk_flag = MODERATE — score_weight = 0.25. "
            "FAIR: score_band = FAIR when score 650 to 699 — base_limit_band = INR 35,00,000 — score_risk_flag = MODERATE — score_weight = 0.25. "
            "SUBPRIME: score_band = SUBPRIME when score below 650 — base_limit_band = INR 20,00,000 — score_risk_flag = HIGH — score_weight = 0.25. "
            "Score source: riskModel[0].score from pi_masked_experian_data. "
            "When llm_response_type = RAG, thresholds retrieved from knowledge base take precedence over these defaults.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.4 Public Records ─────────────────────────────────────
    story += [
        chap_hdr("7.4  Public Record Severity and Hard-Decline Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: public_record_node.", s["BP_Sub"]),
        Paragraph("7.4.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Public record events are evaluated for severity. Each severity level "
            "carries an adjustment factor that reduces the base lending limit. SEVERE "
            "events trigger a Hard Decline flag that supersedes all other signals.",
            s["BP_Directive"]
        ),
    ]
    pr_rows = [
        ["Severity",  "Trigger Conditions\n[TEMPLATE VALUE]",
         "Adj Factor\n[TEMPLATE VALUE]", "hard_decline_flag"],
        ["NONE",     "No public records on file",                               "1.00", "False"],
        ["LOW",      "Non-bankruptcy adverse records (liens, minor judgments)", "0.90", "False"],
        ["MODERATE", "Bankruptcy discharged 5 or more years ago",               "0.75", "False"],
        ["SEVERE",   "Bankruptcy under 5 years; multiple judgments; active proceedings","0.50","True"],
    ]
    story += [
        data_table(pr_rows, [2.5 * cm, 7 * cm, 3.5 * cm, 4.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Public Record Adjustment Factors and Hard-Decline Triggers",
            "NONE: no records — public_record_adjustment_factor = 1.00, hard_decline_flag = False. "
            "LOW: non-bankruptcy adverse records — public_record_adjustment_factor = 0.90, hard_decline_flag = False. "
            "MODERATE: bankruptcy discharged >= 5 years — public_record_adjustment_factor = 0.75, hard_decline_flag = False. "
            "SEVERE: bankruptcy within 5 years OR multiple judgments OR active insolvency — "
            "public_record_adjustment_factor = 0.50, hard_decline_flag = True. "
            "Additional hard-decline triggers: bankruptcy within 24 months sets hard_decline_flag = True. "
            "Wilful defaulter listing sets hard_decline_flag = True. "
            "Active IBC Section 14 moratorium sets hard_decline_flag = True.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        sp(),
        warn_box(
            "hard_decline_flag = True forces aggregated_risk_score to 0.0. "
            "This cannot be overridden by the decision node, counter-offer node, or any operator.",
            s, "BP_Note"
        ),
        PageBreak(),
    ]

    # ─── 7.5 Utilisation ────────────────────────────────────────
    story += [
        chap_hdr("7.5  Credit Utilisation Adjustment Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: utilization_node.", s["BP_Sub"]),
        Paragraph("7.5.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Revolving credit utilisation is computed using only revolving accounts "
            "(revolvingOrInstallment = R). The ratio determines a utilisation_adjustment_factor "
            "applied multiplicatively to the base lending limit.",
            s["BP_Directive"]
        ),
    ]
    ut_rows = [
        ["Utilisation Range\n[TEMPLATE VALUE]", "Risk Level",  "Adj Factor\n[TEMPLATE VALUE]",
         "Interpretation"],
        ["0% to 30%",  "EXCELLENT", "0.975", "Low revolving burden"],
        ["31% to 50%", "GOOD",      "0.875", "Moderate; manageable"],
        ["51% to 75%", "MODERATE",  "0.725", "Elevated; nearing stress"],
        ["Above 75%",  "CRITICAL",  "0.575", "Near-maxed; strong stress indicator"],
    ]
    story += [
        data_table(ut_rows, [3.5 * cm, 2.5 * cm, 3 * cm, 8.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Utilisation Thresholds and Adjustment Factors",
            "EXCELLENT: utilisation_ratio 0.00 to 0.30 — utilisation_adjustment_factor = 0.975. "
            "GOOD: utilisation_ratio 0.31 to 0.50 — utilisation_adjustment_factor = 0.875. "
            "MODERATE: utilisation_ratio 0.51 to 0.75 — utilisation_adjustment_factor = 0.725. "
            "CRITICAL: utilisation_ratio above 0.75 — utilisation_adjustment_factor = 0.575. "
            "Formula: utilisation_ratio = total_revolving_balance divided by total_revolving_credit_limit. "
            "Only accounts with revolvingOrInstallment = R are included in the calculation.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.6 Debt Exposure ──────────────────────────────────────
    story += [
        chap_hdr("7.6  Debt Exposure and Leverage Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: debt_exposure_node.", s["BP_Sub"]),
        Paragraph("7.6.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Total outstanding debt across all open tradelines (openOrClosed = O) is "
            "assessed to ensure the applicant's leverage does not exceed the bank's "
            "risk appetite. Monthly obligations from this node feed the DTI calculation.",
            s["BP_Directive"]
        ),
    ]
    ex_rows = [
        ["Exposure Risk", "Total Debt Multiple\n[TEMPLATE VALUE]",
         "Monthly Obligation Ceiling\n[TEMPLATE VALUE]", "Lending Impact"],
        ["LOW",     "Below 2 times annual income",   "Below 15% of monthly income",  "Full capacity available"],
        ["MODERATE","2 to 4 times annual income",    "15% to 30% of monthly income", "Moderate capacity reduction"],
        ["HIGH",    "4 to 6 times annual income",    "30% to 45% of monthly income", "Significant reduction; monitoring"],
        ["EXTREME", "Above 6 times annual income",   "Above 45% of monthly income",  "Counter-offer required"],
    ]
    story += [
        data_table(ex_rows, [2.5 * cm, 4 * cm, 4.5 * cm, 6.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Debt Exposure Risk Thresholds",
            "LOW: total_existing_debt below 2 times gross annual income — exposure_risk = LOW. "
            "MODERATE: total debt 2 to 4 times annual income — exposure_risk = MODERATE. "
            "HIGH: total debt 4 to 6 times annual income — exposure_risk = HIGH. "
            "EXTREME: total debt above 6 times annual income — exposure_risk = EXTREME. "
            "monthly_obligation_estimate = sum of monthlyPaymentAmount from all open tradelines.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.7 Inquiry ────────────────────────────────────────────
    story += [
        chap_hdr("7.7  Inquiry Velocity and Fraud Control Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: inquiry_node.", s["BP_Sub"]),
        Paragraph("7.7.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Hard credit inquiry count over a 12-month rolling window is monitored. "
            "High velocity signals distress or fraud. An inquiry_penalty_factor is "
            "applied multiplicatively to the lending limit.",
            s["BP_Directive"]
        ),
    ]
    inq_rows = [
        ["Inquiry Count\n(12 months)\n[TEMPLATE VALUE]", "Velocity Risk",
         "Penalty Factor\n[TEMPLATE VALUE]", "Required Action"],
        ["0 to 1",  "LOW",      "1.00",  "Normal processing"],
        ["2 to 3",  "MODERATE", "0.90",  "Note sources in credit file"],
        ["4 to 6",  "HIGH",     "0.70",  "Enhanced due diligence; senior review"],
        ["7+",      "CRITICAL", "0.50",  "Fraud screening mandatory"],
    ]
    story += [
        data_table(inq_rows, [3.5 * cm, 2.5 * cm, 3.5 * cm, 8 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Inquiry Velocity Thresholds",
            "LOW: 0 to 1 hard inquiries in 12 months — inquiry_penalty_factor = 1.00. "
            "MODERATE: 2 to 3 inquiries — inquiry_penalty_factor = 0.90. "
            "HIGH: 4 to 6 inquiries — inquiry_penalty_factor = 0.70. "
            "CRITICAL: 7 or more inquiries — inquiry_penalty_factor = 0.50. "
            "Soft inquiries excluded. "
            "Penalty factor applied multiplicatively after other adjustments.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.8 Payment Behaviour ──────────────────────────────────
    story += [
        chap_hdr("7.8  Payment Behaviour Scoring Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: payment_behavior_node.", s["BP_Sub"]),
        Paragraph("7.8.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Applicants are scored on a 0 to 100 behaviour scale derived from delinquency "
            "counts and chargeoff history across all tradelines. The behaviour_score feeds "
            "directly into risk aggregation at the weight defined in Section 7.11.",
            s["BP_Directive"]
        ),
    ]
    beh_rows = [
        ["Risk Band",    "30+ DPD Count\n[TEMPLATE VALUE]", "Chargeoff Present\n[TEMPLATE VALUE]",
         "Behaviour Score\n[TEMPLATE VALUE]", "Aggregation Sub-Score"],
        ["EXCELLENT",   "0",             "None",               "90 to 100", "90"],
        ["GOOD",        "1 to 2",        "None",               "75 to 89",  "80"],
        ["FAIR",        "3 to 5",        "Older than 2 years", "50 to 74",  "65"],
        ["POOR",        "6 or more",     "Within past 2 years","25 to 49",  "30"],
        ["UNACCEPTABLE","Multiple chargeoffs","Active collections","5 to 24", "5"],
    ]
    story += [
        data_table(beh_rows, [2.8 * cm, 3.2 * cm, 3.5 * cm, 3.5 * cm, 4.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Behaviour Scoring Bands",
            "EXCELLENT: 0 delinquencies, no chargeoffs — behaviour_score = 95 — aggregation sub-score = 90. "
            "GOOD: 1 to 2 delinquencies, no chargeoffs — behaviour_score = 80 — aggregation sub-score = 80. "
            "FAIR: 3 to 5 delinquencies OR chargeoff older than 2 years — behaviour_score = 65 — aggregation sub-score = 65. "
            "POOR: 6 or more delinquencies OR chargeoff within 2 years — behaviour_score = 30 — aggregation sub-score = 30. "
            "UNACCEPTABLE: multiple chargeoffs or active collections — behaviour_score = 5 — aggregation sub-score = 5. "
            "chargeoff_history = True if any tradeline has been written off by a lender.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.9 Income / DTI ───────────────────────────────────────
    story += [
        chap_hdr("7.9  Income Verification and DTI Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: income_analysis_node.", s["BP_Sub"]),
        Paragraph("7.9.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "No loan shall be disbursed without verified income. DTI must be calculated "
            "using verified gross monthly income. Applications where DTI exceeds the "
            "maximum threshold must be declined or restructured.",
            s["BP_Directive"]
        ),
    ]
    dti_rows = [
        ["DTI Range\n[TEMPLATE VALUE]", "Income Risk",   "affordability_flag",
         "Policy Action"],
        ["0% to 30%",  "LOW",           "True",  "Full approval if capacity permits"],
        ["31% to 40%", "MODERATE",      "True",  "Approve with income documentation on file"],
        ["41% to 50%", "HIGH",          "True",  "Approve; flag for post-disbursement monitoring"],
        ["Above 50%",  "UNACCEPTABLE",  "False", "DECLINE or COUNTER_OFFER with reduced principal"],
    ]
    story += [
        data_table(dti_rows, [3 * cm, 2.5 * cm, 3.5 * cm, 8.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "DTI Thresholds and Affordability Rules",
            "DTI = (sum_open_monthly_obligations + proposed_new_EMI) / verified_gross_monthly_income. "
            "LOW: DTI 0.00 to 0.30 — income_risk = LOW, affordability_flag = True. "
            "MODERATE: DTI 0.31 to 0.40 — income_risk = MODERATE, affordability_flag = True. "
            "HIGH: DTI 0.41 to 0.50 — income_risk = HIGH, affordability_flag = True. "
            "UNACCEPTABLE: DTI above 0.50 — income_risk = UNACCEPTABLE, affordability_flag = False. "
            "Missing income: income_missing_flag = True when monthly_income is None or zero; treat DTI as UNACCEPTABLE. "
            "Maximum DTI allowed for any counter-offer option = 0.40.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.10 RAG Policy ────────────────────────────────────────
    story += [
        chap_hdr("7.10  RAG Knowledge Base Maintenance Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: rag_retrieval_node (Indian variant workflow).", s["BP_Sub"]),
        Paragraph("7.10.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "The bank maintains a Qdrant vector store containing chunked policy documents. "
            "The ADS queries this store at runtime to retrieve applicable thresholds for "
            "each risk signal node. This section governs what must be indexed and how "
            "retrieval maps to each node.",
            s["BP_Directive"]
        ),
        Paragraph("7.10.2  Documents That Must Be Indexed", s["BP_Section"]),
    ]
    rag_rows = [
        ["Document",                                           "Collection Name",   "Re-index Trigger"],
        ["This Bank Lending Policy Manual (this document)",    "bank_policy",        "Any threshold change; at minimum annually"],
        ["RBI Master Direction on Automated Credit Assessment","rbi_guidelines",     "Each new RBI circular"],
        ["RBI Master Direction on Interest Rate on Advances",  "rbi_guidelines",     "Each rate direction update"],
        ["RBI Digital Lending Guidelines",                     "rbi_guidelines",     "Each guideline revision"],
    ]
    story += [
        data_table(rag_rows, [6 * cm, 4 * cm, 7.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph("7.10.3  Per-Node Query Mapping", s["BP_Section"]),
    ]
    qry_rows = [
        ["ADS Node",              "Query Topic Sent to Vector Store"],
        ["credit_score_node",     "score band thresholds, base limits, risk flags"],
        ["public_record_node",    "bankruptcy severity, adjustment factors, hard-decline rules"],
        ["utilization_node",      "revolving balance thresholds, utilisation adjustment factors"],
        ["debt_exposure_node",    "debt leverage limits, monthly obligation caps"],
        ["inquiry_node",          "inquiry velocity thresholds, penalty structures"],
        ["payment_behavior_node", "delinquency severity, chargeoff rules, behaviour score bands"],
        ["income_analysis_node",  "DTI thresholds, affordability rules, income verification"],
    ]
    story += [
        data_table(qry_rows, [5 * cm, 12.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph("• Empty RAG retrieval causes the node to use hardcoded FALLBACK defaults.", s["BP_BulletItem"]),
        Paragraph("• Re-index within 5 business days of any threshold change.", s["BP_BulletItem"]),
        Paragraph("• FALLBACK rate above 5% of daily volume triggers immediate re-index review.", s["BP_BulletItem"]),
        PageBreak(),
    ]

    # ─── 7.11 Aggregation ───────────────────────────────────────
    story += [
        chap_hdr("7.11  Risk Aggregation Weights and Tier Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: risk_aggregator_node.", s["BP_Sub"]),
        Paragraph("7.11.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "Seven risk signals are combined into a composite score using a weighted "
            "average. Weights are fixed and may only change after a formal Model "
            "Governance review approved by the Chief Credit Officer.",
            s["BP_Directive"]
        ),
    ]
    wt_rows = [
        ["Risk Factor",        "Weight\n[TEMPLATE VALUE]", "ADS Node",
         "Normalisation Rule"],
        ["Credit Score",       "0.25",  "credit_score_node",
         "(score minus 300) divided by 5.5, clamped 0 to 100"],
        ["Payment Behaviour",  "0.15",  "payment_behavior_node",
         "Use raw behaviour_score (0 to 100)"],
        ["Public Records",     "0.15",  "public_record_node",
         "NONE = 100, LOW = 90, MODERATE = 60, SEVERE = 30"],
        ["Credit Utilisation", "0.15",  "utilization_node",
         "EXCELLENT = 90, GOOD = 60, MODERATE = 65, CRITICAL = 10"],
        ["Income and DTI",     "0.15",  "income_analysis_node",
         "LOW = 90, MODERATE = 60, HIGH = 65, UNACCEPTABLE = 5"],
        ["Debt Exposure",      "0.10",  "debt_exposure_node",
         "LOW = 90, MODERATE = 60, HIGH = 65, EXTREME = 5"],
        ["Inquiry Velocity",   "0.05",  "inquiry_node",
         "LOW = 90, MODERATE = 60, HIGH = 65, CRITICAL = 10"],
    ]
    story += [
        data_table(wt_rows, [3.5 * cm, 2 * cm, 4 * cm, 8 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Aggregation Weights, Formula and Risk Tier Bands",
            "aggregated_risk_score = sum of (normalised_sub_score multiplied by weight) for all 7 factors. "
            "Weights sum to 1.00. "
            "Hard-decline override: if hard_decline_flag = True then aggregated_risk_score = 0.0. "
            "Tier A: aggregated_risk_score >= 80 — APPROVE. "
            "Tier B: aggregated_risk_score 65 to 79 — APPROVE with conditions. "
            "Tier C: aggregated_risk_score 50 to 64 — COUNTER_OFFER likely. "
            "Tier D: aggregated_risk_score 35 to 49 — COUNTER_OFFER or DECLINE. "
            "Tier F: aggregated_risk_score below 35 — DECLINE.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.12 Decision / Pricing ────────────────────────────────
    story += [
        chap_hdr("7.12  Lending Decision and Pricing Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: decision_llm_node.", s["BP_Sub"]),
        Paragraph("7.12.1  Decision Protocol", s["BP_Section"]),
    ]
    dec_rows = [
        ["Step", "Condition",                                               "Action"],
        ["1",    "Risk Tier = F  OR  hard_decline_flag = True",            "Output DECLINE immediately"],
        ["2",    "Assign interest rate by tier",                           "Use rate schedule in 7.12.2"],
        ["3",    "Calculate max capacity",
         "max_approved = base_limit_band x public_record_adj x util_adj x inquiry_penalty"],
        ["4",    "affordability_flag = False",                             "Output DECLINE"],
        ["5",    "Requested <= max_approved",                              "Output APPROVE at requested amount"],
        ["6",    "Requested > max_approved AND max_approved > 0",          "Output COUNTER_OFFER"],
        ["7",    "max_approved = 0",                                       "Output DECLINE"],
        ["8",    "APPROVE: calculate disbursement",
         "disbursement_amount = approved_amount multiplied by 0.98"],
    ]
    story += [
        data_table(dec_rows, [1 * cm, 7 * cm, 9.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph("7.12.2  Interest Rate Schedule", s["BP_Section"]),
    ]
    rate_rows = [
        ["Tier",            "Annual Rate\n[TEMPLATE VALUE]", "Monthly Rate",   "Products\n[TEMPLATE VALUE]"],
        ["A (PRIME)",       "7.5%",   "0.625%",  "Personal loans, home loans, MSME term loans"],
        ["B (NEAR_PRIME)",  "10.0%",  "0.833%",  "Personal loans, vehicle finance"],
        ["C (FAIR)",        "13.5%",  "1.125%",  "Unsecured personal credit, top-up loans"],
        ["D (SUBPRIME)",    "18.0%",  "1.500%",  "Secured personal loans, micro-credit only"],
        ["F (DECLINE)",     "N/A",    "N/A",     "No lending permitted"],
    ]
    story += [
        data_table(rate_rows, [2.5 * cm, 3.5 * cm, 3 * cm, 8.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Interest Rate and Origination Fee",
            "Tier A interest rate = 7.5% per annum. "
            "Tier B interest rate = 10.0% per annum. "
            "Tier C interest rate = 13.5% per annum. "
            "Tier D interest rate = 18.0% per annum. "
            "origination_fee_rate = 0.02 (2% of approved amount). "
            "disbursement_amount = approved_amount multiplied by (1 minus origination_fee_rate). "
            "Example: approved INR 10,00,000 at 2% fee yields disbursement of INR 9,80,000.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.13 Counter-Offer ─────────────────────────────────────
    story += [
        chap_hdr("7.13  Counter-Offer Generation Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("ADS node: counter_offer_node.", s["BP_Sub"]),
        Paragraph("7.13.1  Policy Statement", s["BP_Section"]),
        Paragraph(
            "When requested amount exceeds assessed capacity, the counter-offer node "
            "must generate at least two restructured loan options. Every option must "
            "bring the EMI within the affordability ceiling.",
            s["BP_Directive"]
        ),
    ]
    co_rows = [
        ["Option ID",           "Principal Reduction\n[TEMPLATE VALUE]",
         "Tenure Change\n[TEMPLATE VALUE]", "EMI Ceiling",      "Min Tenure"],
        ["OPT_REDUCED_AMOUNT",  "15% reduction (x 0.85)",  "No change",           "35% of monthly income", "12 months"],
        ["OPT_EXTENDED_TERM",   "30% reduction (x 0.70)",  "Add 12 months",       "35% of monthly income", "36 months"],
    ]
    story += [
        data_table(co_rows, [4 * cm, 4 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        tpl_box(
            "Counter-Offer Generation Rules",
            "max_affordable_emi = verified_monthly_income multiplied by 0.35. "
            "OPT_REDUCED_AMOUNT: proposed_amount = requested_amount multiplied by 0.85, tenure unchanged. "
            "OPT_EXTENDED_TERM: proposed_amount = requested_amount multiplied by 0.70, "
            "proposed_tenure = requested_tenure plus 12 months. "
            "Origination fee 2% applies to disbursement on all options. "
            "counter_offer_logic must state reason original amount was not sanctioned. "
            "If max_approved = 0 then output DECLINE instead of counter-offer.",
            s, "BP_Tpl", "BP_Body",
            colors.HexColor("#E8F5E9"), BP_ACCENT
        ),
        PageBreak(),
    ]

    # ─── 7.14 Fallback ──────────────────────────────────────────
    story += [
        chap_hdr("7.14  Model Fallback and Human Override Policy", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("Applicable to all LLM-based ADS nodes.", s["BP_Sub"]),
        Paragraph("7.14.1  Fallback Activation", s["BP_Section"]),
        Paragraph(
            "Every LLM-based node must implement a deterministic fallback path that "
            "activates when the LLM call fails, times out, or returns an unparseable "
            "response. All fallback activations must be logged with llm_response_type = FALLBACK.",
            s["BP_Directive"]
        ),
    ]
    fb_rows = [
        ["Node",                  "Fallback Defaults Applied"],
        ["credit_score_node",     "Hardcoded score bands and base limits from Section 7.3"],
        ["public_record_node",    "Hardcoded severity rules from Section 7.4"],
        ["utilization_node",      "Hardcoded utilisation tiers from Section 7.5"],
        ["debt_exposure_node",    "Hardcoded exposure tiers from Section 7.6"],
        ["inquiry_node",          "Hardcoded velocity tiers from Section 7.7"],
        ["payment_behavior_node", "Hardcoded behaviour rubric from Section 7.8"],
        ["income_analysis_node",  "Hardcoded DTI bands from Section 7.9"],
        ["decision_llm_node",
         "score >= 75 then APPROVE at requested amount and tier rate; "
         "score 55 to 74 then COUNTER_OFFER at 80% of requested; score below 55 then DECLINE"],
        ["counter_offer_node",
         "OPT_REDUCED_AMOUNT at 85% of requested; OPT_EXTENDED_TERM at 70%, plus 12 months"],
    ]
    story += [
        data_table(fb_rows, [5 * cm, 12.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph("7.14.2  Human Override Requirements", s["BP_Section"]),
        Paragraph("• FALLBACK decisions must be reviewed by a credit officer within 24 hours.", s["BP_BulletItem"]),
        Paragraph("• Human overrides must log: officer ID, timestamp, override reason.", s["BP_BulletItem"]),
        Paragraph("• Override volume above 5% of daily applications triggers Technology Risk escalation.", s["BP_BulletItem"]),
        PageBreak(),
    ]

    # ─── 7.15 Audit ─────────────────────────────────────────────
    story += [
        chap_hdr("7.15  Audit, Reporting and Compliance", "BP_Chapter", s, BP_DARK), sp(),
        Paragraph("Applicable to all ADS nodes via audit decorator.", s["BP_Sub"]),
        Paragraph("7.15.1  Mandatory Audit Fields", s["BP_Section"]),
    ]
    aud_rows = [
        ["Field",                  "Content",                                "Retention\n[TEMPLATE VALUE]"],
        ["application_id",         "Unique application identifier",           "Permanent"],
        ["correlation_id",         "Request trace identifier",               "Permanent"],
        ["node_execution_times",   "Duration of each node in milliseconds",  "90 days"],
        ["model_reasoning",        "LLM explanation per classification",      "7 years"],
        ["llm_response_type",      "RAG or FALLBACK",                        "7 years"],
        ["confidence_score",       "Model confidence 0 to 1 per output",     "7 years"],
        ["reasoning_trace",        "Aggregator sub-scores and hard-decline flag","7 years"],
        ["reasoning_steps",        "Decision node step-by-step logic",       "7 years"],
        ["rag_pool",               "Source documents and chunk IDs used",    "7 years"],
        ["decision",               "APPROVE, COUNTER_OFFER, or DECLINE",     "7 years"],
        ["decline_reason",         "Explanation for adverse decision",        "7 years"],
    ]
    story += [
        data_table(aud_rows, [4 * cm, 8 * cm, 5.5 * cm], BP_DARK, BP_LIGHT),
        sp(),
        Paragraph("7.15.2  Reporting Schedule", s["BP_Section"]),
        Paragraph("• Monthly to Board Risk Committee: approval rate, decline rate, FALLBACK rate, override rate.", s["BP_BulletItem"]),
        Paragraph("• Quarterly model validation to confirm thresholds reflect current portfolio performance.", s["BP_BulletItem"]),
        Paragraph("• Annual third-party model audit if portfolio above INR 500 crore.", s["BP_BulletItem"]),
        Paragraph("• Adverse action notice to applicant within 7 working days of DECLINE or COUNTER_OFFER.", s["BP_BulletItem"]),
        sp(2),
        Table([[Paragraph(
            "<b>Document Control:</b>  Policy Owner: Chief Credit Officer  |  "
            "Approved by: Board Risk Committee  |  Review Frequency: Annual  |  "
            "Next Review: [TEMPLATE VALUE]  |  Version: [TEMPLATE VALUE]",
            s["BP_Body"]
        )]], colWidths=[17.5 * cm], style=TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BP_LIGHT),
            ("BOX",           (0, 0), (-1, -1), 0.8, BP_DARK),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])),
    ]

    doc.build(story)
    print(f"  Generated: {path}")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rbi_path  = os.path.join(OUTPUT_DIR, "RBI_Master_Direction_Template.pdf")
    bank_path = os.path.join(OUTPUT_DIR, "Bank_Lending_Policy_Template.pdf")
    print("Generating policy template PDFs...")
    build_rbi(rbi_path)
    build_bank(bank_path)
    print("Done.")
