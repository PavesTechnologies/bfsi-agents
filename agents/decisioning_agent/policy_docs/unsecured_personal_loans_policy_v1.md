# Unsecured Personal Loans Policy

Policy ID: UPL_POLICY  
Version: v1  
Effective Date: 2026-04-01  
Product: UNSECURED_PERSONAL_LOAN

## 1 Document Metadata
This policy governs deterministic underwriting for unsecured personal loans. Policy citations in underwriting explanations must reference the section identifiers in this document.

## 2 Eligibility
Applicants must provide a valid bureau file and a complete application. Applications below the product minimum credit requirements may be declined or referred for manual review.

## 3 Credit History
### 3.1 Minimum Score
Applicants below the configured minimum credit score may fail policy eligibility.

### 3.2 File Depth
Applications with fewer than three tradelines or limited credit age may be considered thin-file or insufficient-credit-history cases and may require manual review or decline reason mapping.

## 4 Affordability
### 4.1 Income Verification
Income must be present and verifiable through the approved income source. Missing or unverifiable income requires manual review or adverse-action mapping if decline logic is final.

### 4.2 DTI Threshold
Applicants with debt-to-income ratios above 45% exceed the affordability threshold for standard approval.

## 5 Public Records
### 5.1 Bankruptcy Hard Decline
Recent bankruptcy within two years is a hard-decline condition unless an approved exception policy applies.

### 5.2 Severe Public Record History
Severe public-record history increases underwriting risk and may support decline or manual-review outcomes.

### 5.3 Utilization
High revolving utilization indicates elevated near-term repayment stress and may reduce lending capacity.

### 5.4 Exposure
High existing obligations indicate elevated exposure risk and may reduce lending capacity or support adverse-action mapping.

## 6 Behavior and Inquiry Guidance
### 6.1 Payment Behavior
Recent delinquencies, charge-offs, or poor payment behavior increase underwriting risk and may support adverse-action mapping.

### 6.2 Inquiry Velocity
Excessive recent credit inquiries indicate elevated credit-seeking behavior and may support adverse-action mapping.

## 7 Human Review Gates
### 7.1 Borderline Risk Bands
Borderline subprime outcomes may be referred to a human underwriter rather than automatically declined.

### 7.2 Unverifiable Income
Applications with unverifiable income should be referred to manual review when the rest of the file is otherwise potentially approvable.

### 7.3 Thin File
Thin-file scenarios may be referred to manual review when policy allows underwriter judgment.

## 8 Adverse Action Mapping
Adverse action notices must use approved reason codes and customer-safe language. Internal trigger logic must remain mapped to regulator-safe principal reason statements.

## 9 Exceptions
Any policy exception must be explicitly routed to human review and documented in the audit trail.
