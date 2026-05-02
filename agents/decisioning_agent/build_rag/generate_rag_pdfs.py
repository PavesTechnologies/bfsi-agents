"""
Generates two RAG-source PDFs for the BFSI decisioning agent:

  1. build_rag/bank_policies/Bank_Lending_Policy.pdf
     - One section per node, labelled to match NODE_CONCERN_QUERIES
     - Bank fills in [BANK VALUE] placeholders and re-ingests

  2. build_rag/rbi_guidelines/RBI_Guidelines_Individual_Loans_India.pdf
     - Common RBI guidelines for individual retail loans in India
     - Retrieved once and shared across all 7 analyzer nodes

Run:  python generate_rag_pdfs.py
"""

import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

BASE  = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().strftime("%d %B %Y")

# ── colours ──────────────────────────────────────────────────────
TEAL_D  = colors.HexColor("#004D40")
TEAL_L  = colors.HexColor("#E0F2F1")
NAVY    = colors.HexColor("#1A237E")
NAVY_L  = colors.HexColor("#E8EAF6")
AMBER   = colors.HexColor("#E65100")
AMBER_L = colors.HexColor("#FFF3E0")
GREY    = colors.HexColor("#BDBDBD")
DARK    = colors.HexColor("#212121")
WHITE   = colors.white


# ── style helpers ─────────────────────────────────────────────────
def make_styles(accent):
    s = getSampleStyleSheet()
    def add(n, **kw): s.add(ParagraphStyle(name=n, **kw))
    add("H_Cover",  fontName="Helvetica-Bold", fontSize=18, textColor=WHITE,
        alignment=TA_CENTER, leading=24, spaceAfter=4)
    add("H_Sub",    fontName="Helvetica",      fontSize=10, textColor=WHITE,
        alignment=TA_CENTER, leading=14, spaceAfter=2)
    add("H_Meta",   fontName="Helvetica",      fontSize=8,  textColor=WHITE,
        alignment=TA_CENTER)
    add("H_Chap",   fontName="Helvetica-Bold", fontSize=12, textColor=WHITE,
        alignment=TA_LEFT, leading=16, spaceBefore=2, spaceAfter=2)
    add("H_Sec",    fontName="Helvetica-Bold", fontSize=10, textColor=accent,
        spaceBefore=8, spaceAfter=2)
    add("H_Sub2",   fontName="Helvetica-Bold", fontSize=9,  textColor=accent,
        spaceBefore=4, spaceAfter=2)
    add("Body",     fontName="Helvetica",      fontSize=9,  textColor=DARK,
        alignment=TA_JUSTIFY, leading=14, spaceAfter=4)
    add("Li",       fontName="Helvetica",      fontSize=9,  textColor=DARK,
        leftIndent=14, spaceAfter=2, leading=13)
    add("CodeBlock", fontName="Courier",        fontSize=8,  textColor=DARK,
        leftIndent=14, spaceAfter=2, leading=13)
    add("NodeTag",  fontName="Helvetica-Bold", fontSize=8,  textColor=AMBER,
        spaceAfter=2)
    return s


def sp(n=1):  return Spacer(1, n * 0.25 * cm)


def cover(title, sub, doc_no, issuer, accent, s):
    rows = [
        [Paragraph(title, s["H_Cover"])], [sp()],
        [Paragraph(sub,   s["H_Sub"])],
        [Paragraph(f"Doc: {doc_no}  |  Effective: {TODAY}", s["H_Meta"])],
        [Paragraph(f"Issued by: {issuer}", s["H_Meta"])],
    ]
    t = Table(rows, colWidths=[17.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), accent),
        ("LEFTPADDING",   (0,0),(-1,-1), 24),
        ("RIGHTPADDING",  (0,0),(-1,-1), 24),
        ("TOPPADDING",    (0,0),(-1, 0), 28),
        ("BOTTOMPADDING", (0,-1),(-1,-1), 24),
    ]))
    return t


def chap(title, accent, s):
    t = Table([[Paragraph(title, s["H_Chap"])]], colWidths=[17.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), accent),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
    ]))
    return t


def node_tag(label, s):
    t = Table([[Paragraph(f"ADS NODE: {label}", s["NodeTag"])]], colWidths=[17.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), AMBER_L),
        ("BOX",           (0,0),(-1,-1), 0.8, AMBER),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))
    return t


def note(text, s, bg=AMBER_L, border=AMBER):
    t = Table([[Paragraph(text, s["Body"])]], colWidths=[17.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("BOX",           (0,0),(-1,-1), 0.8, border),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    return t


def dtbl(rows, widths, hdr_bg, alt):
    t = Table(rows, colWidths=widths)
    ts = [
        ("BACKGROUND",    (0,0),(-1, 0), hdr_bg),
        ("TEXTCOLOR",     (0,0),(-1, 0), WHITE),
        ("FONTNAME",      (0,0),(-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ALIGN",         (0,0),(-1, 0), "CENTER"),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),
        ("RIGHTPADDING",  (0,0),(-1,-1), 7),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("GRID",          (0,0),(-1,-1), 0.4, GREY),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, alt]),
    ]
    t.setStyle(TableStyle(ts))
    return t


# ══════════════════════════════════════════════════════════════════
#  PDF 1 — Bank Lending Policy (per-node sections)
# ══════════════════════════════════════════════════════════════════
def build_bank_policy(path):
    s   = make_styles(TEAL_D)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="Bank Lending Policy – AI Decisioning Parameters",
    )
    story = []

    story += [
        cover(
            "[BANK NAME] — Credit Risk Division",
            "Automated Lending Decisioning: Node-Specific Policy Parameters\n"
            "Source document for RAG knowledge base ingestion",
            "BP-ADS-2025-01", "Chief Credit Officer — [SIGNATURE REQUIRED]",
            TEAL_D, s
        ),
        sp(2),
        note(
            "<b>How to use this document:</b>  Each section below corresponds to exactly "
            "one node in the AI decisioning pipeline. Replace every <b>[BANK VALUE]</b> "
            "with your board-approved figure, then re-ingest this PDF into the "
            "<b>bank_policies</b> Qdrant collection. The AI will retrieve these values "
            "at runtime — no code changes needed.",
            s, TEAL_L, TEAL_D
        ),
        sp(2),
        PageBreak(),
    ]

    # ── Section 1: Credit Score Node ────────────────────────────
    story += [
        chap("Section 1: Credit Score Band Classification Parameters", TEAL_D, s), sp(),
        node_tag("credit_score_node", s), sp(),
        Paragraph(
            "This section defines the credit score band thresholds, base lending limits, "
            "risk flags, and aggregation weight that the credit_score_node reads from the "
            "knowledge base. All values below are ingested and retrieved by the RAG system "
            "when the node queries: <i>Credit score band classification thresholds for "
            "personal loan: PRIME NEAR_PRIME FAIR SUBPRIME score ranges. Base lending limit "
            "by score band. Risk flag LOW MODERATE HIGH mapping. Score weight in aggregated "
            "risk computation.</i>",
            s["Body"]
        ), sp(),

        Paragraph("1.1  Score Band Thresholds", s["H_Sec"]),
        Paragraph("Score band thresholds classify every applicant's CIBIL or bureau credit score "
                  "into one of four risk bands for personal loan assessment:", s["Body"]),
        Paragraph("- PRIME: credit score [BANK VALUE] or higher  (example: 720 or higher)", s["Li"]),
        Paragraph("- NEAR_PRIME: credit score [BANK VALUE] to [BANK VALUE]  (example: 680 to 719)", s["Li"]),
        Paragraph("- FAIR: credit score [BANK VALUE] to [BANK VALUE]  (example: 640 to 679)", s["Li"]),
        Paragraph("- SUBPRIME: credit score below [BANK VALUE]  (example: below 640)", s["Li"]),
        sp(),

        Paragraph("1.2  Base Lending Limit by Score Band", s["H_Sec"]),
        Paragraph("Base lending limit is the maximum loan amount before any adjustment factors "
                  "are applied. The credit_score_node sets base_limit_band to these values:", s["Body"]),
        Paragraph("- PRIME score band base lending limit: INR [BANK VALUE]  (example: 75000)", s["Li"]),
        Paragraph("- NEAR_PRIME score band base lending limit: INR [BANK VALUE]  (example: 50000)", s["Li"]),
        Paragraph("- FAIR score band base lending limit: INR [BANK VALUE]  (example: 35000)", s["Li"]),
        Paragraph("- SUBPRIME score band base lending limit: INR [BANK VALUE]  (example: 20000)", s["Li"]),
        sp(),

        Paragraph("1.3  Risk Flag by Score Band", s["H_Sec"]),
        Paragraph("The score_risk_flag field is populated as follows:", s["Body"]),
        Paragraph("- PRIME score band risk flag: LOW", s["Li"]),
        Paragraph("- NEAR_PRIME score band risk flag: MODERATE", s["Li"]),
        Paragraph("- FAIR score band risk flag: MODERATE", s["Li"]),
        Paragraph("- SUBPRIME score band risk flag: HIGH", s["Li"]),
        sp(),

        Paragraph("1.4  Score Weight in Risk Aggregation", s["H_Sec"]),
        Paragraph("The credit score weight in the composite risk aggregation score is: "
                  "[BANK VALUE]  (example: 0.25 representing 25 percent).", s["Body"]),
        Paragraph("score_weight = [BANK VALUE]", s["CodeBlock"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 2: Public Record Node ───────────────────────────
    story += [
        chap("Section 2: Public Record Severity and Hard-Decline Parameters", TEAL_D, s), sp(),
        node_tag("public_record_node", s), sp(),
        Paragraph(
            "This section defines the public record severity classification rules, adjustment "
            "factors, and hard-decline conditions that the public_record_node reads from the "
            "knowledge base. Retrieved when the node queries: <i>Public record severity "
            "classification rules: NONE LOW MODERATE SEVERE. Adjustment factor by severity "
            "level. Hard decline rules for bankruptcy, suit filed, wilful defaulter, "
            "written-off accounts. Years since bankruptcy threshold for severity downgrade.</i>",
            s["Body"]
        ), sp(),

        Paragraph("2.1  Severity Classification Rules", s["H_Sec"]),
        Paragraph("Public record severity is classified as follows based on bureau data:", s["Body"]),
        Paragraph("- NONE: No public records on file. public_record_severity = NONE.", s["Li"]),
        Paragraph("- LOW: Non-bankruptcy adverse records only — minor court judgments, liens "
                  "without default. public_record_severity = LOW.", s["Li"]),
        Paragraph("- MODERATE: Bankruptcy discharged [BANK VALUE] or more years ago  "
                  "(example: 5 or more years). public_record_severity = MODERATE.", s["Li"]),
        Paragraph("- SEVERE: Bankruptcy discharged less than [BANK VALUE] years ago  "
                  "(example: less than 5 years), OR multiple unsatisfied judgments, OR "
                  "active insolvency proceedings, OR wilful defaulter listing. "
                  "public_record_severity = SEVERE.", s["Li"]),
        sp(),

        Paragraph("2.2  Adjustment Factor by Severity", s["H_Sec"]),
        Paragraph("The public_record_adjustment_factor multiplies the base lending limit:", s["Body"]),
        Paragraph("- NONE severity adjustment factor: 1.00  (no reduction)", s["Li"]),
        Paragraph("- LOW severity adjustment factor: [BANK VALUE]  (example: 0.90)", s["Li"]),
        Paragraph("- MODERATE severity adjustment factor: [BANK VALUE]  (example: 0.75)", s["Li"]),
        Paragraph("- SEVERE severity adjustment factor: [BANK VALUE]  (example: 0.50)", s["Li"]),
        sp(),

        Paragraph("2.3  Hard Decline Rules", s["H_Sec"]),
        Paragraph("The hard_decline_flag is set to True — triggering immediate DECLINE — "
                  "in the following conditions:", s["Body"]),
        Paragraph("- Severity equals SEVERE: hard_decline_flag = True.", s["Li"]),
        Paragraph("- Bankruptcy filed within [BANK VALUE] months  (example: 24 months): "
                  "hard_decline_flag = True.", s["Li"]),
        Paragraph("- Applicant is on RBI Wilful Defaulter list: hard_decline_flag = True.", s["Li"]),
        Paragraph("- Active insolvency proceedings under IBC Section 14: "
                  "hard_decline_flag = True.", s["Li"]),
        Paragraph("- All other cases: hard_decline_flag = False.", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 3: Credit Utilisation Node ──────────────────────
    story += [
        chap("Section 3: Revolving Credit Utilisation Parameters", TEAL_D, s), sp(),
        node_tag("utilization_node", s), sp(),
        Paragraph(
            "This section defines the revolving credit utilisation risk bands and adjustment "
            "factors that the utilization_node reads from the knowledge base. Retrieved when "
            "the node queries: <i>Revolving credit utilization ratio risk classification "
            "thresholds: EXCELLENT GOOD HIGH CRITICAL utilization percentage bands. "
            "Adjustment factor multiplier by utilization risk tier.</i>",
            s["Body"]
        ), sp(),

        Paragraph("3.1  Utilisation Risk Classification", s["H_Sec"]),
        Paragraph("Utilisation ratio = total revolving balance divided by total revolving "
                  "credit limit. Only accounts with revolvingOrInstallment = R are included.", s["Body"]),
        Paragraph("- EXCELLENT: utilisation ratio 0 to [BANK VALUE] percent  "
                  "(example: 0 to 15 percent). utilization_risk = EXCELLENT.", s["Li"]),
        Paragraph("- GOOD: utilisation ratio [BANK VALUE] to [BANK VALUE] percent  "
                  "(example: 16 to 35 percent). utilization_risk = GOOD.", s["Li"]),
        Paragraph("- HIGH: utilisation ratio [BANK VALUE] to [BANK VALUE] percent  "
                  "(example: 36 to 60 percent). utilization_risk = HIGH.", s["Li"]),
        Paragraph("- CRITICAL: utilisation ratio above [BANK VALUE] percent  "
                  "(example: above 60 percent). utilization_risk = CRITICAL.", s["Li"]),
        sp(),

        Paragraph("3.2  Adjustment Factor by Utilisation Risk", s["H_Sec"]),
        Paragraph("The utilization_adjustment_factor multiplies the base lending limit:", s["Body"]),
        Paragraph("- EXCELLENT utilisation adjustment factor: [BANK VALUE]  (example: 1.10)", s["Li"]),
        Paragraph("- GOOD utilisation adjustment factor: [BANK VALUE]  (example: 1.00)", s["Li"]),
        Paragraph("- HIGH utilisation adjustment factor: [BANK VALUE]  (example: 0.85)", s["Li"]),
        Paragraph("- CRITICAL utilisation adjustment factor: [BANK VALUE]  (example: 0.70)", s["Li"]),
        Paragraph("If total_credit_limit equals zero, set utilization_ratio to 0.0 and "
                  "utilization_risk to EXCELLENT.", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 4: Debt Exposure Node ───────────────────────────
    story += [
        chap("Section 4: Debt Exposure and Monthly Obligation Parameters", TEAL_D, s), sp(),
        node_tag("debt_exposure_node", s), sp(),
        Paragraph(
            "This section defines the monthly debt obligation bands and exposure risk "
            "classification that the debt_exposure_node reads from the knowledge base. "
            "Retrieved when the node queries: <i>Monthly debt obligation thresholds for "
            "exposure risk classification: LOW MODERATE HIGH EXTREME monthly payment "
            "amount bands in INR. Total outstanding debt ceiling. Monthly EMI estimation "
            "rules for tradelines without payment data.</i>",
            s["Body"]
        ), sp(),

        Paragraph("4.1  Monthly Obligation Bands for Exposure Risk", s["H_Sec"]),
        Paragraph("Monthly obligation bands are applied to monthly_obligation_estimate "
                  "(sum of monthlyPaymentAmount across all open tradelines):", s["Body"]),
        Paragraph("- LOW exposure: monthly obligations below INR [BANK VALUE]  "
                  "(example: below 500). exposure_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE exposure: monthly obligations INR [BANK VALUE] to [BANK VALUE]  "
                  "(example: 500 to 1500). exposure_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH exposure: monthly obligations INR [BANK VALUE] to [BANK VALUE]  "
                  "(example: 1500 to 3500). exposure_risk = HIGH.", s["Li"]),
        Paragraph("- EXTREME exposure: monthly obligations above INR [BANK VALUE]  "
                  "(example: above 3500). exposure_risk = EXTREME.", s["Li"]),
        sp(),

        Paragraph("4.2  Total Existing Debt Calculation", s["H_Sec"]),
        Paragraph("total_existing_debt = sum of balanceAmount across all open tradelines "
                  "(openOrClosed = O).", s["Body"]),
        sp(),

        Paragraph("4.3  EMI Estimation Rule for Missing Payment Data", s["H_Sec"]),
        Paragraph("If monthlyPaymentAmount is absent for an open tradeline, estimate EMI as: "
                  "balanceAmount divided by remaining_terms. If remaining terms are unknown, "
                  "use balanceAmount divided by 36.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 5: Payment Behaviour Node ───────────────────────
    story += [
        chap("Section 5: Payment Behaviour Scoring Parameters", TEAL_D, s), sp(),
        node_tag("payment_behavior_node", s), sp(),
        Paragraph(
            "This section defines the delinquency count thresholds, charge-off detection "
            "rules, and behavior score values that the payment_behavior_node reads from "
            "the knowledge base. Retrieved when the node queries: <i>Delinquency count "
            "and DPD bucket thresholds for behavior risk classification: EXCELLENT FAIR "
            "POOR UNACCEPTABLE behavior score values. Charge-off identification rules. "
            "SMA-0 SMA-1 SMA-2 NPA classification. 30-DPD 60-DPD 90-DPD bucket counting.</i>",
            s["Body"]
        ), sp(),

        Paragraph("5.1  Delinquency Counting Rules", s["H_Sec"]),
        Paragraph("Total delinquencies = sum of delinquencies30Days + delinquencies60Days + "
                  "delinquencies90to180Days across all tradelines. Each field is a string "
                  "count (e.g., 00, 01, 03). This count of 30-DPD, 60-DPD and 90-DPD "
                  "buckets determines the behavior_risk classification.", s["Body"]),
        sp(),

        Paragraph("5.2  Charge-off Detection Rules", s["H_Sec"]),
        Paragraph("chargeoff_history = True if any tradeline meets one of these conditions:", s["Body"]),
        Paragraph("- derogCounter greater than 0", s["Li"]),
        Paragraph("- status code equals 97 or 93 (written-off)", s["Li"]),
        Paragraph("- dpdHistory contains any of: SUB, DBT, LSS, XXX", s["Li"]),
        Paragraph("chargeoff_history = False if none of the above conditions are met.", s["Li"]),
        sp(),

        Paragraph("5.3  Behavior Risk Classification and Behavior Score", s["H_Sec"]),
        Paragraph("Risk classification and behavior_score (0 to 100) are determined as follows:", s["Body"]),
        Paragraph("- EXCELLENT: 0 delinquencies AND no charge-offs — "
                  "behavior_risk = EXCELLENT, behavior_score = [BANK VALUE]  (example: 100)", s["Li"]),
        Paragraph("- FAIR: [BANK VALUE] to [BANK VALUE] delinquencies AND no charge-offs — "
                  "behavior_risk = FAIR, behavior_score = [BANK VALUE]  (example: 1-2 delinquencies, score 75)", s["Li"]),
        Paragraph("- POOR: [BANK VALUE] or more delinquencies AND no charge-offs — "
                  "behavior_risk = POOR, behavior_score = [BANK VALUE]  (example: 3+, score 40)", s["Li"]),
        Paragraph("- UNACCEPTABLE: ANY charge-offs present — "
                  "behavior_risk = UNACCEPTABLE, behavior_score = [BANK VALUE]  (example: 0)", s["Li"]),
        sp(),

        Paragraph("5.4  SMA and NPA Classification Reference", s["H_Sec"]),
        Paragraph("SMA-0 = overdue 1 to 30 days. SMA-1 = overdue 31 to 60 days. "
                  "SMA-2 = overdue 61 to 90 days. NPA = overdue more than 90 days. "
                  "These map to the DPD bucket counts used in delinquency counting.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 6: Inquiry Node ──────────────────────────────────
    story += [
        chap("Section 6: Credit Inquiry Velocity Parameters", TEAL_D, s), sp(),
        node_tag("inquiry_node", s), sp(),
        Paragraph(
            "This section defines the inquiry count thresholds and penalty factors that "
            "the inquiry_node reads from the knowledge base. Retrieved when the node "
            "queries: <i>Credit inquiry count thresholds in last 12 months for velocity "
            "risk: LOW MODERATE HIGH inquiry-count bands. Inquiry penalty factor multiplier "
            "by velocity risk tier.</i>",
            s["Body"]
        ), sp(),

        Paragraph("6.1  Inquiry Counting Window", s["H_Sec"]),
        Paragraph("Count only hard inquiries with dates within the last 12 months from the "
                  "assessment date. Soft inquiries are excluded. inquiries_last_12m is the "
                  "result of this count.", s["Body"]),
        sp(),

        Paragraph("6.2  Velocity Risk Classification by Inquiry Count", s["H_Sec"]),
        Paragraph("velocity_risk is classified based on inquiries_last_12m as follows:", s["Body"]),
        Paragraph("- LOW velocity risk: 0 to [BANK VALUE] inquiries in last 12 months  "
                  "(example: 0 to 2). velocity_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE velocity risk: [BANK VALUE] to [BANK VALUE] inquiries  "
                  "(example: 3 to 5). velocity_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH velocity risk: [BANK VALUE] or more inquiries  "
                  "(example: 6 or more). velocity_risk = HIGH.", s["Li"]),
        sp(),

        Paragraph("6.3  Inquiry Penalty Factor", s["H_Sec"]),
        Paragraph("The inquiry_penalty_factor multiplies the lending limit. Applied "
                  "multiplicatively after public record and utilisation adjustment factors.", s["Body"]),
        Paragraph("- LOW velocity risk inquiry penalty factor: [BANK VALUE]  (example: 1.0)", s["Li"]),
        Paragraph("- MODERATE velocity risk inquiry penalty factor: [BANK VALUE]  (example: 0.95)", s["Li"]),
        Paragraph("- HIGH velocity risk inquiry penalty factor: [BANK VALUE]  (example: 0.85)", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 7: Income Analysis Node ─────────────────────────
    story += [
        chap("Section 7: Income Verification and DTI Policy Parameters", TEAL_D, s), sp(),
        node_tag("income_analysis_node", s), sp(),
        Paragraph(
            "This section defines the DTI thresholds, FOIR limits, and missing-income "
            "handling rules that the income_analysis_node reads from the knowledge base. "
            "Retrieved when the node queries: <i>Debt to income DTI ratio thresholds for "
            "income risk classification: LOW MODERATE HIGH UNACCEPTABLE DTI percentage "
            "bands. Affordability cap, FOIR fixed-obligation-to-income ratio. Missing "
            "income handling rules and defaults.</i>",
            s["Body"]
        ), sp(),

        Paragraph("7.1  DTI Calculation Method", s["H_Sec"]),
        Paragraph("DTI formula: estimated_dti = monthly_obligations divided by monthly_income. "
                  "Monthly obligations = sum of monthlyPaymentAmount from all open tradelines "
                  "plus the proposed new EMI. Income source = bank_statement_summary "
                  "monthly_income field. FOIR (Fixed Obligation to Income Ratio) is equivalent "
                  "to DTI in this context.", s["Body"]),
        sp(),

        Paragraph("7.2  Missing Income Handling", s["H_Sec"]),
        Paragraph("If monthly_income is null, zero, or UNKNOWN:", s["Body"]),
        Paragraph("- income_missing_flag = True", s["Li"]),
        Paragraph("- estimated_dti = 99.9", s["Li"]),
        Paragraph("- income_risk = UNACCEPTABLE", s["Li"]),
        Paragraph("- affordability_flag = False", s["Li"]),
        sp(),

        Paragraph("7.3  DTI Risk Classification Bands", s["H_Sec"]),
        Paragraph("income_risk is classified based on estimated_dti as follows:", s["Body"]),
        Paragraph("- LOW income risk: DTI below [BANK VALUE]  "
                  "(example: below 0.25). income_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE income risk: DTI [BANK VALUE] to [BANK VALUE]  "
                  "(example: 0.25 to 0.35). income_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH income risk: DTI [BANK VALUE] to [BANK VALUE]  "
                  "(example: 0.36 to 0.45). income_risk = HIGH.", s["Li"]),
        Paragraph("- UNACCEPTABLE income risk: DTI above [BANK VALUE]  "
                  "(example: above 0.45). income_risk = UNACCEPTABLE.", s["Li"]),
        sp(),

        Paragraph("7.4  Affordability Cap — FOIR Limit", s["H_Sec"]),
        Paragraph("affordability_flag = True only if DTI is at or below [BANK VALUE]  "
                  "(example: 0.45). This is the maximum FOIR permitted by this bank. "
                  "affordability_flag = False if DTI exceeds this cap. A False "
                  "affordability_flag triggers immediate DECLINE in the decision node.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 8: Decision Node ─────────────────────────────────
    story += [
        chap("Section 8: Lending Decision and Interest Rate Parameters", TEAL_D, s), sp(),
        node_tag("decision_llm_node", s), sp(),
        Paragraph(
            "This section defines interest rates by risk tier, origination fee, and "
            "counter-offer affordability parameters used by the decision_llm_node and "
            "counter_offer_node.",
            s["Body"]
        ), sp(),

        Paragraph("8.1  Interest Rate Schedule by Risk Tier", s["H_Sec"]),
        Paragraph("Annual interest rate by aggregated risk tier:", s["Body"]),
        Paragraph("- Tier A (PRIME risk): interest_rate = [BANK VALUE] percent per annum  "
                  "(example: 7.5)", s["Li"]),
        Paragraph("- Tier B (NEAR_PRIME risk): interest_rate = [BANK VALUE] percent per annum  "
                  "(example: 10.0)", s["Li"]),
        Paragraph("- Tier C (FAIR risk): interest_rate = [BANK VALUE] percent per annum  "
                  "(example: 13.5)", s["Li"]),
        Paragraph("- Tier D (SUBPRIME risk): interest_rate = [BANK VALUE] percent per annum  "
                  "(example: 18.0)", s["Li"]),
        sp(),

        Paragraph("8.2  Origination Fee and Disbursement", s["H_Sec"]),
        Paragraph("- Origination fee: [BANK VALUE] percent of approved amount  (example: 2.0)", s["Li"]),
        Paragraph("- disbursement_amount = approved_amount multiplied by (1 minus origination_fee_rate)  "
                  "(example: 0.98 for 2 percent fee)", s["Li"]),
        sp(),

        Paragraph("8.3  Counter-Offer EMI Affordability Ceiling", s["H_Sec"]),
        Paragraph("max_affordable_emi = monthly_income multiplied by [BANK VALUE]  "
                  "(example: 0.40, representing 40 percent of income) minus existing "
                  "monthly_obligations.", s["Body"]),
        sp(2),
    ]

    doc.build(story)
    print(f"  Generated: {path}")


# ══════════════════════════════════════════════════════════════════
#  PDF 2 — RBI Guidelines for Individual Loans in India
# ══════════════════════════════════════════════════════════════════
def build_rbi_guidelines(path):
    s   = make_styles(NAVY)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="RBI Guidelines – Individual Loans in India",
    )
    story = []

    story += [
        cover(
            "RESERVE BANK OF INDIA",
            "Regulatory Guidelines for Individual and Retail Lending in India\n"
            "Common Framework for AI-Assisted Credit Assessment Systems",
            "RBI/RETAIL-LENDING/2025-GUIDE", "Department of Regulation, RBI",
            NAVY, s
        ),
        sp(2),
        note(
            "<b>Purpose:</b> This document provides the common RBI regulatory framework "
            "that applies to all credit assessment decisions for individual retail loans "
            "in India. It is ingested into the <b>rbi_guidelines</b> knowledge base "
            "collection and retrieved once per application to provide regulatory context "
            "to all AI decisioning nodes.",
            s, NAVY_L, NAVY
        ),
        sp(2),
        PageBreak(),
    ]

    # ── Chapter 1: Framework ────────────────────────────────────
    story += [
        chap("Chapter 1: Regulatory Framework for Retail Lending", NAVY, s), sp(),
        Paragraph("1.1  Scope and Applicability", s["H_Sec"]),
        Paragraph(
            "These guidelines apply to all Regulated Entities (REs) — Scheduled Commercial "
            "Banks, Small Finance Banks, NBFCs, and Housing Finance Companies — that extend "
            "individual retail loans including personal loans, consumer durable loans, two-wheeler "
            "loans, and MSME credit to individuals. All automated or AI-assisted credit "
            "decisioning systems must comply with these directives when assessing individual "
            "borrower creditworthiness.",
            s["Body"]
        ),
        Paragraph("1.2  Responsible Lending Principles", s["H_Sec"]),
        Paragraph(
            "REs must ensure that credit is extended only to borrowers with demonstrated "
            "repayment capacity. Credit assessment must be objective, data-driven, and "
            "free from discrimination. Every assessment must be explainable and the "
            "borrower must be informed of the credit decision and its basis.",
            s["Body"]
        ),
        Paragraph("1.3  Minimum Creditworthiness Assessment", s["H_Sec"]),
        Paragraph(
            "Before approving any individual retail loan, REs must assess: "
            "(a) bureau credit history and score from a licensed Credit Information Company, "
            "(b) repayment capacity through income verification, "
            "(c) existing debt obligations, "
            "(d) public record and legal history, and "
            "(e) recent credit-seeking behaviour through inquiry analysis.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 2: Credit Bureau Usage and CIBIL Score Standards", NAVY, s), sp(),
        Paragraph("2.1  Mandatory Bureau Check", s["H_Sec"]),
        Paragraph(
            "REs shall obtain a credit report from at least one licensed Credit Information "
            "Company (CIBIL, Experian, Equifax, CRIF) before approving any individual loan. "
            "The CIBIL TransUnion Score, Experian Credit Score, or equivalent bureau score "
            "ranges from 300 to 900 for individuals in India.",
            s["Body"]
        ),
        Paragraph("2.2  Credit Score Interpretation", s["H_Sec"]),
        Paragraph(
            "A bureau credit score reflects the borrower's overall creditworthiness based "
            "on repayment history, credit utilisation, length of credit history, credit mix, "
            "and recent inquiries. Higher scores indicate lower credit risk. "
            "REs must classify applicants into internal credit risk bands based on the score "
            "and apply corresponding lending limits and risk flags.",
            s["Body"]
        ),
        Paragraph("2.3  Score-Based Risk Classification Requirements", s["H_Sec"]),
        Paragraph(
            "Each RE must maintain a documented score band policy defining: "
            "(a) the minimum score threshold for each risk tier, "
            "(b) the maximum base lending limit per tier, "
            "(c) the risk flag (LOW, MODERATE, HIGH) for each tier, and "
            "(d) the weight of the credit score in any composite risk score calculation.",
            s["Body"]
        ),
        Paragraph("2.4  New-to-Credit (NTC) Borrowers", s["H_Sec"]),
        Paragraph(
            "For borrowers with no bureau history, REs must use alternative data sources "
            "such as bank account statements, GST filings, or utility payment history. "
            "NTC borrowers should not be automatically declined; alternative assessment "
            "methods must be documented in the credit policy.",
            s["Body"]
        ),
        sp(2),
        PageBreak(),

        chap("Chapter 3: Income Verification and Affordability Standards", NAVY, s), sp(),
        Paragraph("3.1  Mandatory Income Verification", s["H_Sec"]),
        Paragraph(
            "No retail loan shall be sanctioned without verification of the borrower's "
            "income. Acceptable income evidence includes: bank account statements for the "
            "last 6 months, Income Tax Return (ITR) filings, Form 16 or salary slips from "
            "employer, GST returns for self-employed individuals, or audited financial "
            "statements for business owners.",
            s["Body"]
        ),
        Paragraph("3.2  Debt-to-Income Ratio and FOIR", s["H_Sec"]),
        Paragraph(
            "The Fixed Obligation to Income Ratio (FOIR) — equivalent to the "
            "Debt-to-Income (DTI) ratio — is the primary affordability metric. "
            "FOIR is calculated as total monthly fixed obligations (all EMIs plus the "
            "proposed new EMI) divided by net monthly income. "
            "REs must define a maximum FOIR threshold beyond which no loan shall be "
            "sanctioned. This threshold must be documented in the credit policy.",
            s["Body"]
        ),
        Paragraph("3.3  Missing Income Policy", s["H_Sec"]),
        Paragraph(
            "If income cannot be verified from any acceptable source, the application "
            "must be treated as having UNACCEPTABLE income risk. An automated system "
            "must set income_missing_flag to True and reject the application unless "
            "additional manual verification is performed and documented.",
            s["Body"]
        ),
        Paragraph("3.4  Affordability Assessment Requirement", s["H_Sec"]),
        Paragraph(
            "REs must assess whether the proposed EMI is affordable for the borrower. "
            "If the FOIR after including the proposed EMI exceeds the bank's documented "
            "maximum, the application must be declined or restructured to a lower "
            "principal or longer tenure that brings FOIR within permissible limits.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 4: NPA Classification and Payment History Standards", NAVY, s), sp(),
        Paragraph("4.1  IRACP Norms — NPA Classification", s["H_Sec"]),
        Paragraph(
            "As per RBI's Income Recognition, Asset Classification and Provisioning (IRACP) "
            "norms, accounts are classified as Non-Performing Assets (NPA) when overdue "
            "for more than 90 days. The DPD (Days Past Due) classification is: "
            "Standard (0 DPD), SMA-0 (1 to 30 DPD), SMA-1 (31 to 60 DPD), "
            "SMA-2 (61 to 90 DPD), Sub-Standard NPA (91 to 12 months), "
            "Doubtful NPA (more than 12 months), Loss Asset.",
            s["Body"]
        ),
        Paragraph("4.2  Delinquency Assessment in Credit Scoring", s["H_Sec"]),
        Paragraph(
            "REs must count the number of accounts that have experienced 30-DPD, 60-DPD, "
            "and 90-DPD events. Each delinquency event increases credit risk. "
            "The total delinquency count across all tradelines must be used to classify "
            "the borrower's payment behaviour risk tier.",
            s["Body"]
        ),
        Paragraph("4.3  Charge-off and Written-Off Accounts", s["H_Sec"]),
        Paragraph(
            "A charge-off (written-off account) indicates that the lender has given up "
            "on recovering the debt. Accounts with derog_counter greater than zero, "
            "status codes 97 or 93, or DPD history containing SUB, DBT, LSS, or XXX "
            "are considered charge-offs. The presence of any charge-off is treated as "
            "a significant adverse indicator in the payment behaviour assessment.",
            s["Body"]
        ),
        sp(2),
        PageBreak(),

        chap("Chapter 5: Public Records and Insolvency Norms", NAVY, s), sp(),
        Paragraph("5.1  Treatment of Bankruptcies and Insolvency Proceedings", s["H_Sec"]),
        Paragraph(
            "Under the Insolvency and Bankruptcy Code (IBC) 2016, individuals may file "
            "for insolvency. Active insolvency proceedings trigger an automatic moratorium "
            "under IBC Section 14, during which no credit may be extended. "
            "REs must check bureau data for bankruptcy filings and insolvency proceedings "
            "before any credit approval.",
            s["Body"]
        ),
        Paragraph("5.2  Wilful Defaulter Classification", s["H_Sec"]),
        Paragraph(
            "Borrowers classified as wilful defaulters by any lender and reported to the "
            "Central Repository of Information on Large Credits (CRILC) or appearing on "
            "the RBI wilful defaulter list must be declined for any new credit. "
            "This is a mandatory hard decline condition.",
            s["Body"]
        ),
        Paragraph("5.3  Severity-Based Adjustment", s["H_Sec"]),
        Paragraph(
            "Where public records are present but do not trigger a hard decline — such as "
            "satisfied judgments or bankruptcies discharged several years ago — REs must "
            "apply a documented adjustment factor that reduces the maximum lending limit. "
            "This adjustment must be conservative and proportional to the severity and "
            "recency of the adverse event.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 6: Credit Utilisation and Revolving Credit Assessment", NAVY, s), sp(),
        Paragraph("6.1  Revolving Credit Utilisation Standard", s["H_Sec"]),
        Paragraph(
            "Credit utilisation measures the proportion of available revolving credit "
            "currently in use. High utilisation (typically above 60 percent) is an "
            "indicator of financial stress and reduces the RE's willingness to extend "
            "additional credit. Only revolving credit facilities (credit cards, overdrafts, "
            "cash credit accounts) should be included in the utilisation calculation; "
            "instalment loans must be excluded.",
            s["Body"]
        ),
        Paragraph("6.2  Utilisation as a Risk Signal", s["H_Sec"]),
        Paragraph(
            "REs must define utilisation risk bands and corresponding adjustment factors "
            "that reduce the base lending limit proportionally. Low utilisation may be "
            "treated favourably with a positive adjustment. High utilisation indicates "
            "the borrower is nearing their credit limits and warrants a reduction in "
            "the maximum loan amount.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 7: Credit Inquiry Governance", NAVY, s), sp(),
        Paragraph("7.1  Inquiry Velocity as a Risk Indicator", s["H_Sec"]),
        Paragraph(
            "Multiple credit inquiries in a short period indicate either financial distress "
            "(seeking multiple credit lines simultaneously) or possible fraud. "
            "REs must count the number of hard credit inquiries in the preceding "
            "12 months and classify the borrower's inquiry velocity risk.",
            s["Body"]
        ),
        Paragraph("7.2  Hard vs Soft Inquiries", s["H_Sec"]),
        Paragraph(
            "Hard inquiries (initiated by the borrower seeking credit) must be counted "
            "for velocity risk assessment. Soft inquiries (e.g., account monitoring by "
            "existing lenders) must be excluded from the count. "
            "High inquiry velocity warrants an inquiry penalty factor that reduces "
            "the lending limit.",
            s["Body"]
        ),
        sp(2),
        PageBreak(),

        chap("Chapter 8: Debt Exposure and Leverage Norms", NAVY, s), sp(),
        Paragraph("8.1  Total Outstanding Debt Assessment", s["H_Sec"]),
        Paragraph(
            "REs must assess the borrower's total outstanding indebtedness across all "
            "open credit accounts before extending new credit. Total existing debt "
            "and estimated monthly obligations from open tradelines must be computed "
            "and classified into exposure risk tiers.",
            s["Body"]
        ),
        Paragraph("8.2  Monthly Obligation Estimation", s["H_Sec"]),
        Paragraph(
            "Where the exact monthly payment is not available from the bureau report, "
            "REs must apply a documented estimation methodology. A common approach is "
            "to divide the outstanding balance by the estimated remaining tenure. "
            "This estimated obligation must be included in the FOIR calculation.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 9: Risk Aggregation and Composite Scoring", NAVY, s), sp(),
        Paragraph("9.1  Composite Risk Score Requirement", s["H_Sec"]),
        Paragraph(
            "REs using automated decisioning systems must maintain a documented composite "
            "risk scoring methodology that combines multiple credit risk signals. "
            "The composite score must be computed using a weighted average of individual "
            "risk signals. All weights must be documented, sum to 100 percent, and "
            "be subject to periodic model validation.",
            s["Body"]
        ),
        Paragraph("9.2  Hard Decline Override", s["H_Sec"]),
        Paragraph(
            "Certain adverse conditions — active insolvency proceedings, wilful defaulter "
            "classification, bankruptcy within the look-back period — must trigger an "
            "unconditional decline regardless of the composite risk score. "
            "No positive score from other risk factors may override these hard decline "
            "conditions. When a hard decline flag is triggered, the composite risk score "
            "must be set to zero.",
            s["Body"]
        ),
        Paragraph("9.3  Risk Tier Classification", s["H_Sec"]),
        Paragraph(
            "The composite risk score must be mapped to discrete risk tiers (such as A, B, "
            "C, D, F) that drive the lending decision and interest rate assignment. "
            "Higher tiers (A, B) represent lower risk and attract more favourable interest "
            "rates. Lower tiers (D, F) represent higher risk and attract higher rates "
            "or mandatory decline.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 10: Lending Decision and Interest Rate Regulation", NAVY, s), sp(),
        Paragraph("10.1  Risk-Based Pricing Requirement", s["H_Sec"]),
        Paragraph(
            "As per RBI's Master Direction on Interest Rate on Advances, REs must link "
            "interest rates to the borrower's risk profile. Higher-risk borrowers must "
            "be charged higher interest rates. All interest rates must be based on the "
            "Marginal Cost of Funds Based Lending Rate (MCLR) or external benchmark "
            "plus a documented risk spread. The risk spread must reflect the borrower's "
            "credit tier.",
            s["Body"]
        ),
        Paragraph("10.2  Origination Fee and Charges Transparency", s["H_Sec"]),
        Paragraph(
            "All loan charges — including origination fee, processing fee, and prepayment "
            "penalty — must be disclosed to the borrower upfront as per the Fair Practices "
            "Code. The disbursement amount (after deducting origination fee) must be "
            "clearly stated in the sanction letter.",
            s["Body"]
        ),
        Paragraph("10.3  Counter-Offer Obligation", s["H_Sec"]),
        Paragraph(
            "Where the requested loan amount exceeds the assessed lending capacity but the "
            "borrower is not subject to a hard decline, REs must not issue an outright "
            "rejection. A counter-offer with a reduced principal amount and/or extended "
            "tenure must be computed and presented to the applicant, demonstrating the "
            "RE's effort to meet the borrower's credit needs within permissible limits.",
            s["Body"]
        ),
        sp(2),

        chap("Chapter 11: Audit, Explainability and Consumer Protection", NAVY, s), sp(),
        Paragraph("11.1  Explainability of AI Credit Decisions", s["H_Sec"]),
        Paragraph(
            "All automated or AI-assisted credit decisions must be explainable. "
            "The system must maintain a reasoning trace documenting which factors "
            "contributed to the decision, what thresholds were applied, and whether "
            "the values were retrieved from policy guidance (RAG) or generated "
            "by the model (FALLBACK). This trace must be retained for regulatory inspection.",
            s["Body"]
        ),
        Paragraph("11.2  Adverse Action Notice", s["H_Sec"]),
        Paragraph(
            "As per RBI's Fair Practices Code, every borrower who receives a DECLINE "
            "or COUNTER_OFFER must be informed of the decision and its primary reason "
            "within a reasonable timeframe. The written communication must cite the "
            "credit factors that led to the adverse decision in plain language.",
            s["Body"]
        ),
        Paragraph("11.3  Data Privacy and PII Protection", s["H_Sec"]),
        Paragraph(
            "Bureau data containing personal identifiers — name, address, account numbers, "
            "employer details, court record references — must be masked before processing "
            "through any AI or ML model. The original PII-bearing payload must not be "
            "accessible to any model or downstream system. This is mandatory under the "
            "Digital Personal Data Protection Act 2023 and RBI's Digital Lending Guidelines.",
            s["Body"]
        ),
        Paragraph("11.4  Audit Trail Requirements", s["H_Sec"]),
        Paragraph(
            "REs must maintain a complete audit trail for every AI-assisted credit decision, "
            "including: the application identifier, the credit signals evaluated, the "
            "policy sources retrieved (RAG pool), the composite risk score, the risk tier, "
            "the decision rationale, and the final outcome. Audit records must be retained "
            "for a minimum of 7 years.",
            s["Body"]
        ),
        sp(2),
    ]

    doc.build(story)
    print(f"  Generated: {path}")


# ══════════════════════════════════════════════════════════════════
#  PDF 3 — Bank Lending Policy SAMPLE (filled values for testing)
# ══════════════════════════════════════════════════════════════════
GREEN_D = colors.HexColor("#1B5E20")
GREEN_L = colors.HexColor("#E8F5E9")
GREEN_M = colors.HexColor("#2E7D32")


def build_bank_policy_sample(path):
    """
    Identical structure to build_bank_policy() but every [BANK VALUE]
    is replaced with a concrete sample figure so the RAG system can be
    tested end-to-end without manual editing.

    These are illustrative values — not real bank policy.
    """
    s   = make_styles(GREEN_D)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
        title="Bank Lending Policy – SAMPLE (Testing Only)",
    )
    story = []

    # ── Cover ────────────────────────────────────────────────────
    story += [
        cover(
            "SAMPLE BANK — Credit Risk Division",
            "Automated Lending Decisioning: Node-Specific Policy Parameters\n"
            "SAMPLE DOCUMENT — For RAG Testing and Evaluation Only",
            "BP-ADS-SAMPLE-01", "Chief Credit Officer — SAMPLE ONLY",
            GREEN_D, s
        ),
        sp(2),
        note(
            "<b>TESTING DOCUMENT:</b>  All values in this PDF are filled sample figures "
            "intended for end-to-end RAG pipeline testing. Ingest this file into the "
            "<b>bank_policies</b> Qdrant collection and run an application through the "
            "decisioning agent to verify that all 7 nodes retrieve policy values with "
            "llm_response_type = \"RAG\". Replace with board-approved values before "
            "production use.",
            s, GREEN_L, GREEN_D
        ),
        sp(2),
        PageBreak(),
    ]

    # ── Section 1: Credit Score Node ────────────────────────────
    story += [
        chap("Section 1: Credit Score Band Classification Parameters", GREEN_D, s), sp(),
        node_tag("credit_score_node", s), sp(),
        Paragraph(
            "This section defines the credit score band thresholds, base lending limits, "
            "risk flags, and aggregation weight that the credit_score_node reads from the "
            "knowledge base. Retrieved when the node queries: <i>Credit score band "
            "classification thresholds for personal loan: PRIME NEAR_PRIME FAIR SUBPRIME "
            "score ranges. Base lending limit by score band. Risk flag LOW MODERATE HIGH "
            "mapping. Score weight in aggregated risk computation.</i>",
            s["Body"]
        ), sp(),

        Paragraph("1.1  Score Band Thresholds", s["H_Sec"]),
        Paragraph("Score band thresholds classify every applicant's CIBIL bureau credit score "
                  "into one of four risk bands for personal loan assessment:", s["Body"]),
        Paragraph("- PRIME: credit score 750 or higher", s["Li"]),
        Paragraph("- NEAR_PRIME: credit score 700 to 749", s["Li"]),
        Paragraph("- FAIR: credit score 650 to 699", s["Li"]),
        Paragraph("- SUBPRIME: credit score below 650", s["Li"]),
        sp(),

        Paragraph("1.2  Base Lending Limit by Score Band (INR)", s["H_Sec"]),
        Paragraph("Base lending limit is the maximum loan amount before any adjustment factors "
                  "are applied. The credit_score_node sets base_limit_band to these values:", s["Body"]),
        Paragraph("- PRIME score band base lending limit: INR 1000000  (10 Lakh)", s["Li"]),
        Paragraph("- NEAR_PRIME score band base lending limit: INR 750000  (7.5 Lakh)", s["Li"]),
        Paragraph("- FAIR score band base lending limit: INR 500000  (5 Lakh)", s["Li"]),
        Paragraph("- SUBPRIME score band base lending limit: INR 250000  (2.5 Lakh)", s["Li"]),
        sp(),

        Paragraph("1.3  Risk Flag by Score Band", s["H_Sec"]),
        Paragraph("The score_risk_flag field is populated as follows:", s["Body"]),
        Paragraph("- PRIME score band risk flag: LOW", s["Li"]),
        Paragraph("- NEAR_PRIME score band risk flag: MODERATE", s["Li"]),
        Paragraph("- FAIR score band risk flag: MODERATE", s["Li"]),
        Paragraph("- SUBPRIME score band risk flag: HIGH", s["Li"]),
        sp(),

        Paragraph("1.4  Score Weight in Risk Aggregation", s["H_Sec"]),
        Paragraph("The credit score weight in the composite risk aggregation score is 0.30 "
                  "(representing 30 percent of the total risk score).", s["Body"]),
        Paragraph("score_weight = 0.30", s["CodeBlock"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 2: Public Record Node ───────────────────────────
    story += [
        chap("Section 2: Public Record Severity and Hard-Decline Parameters", GREEN_D, s), sp(),
        node_tag("public_record_node", s), sp(),
        Paragraph(
            "This section defines public record severity classification rules, adjustment "
            "factors, and hard-decline conditions that the public_record_node reads from "
            "the knowledge base. Retrieved when the node queries: <i>Public record severity "
            "classification rules: NONE LOW MODERATE SEVERE. Adjustment factor by severity "
            "level. Hard decline rules for bankruptcy, suit filed, wilful defaulter, "
            "written-off accounts. Years since bankruptcy threshold for severity downgrade.</i>",
            s["Body"]
        ), sp(),

        Paragraph("2.1  Severity Classification Rules", s["H_Sec"]),
        Paragraph("Public record severity is classified as follows based on bureau data:", s["Body"]),
        Paragraph("- NONE: No public records on file. public_record_severity = NONE.", s["Li"]),
        Paragraph("- LOW: Non-bankruptcy adverse records only — minor court judgments or liens "
                  "without active default. public_record_severity = LOW.", s["Li"]),
        Paragraph("- MODERATE: Bankruptcy discharged 5 or more years ago. "
                  "public_record_severity = MODERATE.", s["Li"]),
        Paragraph("- SEVERE: Bankruptcy discharged less than 5 years ago, OR multiple unsatisfied "
                  "judgments, OR active insolvency proceedings, OR RBI wilful defaulter listing. "
                  "public_record_severity = SEVERE.", s["Li"]),
        sp(),

        Paragraph("2.2  Adjustment Factor by Severity", s["H_Sec"]),
        Paragraph("The public_record_adjustment_factor multiplies the base lending limit:", s["Body"]),
        Paragraph("- NONE severity adjustment factor: 1.00  (no reduction)", s["Li"]),
        Paragraph("- LOW severity adjustment factor: 0.90  (10 percent reduction)", s["Li"]),
        Paragraph("- MODERATE severity adjustment factor: 0.75  (25 percent reduction)", s["Li"]),
        Paragraph("- SEVERE severity adjustment factor: 0.50  (50 percent reduction)", s["Li"]),
        sp(),

        Paragraph("2.3  Hard Decline Rules", s["H_Sec"]),
        Paragraph("The hard_decline_flag is set to True — triggering immediate DECLINE — "
                  "in the following conditions:", s["Body"]),
        Paragraph("- Severity equals SEVERE: hard_decline_flag = True.", s["Li"]),
        Paragraph("- Bankruptcy filed within 24 months: hard_decline_flag = True.", s["Li"]),
        Paragraph("- Applicant is on RBI Wilful Defaulter list: hard_decline_flag = True.", s["Li"]),
        Paragraph("- Active insolvency proceedings under IBC Section 14: hard_decline_flag = True.", s["Li"]),
        Paragraph("- All other cases: hard_decline_flag = False.", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 3: Credit Utilisation Node ──────────────────────
    story += [
        chap("Section 3: Revolving Credit Utilisation Parameters", GREEN_D, s), sp(),
        node_tag("utilization_node", s), sp(),
        Paragraph(
            "This section defines revolving credit utilisation risk bands and adjustment "
            "factors that the utilization_node reads from the knowledge base. Retrieved when "
            "the node queries: <i>Revolving credit utilization ratio risk classification "
            "thresholds: EXCELLENT GOOD HIGH CRITICAL utilization percentage bands. "
            "Adjustment factor multiplier by utilization risk tier.</i>",
            s["Body"]
        ), sp(),

        Paragraph("3.1  Utilisation Risk Classification", s["H_Sec"]),
        Paragraph("Utilisation ratio = total revolving balance divided by total revolving "
                  "credit limit. Only accounts with revolvingOrInstallment = R are included.", s["Body"]),
        Paragraph("- EXCELLENT: utilisation ratio 0 to 20 percent. utilization_risk = EXCELLENT.", s["Li"]),
        Paragraph("- GOOD: utilisation ratio 21 to 40 percent. utilization_risk = GOOD.", s["Li"]),
        Paragraph("- HIGH: utilisation ratio 41 to 65 percent. utilization_risk = HIGH.", s["Li"]),
        Paragraph("- CRITICAL: utilisation ratio above 65 percent. utilization_risk = CRITICAL.", s["Li"]),
        sp(),

        Paragraph("3.2  Adjustment Factor by Utilisation Risk", s["H_Sec"]),
        Paragraph("The utilization_adjustment_factor multiplies the base lending limit:", s["Body"]),
        Paragraph("- EXCELLENT utilisation adjustment factor: 1.10  (10 percent bonus)", s["Li"]),
        Paragraph("- GOOD utilisation adjustment factor: 1.00  (no change)", s["Li"]),
        Paragraph("- HIGH utilisation adjustment factor: 0.85  (15 percent reduction)", s["Li"]),
        Paragraph("- CRITICAL utilisation adjustment factor: 0.70  (30 percent reduction)", s["Li"]),
        Paragraph("If total_credit_limit equals zero, set utilization_ratio to 0.0 and "
                  "utilization_risk to EXCELLENT.", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 4: Debt Exposure Node ───────────────────────────
    story += [
        chap("Section 4: Debt Exposure and Monthly Obligation Parameters", GREEN_D, s), sp(),
        node_tag("debt_exposure_node", s), sp(),
        Paragraph(
            "This section defines monthly debt obligation bands and exposure risk classification "
            "that the debt_exposure_node reads from the knowledge base. Retrieved when the "
            "node queries: <i>Monthly debt obligation thresholds for exposure risk "
            "classification: LOW MODERATE HIGH EXTREME monthly payment amount bands in INR. "
            "Total outstanding debt ceiling. Monthly EMI estimation rules for tradelines "
            "without payment data.</i>",
            s["Body"]
        ), sp(),

        Paragraph("4.1  Monthly Obligation Bands for Exposure Risk", s["H_Sec"]),
        Paragraph("Monthly obligation bands applied to monthly_obligation_estimate "
                  "(sum of monthlyPaymentAmount across all open tradelines):", s["Body"]),
        Paragraph("- LOW exposure: monthly obligations below INR 5000. exposure_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE exposure: monthly obligations INR 5000 to 15000. exposure_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH exposure: monthly obligations INR 15001 to 35000. exposure_risk = HIGH.", s["Li"]),
        Paragraph("- EXTREME exposure: monthly obligations above INR 35000. exposure_risk = EXTREME.", s["Li"]),
        sp(),

        Paragraph("4.2  Total Existing Debt Calculation", s["H_Sec"]),
        Paragraph("total_existing_debt = sum of balanceAmount across all open tradelines "
                  "(openOrClosed = O).", s["Body"]),
        sp(),

        Paragraph("4.3  EMI Estimation Rule for Missing Payment Data", s["H_Sec"]),
        Paragraph("If monthlyPaymentAmount is absent for an open tradeline, estimate EMI as: "
                  "balanceAmount divided by remaining_terms. If remaining terms are unknown, "
                  "use balanceAmount divided by 36.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 5: Payment Behaviour Node ───────────────────────
    story += [
        chap("Section 5: Payment Behaviour Scoring Parameters", GREEN_D, s), sp(),
        node_tag("payment_behavior_node", s), sp(),
        Paragraph(
            "This section defines delinquency count thresholds, charge-off detection rules, "
            "and behavior score values that the payment_behavior_node reads from the knowledge "
            "base. Retrieved when the node queries: <i>Delinquency count and DPD bucket "
            "thresholds for behavior risk classification: EXCELLENT FAIR POOR UNACCEPTABLE "
            "behavior score values. Charge-off identification rules. SMA-0 SMA-1 SMA-2 "
            "NPA classification. 30-DPD 60-DPD 90-DPD bucket counting.</i>",
            s["Body"]
        ), sp(),

        Paragraph("5.1  Delinquency Counting Rules", s["H_Sec"]),
        Paragraph("Total delinquencies = sum of delinquencies30Days + delinquencies60Days + "
                  "delinquencies90to180Days across all tradelines. Each field is a string "
                  "count (e.g., 00, 01, 03). This count of 30-DPD, 60-DPD and 90-DPD "
                  "buckets determines the behavior_risk classification.", s["Body"]),
        sp(),

        Paragraph("5.2  Charge-off Detection Rules", s["H_Sec"]),
        Paragraph("chargeoff_history = True if any tradeline meets one of these conditions:", s["Body"]),
        Paragraph("- derogCounter greater than 0", s["Li"]),
        Paragraph("- status code equals 97 or 93 (written-off)", s["Li"]),
        Paragraph("- dpdHistory contains any of: SUB, DBT, LSS, XXX", s["Li"]),
        Paragraph("chargeoff_history = False if none of the above conditions are met.", s["Li"]),
        sp(),

        Paragraph("5.3  Behavior Risk Classification and Behavior Score", s["H_Sec"]),
        Paragraph("Risk classification and behavior_score (0 to 100) determined as follows:", s["Body"]),
        Paragraph("- EXCELLENT: 0 delinquencies AND no charge-offs — "
                  "behavior_risk = EXCELLENT, behavior_score = 100", s["Li"]),
        Paragraph("- FAIR: 1 to 2 delinquencies AND no charge-offs — "
                  "behavior_risk = FAIR, behavior_score = 75", s["Li"]),
        Paragraph("- POOR: 3 or more delinquencies AND no charge-offs — "
                  "behavior_risk = POOR, behavior_score = 40", s["Li"]),
        Paragraph("- UNACCEPTABLE: ANY charge-offs present — "
                  "behavior_risk = UNACCEPTABLE, behavior_score = 0", s["Li"]),
        sp(),

        Paragraph("5.4  SMA and NPA Classification Reference", s["H_Sec"]),
        Paragraph("SMA-0 = overdue 1 to 30 days. SMA-1 = overdue 31 to 60 days. "
                  "SMA-2 = overdue 61 to 90 days. NPA = overdue more than 90 days. "
                  "These map to the DPD bucket counts used in delinquency counting.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 6: Inquiry Node ──────────────────────────────────
    story += [
        chap("Section 6: Credit Inquiry Velocity Parameters", GREEN_D, s), sp(),
        node_tag("inquiry_node", s), sp(),
        Paragraph(
            "This section defines inquiry count thresholds and penalty factors that "
            "the inquiry_node reads from the knowledge base. Retrieved when the node "
            "queries: <i>Credit inquiry count thresholds in last 12 months for velocity "
            "risk: LOW MODERATE HIGH inquiry-count bands. Inquiry penalty factor multiplier "
            "by velocity risk tier.</i>",
            s["Body"]
        ), sp(),

        Paragraph("6.1  Inquiry Counting Window", s["H_Sec"]),
        Paragraph("Count only hard inquiries with dates within the last 12 months from the "
                  "assessment date. Soft inquiries are excluded. inquiries_last_12m is the "
                  "result of this count.", s["Body"]),
        sp(),

        Paragraph("6.2  Velocity Risk Classification by Inquiry Count", s["H_Sec"]),
        Paragraph("velocity_risk is classified based on inquiries_last_12m as follows:", s["Body"]),
        Paragraph("- LOW velocity risk: 0 to 2 inquiries in last 12 months. velocity_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE velocity risk: 3 to 5 inquiries. velocity_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH velocity risk: 6 or more inquiries. velocity_risk = HIGH.", s["Li"]),
        sp(),

        Paragraph("6.3  Inquiry Penalty Factor", s["H_Sec"]),
        Paragraph("The inquiry_penalty_factor multiplies the lending limit. Applied "
                  "multiplicatively after public record and utilisation adjustment factors.", s["Body"]),
        Paragraph("- LOW velocity risk inquiry penalty factor: 1.00  (no reduction)", s["Li"]),
        Paragraph("- MODERATE velocity risk inquiry penalty factor: 0.95  (5 percent reduction)", s["Li"]),
        Paragraph("- HIGH velocity risk inquiry penalty factor: 0.85  (15 percent reduction)", s["Li"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 7: Income Analysis Node ─────────────────────────
    story += [
        chap("Section 7: Income Verification and DTI Policy Parameters", GREEN_D, s), sp(),
        node_tag("income_analysis_node", s), sp(),
        Paragraph(
            "This section defines DTI thresholds, FOIR limits, and missing-income handling "
            "rules that the income_analysis_node reads from the knowledge base. Retrieved "
            "when the node queries: <i>Debt to income DTI ratio thresholds for income risk "
            "classification: LOW MODERATE HIGH UNACCEPTABLE DTI percentage bands. "
            "Affordability cap, FOIR fixed-obligation-to-income ratio. Missing income "
            "handling rules and defaults.</i>",
            s["Body"]
        ), sp(),

        Paragraph("7.1  DTI Calculation Method", s["H_Sec"]),
        Paragraph("DTI formula: estimated_dti = monthly_obligations divided by monthly_income. "
                  "Monthly obligations = sum of monthlyPaymentAmount from all open tradelines "
                  "plus the proposed new EMI. Income source = bank_statement_summary "
                  "monthly_income field. FOIR (Fixed Obligation to Income Ratio) is equivalent "
                  "to DTI in this context.", s["Body"]),
        sp(),

        Paragraph("7.2  Missing Income Handling", s["H_Sec"]),
        Paragraph("If monthly_income is null, zero, or UNKNOWN:", s["Body"]),
        Paragraph("- income_missing_flag = True", s["Li"]),
        Paragraph("- estimated_dti = 99.9", s["Li"]),
        Paragraph("- income_risk = UNACCEPTABLE", s["Li"]),
        Paragraph("- affordability_flag = False", s["Li"]),
        sp(),

        Paragraph("7.3  DTI Risk Classification Bands", s["H_Sec"]),
        Paragraph("income_risk is classified based on estimated_dti as follows:", s["Body"]),
        Paragraph("- LOW income risk: DTI below 0.30  (obligations less than 30 percent of income). "
                  "income_risk = LOW.", s["Li"]),
        Paragraph("- MODERATE income risk: DTI 0.30 to 0.40. income_risk = MODERATE.", s["Li"]),
        Paragraph("- HIGH income risk: DTI 0.41 to 0.50. income_risk = HIGH.", s["Li"]),
        Paragraph("- UNACCEPTABLE income risk: DTI above 0.50. income_risk = UNACCEPTABLE.", s["Li"]),
        sp(),

        Paragraph("7.4  Affordability Cap — FOIR Limit", s["H_Sec"]),
        Paragraph("affordability_flag = True only if DTI is at or below 0.50. "
                  "This is the maximum FOIR permitted by this bank (50 percent of gross monthly income). "
                  "affordability_flag = False if DTI exceeds 0.50. A False affordability_flag "
                  "triggers immediate DECLINE in the decision node.", s["Body"]),
        sp(2),
        PageBreak(),
    ]

    # ── Section 8: Decision Node ─────────────────────────────────
    story += [
        chap("Section 8: Lending Decision and Interest Rate Parameters", GREEN_D, s), sp(),
        node_tag("decision_llm_node", s), sp(),
        Paragraph(
            "This section defines interest rates by risk tier, origination fee, and "
            "counter-offer affordability parameters used by the decision_llm_node and "
            "counter_offer_node.",
            s["Body"]
        ), sp(),

        Paragraph("8.1  Interest Rate Schedule by Risk Tier", s["H_Sec"]),
        Paragraph("Annual interest rate by aggregated risk tier:", s["Body"]),
        Paragraph("- Tier A (PRIME risk): interest_rate = 9.50 percent per annum", s["Li"]),
        Paragraph("- Tier B (NEAR_PRIME risk): interest_rate = 12.00 percent per annum", s["Li"]),
        Paragraph("- Tier C (FAIR risk): interest_rate = 15.50 percent per annum", s["Li"]),
        Paragraph("- Tier D (SUBPRIME risk): interest_rate = 20.00 percent per annum", s["Li"]),
        sp(),

        Paragraph("8.2  Origination Fee and Disbursement", s["H_Sec"]),
        Paragraph("- Origination fee: 2.5 percent of approved amount", s["Li"]),
        Paragraph("- disbursement_amount = approved_amount multiplied by 0.975  "
                  "(i.e., 100 percent minus 2.5 percent origination fee)", s["Li"]),
        sp(),

        Paragraph("8.3  Counter-Offer EMI Affordability Ceiling", s["H_Sec"]),
        Paragraph("max_affordable_emi = monthly_income multiplied by 0.40 "
                  "(40 percent of gross monthly income) minus existing monthly_obligations. "
                  "Counter-offer principal is back-calculated from this EMI ceiling at the "
                  "applicable interest rate and requested tenure.", s["Body"]),
        sp(2),
    ]

    doc.build(story)
    print(f"  Generated: {path}")


# ── entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    bank_dir = os.path.join(BASE, "bank_policies")
    rbi_dir  = os.path.join(BASE, "rbi_guidelines")
    os.makedirs(bank_dir, exist_ok=True)
    os.makedirs(rbi_dir,  exist_ok=True)

    bank_path        = os.path.join(bank_dir, "Bank_Lending_Policy.pdf")
    bank_sample_path = os.path.join(bank_dir, "Bank_Lending_Policy_Sample.pdf")
    rbi_path         = os.path.join(rbi_dir,  "RBI_Guidelines_Individual_Loans_India.pdf")

    print("Generating RAG source PDFs...")
    build_bank_policy(bank_path)
    build_bank_policy_sample(bank_sample_path)
    build_rbi_guidelines(rbi_path)
    print("Done.")
