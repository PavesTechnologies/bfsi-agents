COUNTER_OFFER_PROMPT = """
You are writing plain-language justifications for a bank loan restructuring engine.

All financial figures have already been computed by the underwriting system and are
provided below. Your ONLY job is to write the six text fields listed in the task
section. Do NOT recompute, restate differently, or invent any numbers.

---------------------------------------
APPLICANT FINANCIAL PROFILE
---------------------------------------

Monthly Income:                {monthly_income}
Existing Monthly Obligations:  {existing_monthly_obligations}
Maximum Affordable EMI:        {max_affordable_emi}
Estimated DTI:                 {estimated_dti}
Risk Tier:                     {risk_tier}
Credit Score Band:             {score_band}
Qualifying Cap:                {qualifying_cap}
Requested Amount:              {requested_amount}
Requested Tenure (months):     {requested_tenure}

Analyzers that ran:     {analyzers_ran}
Analyzers that skipped: {analyzers_skipped}

IMPORTANT: Do NOT cite any skipped analyzer in your justification text.
Only reference data from analyzers that ran.

---------------------------------------
PRE-COMPUTED COUNTER OFFERS
---------------------------------------

CO1 — Reduced Amount, Same Tenure
  Amount:           {co1_amount}
  Tenure:           {co1_tenure} months
  Interest Rate:    {co1_rate}%
  Monthly EMI:      {co1_emi}
  Disbursement:     {co1_disbursement}
  Total Repaid:     {co1_total}
  Headroom:         {co1_headroom_pct}% below affordability ceiling

CO2 — Full Requested Amount, Extended Tenure
  Feasible:         {co2_feasible}
  Amount:           {co2_amount}
  Tenure:           {co2_tenure} months  (minimum tenure computed from applicant income)
  Interest Rate:    {co2_rate}%
  Monthly EMI:      {co2_emi}
  Disbursement:     {co2_disbursement}
  Total Repaid:     {co2_total}
  Headroom:         {co2_headroom_pct}%

CO3 — Balanced Option (Partial Reduction + Partial Extension)
  Amount:           {co3_amount}
  Tenure:           {co3_tenure} months
  Interest Rate:    {co3_rate}%
  Monthly EMI:      {co3_emi}
  Disbursement:     {co3_disbursement}
  Total Repaid:     {co3_total}
  Headroom:         {co3_headroom_pct}%

Recommended option:            {recommended_option_id}
System recommendation reason:  {recommendation_reason}

---------------------------------------
YOUR TASK — WRITE THESE SIX FIELDS ONLY
---------------------------------------

1. counter_offer_logic
   2-3 sentences. Why was the original loan request not approved?
   Reference the applicant's qualifying cap, DTI, and income in plain language.
   No jargon. Avoid "algorithm", "model", "system".

2. co1_justification
   2 sentences. Why is CO1 — the reduced amount at the original tenure —
   appropriate for this applicant's financial profile?

3. co2_justification
   2 sentences. Why does CO2's extended tenure make the full requested amount
   affordable for this applicant?
   If co2_feasible is false, explain in plain language why the full requested
   amount cannot be supported even at the maximum allowed repayment period.

4. co3_justification
   2 sentences. Why does CO3's combination of partial amount reduction and
   moderate tenure extension serve this applicant better than the two extremes?

5. recommendation_rationale
   1 sentence. Why is {recommended_option_id} the best fit for this profile?

6. confidence_score
   A decimal between 0.0 and 1.0 reflecting how clearly the financial data
   supports these restructured offers.

{format_instructions}
"""
