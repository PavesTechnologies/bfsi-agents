KYC Agent — Front-End Design & Implementation Guidelines
1. Purpose of This Document

This document defines:

UX principles for KYC flows

Security and compliance UI requirements

Input validation standards

Document capture requirements

Liveness interaction guidelines

Reviewer UI standards

Accessibility requirements

Error and escalation UX

The KYC front-end must be:

Secure

Trust-building

Friction-aware

Regulator-safe

Bias-neutral

Fully auditable

2. UX Philosophy for KYC

KYC is a compliance-critical identity verification step.

The UI must:

Build user trust

Clearly explain why information is needed

Minimize friction

Prevent input errors

Avoid legal misrepresentation

Avoid discriminatory patterns

Tone must be:

Professional

Clear

Non-accusatory

Legally accurate

3. KYC Applicant Flow Overview
Start KYC
   ↓
Enter Identity Details
   ↓
Upload Government ID
   ↓
Take Selfie / Liveness Check
   ↓
Processing Screen
   ↓
Result Screen (Pass / Review / Fail)

4. Identity Information Collection Guidelines
4.1 Required Fields

Full Legal Name

Date of Birth

SSN (masked input)

Address

Phone

Email

4.2 Input Design Standards
SSN Field

Mask first 5 digits

Display last 4 digits after entry

Real-time format validation

No autocomplete allowed

Example display:

***-**-1234

DOB Field

Use date picker

Prevent future dates

Validate logical age (e.g., 18+ if required)

Address Field

Use address auto-complete

Normalize to USPS format

Allow manual override

5. Government ID Upload Guidelines
5.1 Accepted Documents

Driver’s License

Passport

State ID

UI must clearly show accepted document types.

5.2 Capture Options

Mobile camera capture

Desktop upload

Drag & drop

5.3 Image Requirements (Displayed to User)

Clear lighting

No glare

Entire document visible

No cropping

No screenshots

Provide visual examples.

5.4 Real-Time Validation

Front-end should check:

File size limit

Supported format (JPG, PNG, PDF)

Basic blur detection (if possible)

Orientation correction preview

6. Selfie & Liveness Capture Guidelines
6.1 UX Requirements

Before starting liveness:

Display explanation:

"We use facial verification to confirm your identity. This prevents fraud and protects your account."

6.2 Liveness Interaction Types
Passive Liveness

User looks at camera

Minimal instruction

Active Liveness

Blink

Turn head

Follow dot

Instructions must be:

Short

Clear

Non-technical

6.3 Accessibility Considerations

Provide alternative verification path if:

User has visual impairment

User cannot perform motion challenge

Camera unavailable

Alternative path:

→ Manual document review

7. Processing Screen Guidelines

While KYC runs:

Show secure processing animation

Display progress indicator

Avoid revealing internal checks

Display reassurance message

Example:

"We're securely verifying your identity. This usually takes a few seconds."

No technical details shown.

8. Result Screen Guidelines
8.1 PASS State

Display:

Confirmation message

Next step instruction

Example:

"Your identity has been successfully verified."

Do not show internal scores.

8.2 REVIEW State

Display:

Neutral message

Avoid implying wrongdoing

Example:

"We need a little more time to verify your information. Our team is reviewing your details."

Do not mention fraud suspicion.

8.3 FAIL State

If regulatory block (e.g., OFAC):

Do NOT display:

“Sanctions”

“Blacklist”

Internal flags

Display generic message:

"We are unable to proceed with your application at this time. If you believe this is an error, please contact support."

Must trigger support workflow.

9. Error Handling Guidelines
9.1 User Errors

Examples:

Invalid SSN format

Blurry image

Face not detected

Display:

Clear corrective guidance

No technical jargon

9.2 System Errors

If vendor timeout:

"We're experiencing a temporary issue verifying your identity. Please try again shortly."

Do not expose vendor name.

10. Security & Privacy UI Requirements
10.1 Privacy Disclosure

Before KYC starts:

Display consent checkbox

Link to privacy policy

Explain data retention

Must include:

Biometric usage disclosure

Data storage explanation

Third-party processing disclosure

10.2 Session Controls

Auto-timeout after inactivity

Disable back navigation during submission

Prevent multiple parallel submissions

10.3 Front-End Data Handling

Do not store SSN in local storage

Clear form state on logout

Use secure cookies

Prevent screenshot if feasible (optional)

11. Reviewer (Internal) UI Guidelines
11.1 Reviewer Dashboard Requirements

Must display:

Applicant name

KYC status

Trigger reason

Confidence indicators

Flags

Evidence links

11.2 Evidence Display

Reviewer must be able to:

View ID image

View selfie

View vendor results

See rule triggers

Compare face match score

All views must:

Be watermarked

Log access event

Require authentication

11.3 Reviewer Actions

Buttons:

Approve

Reject

Request Re-upload

Each action must require:

Comment entry

Confirmation dialog

12. Accessibility Standards

Must comply with:

WCAG 2.1 AA minimum

Include:

Screen reader support

High contrast mode

Keyboard navigation

Captions for video instructions

13. Mobile Optimization

KYC is primarily mobile-heavy.

Must:

Use camera-first flow

Auto-switch to rear camera for ID

Auto-switch to front camera for selfie

Support portrait mode

14. Performance Requirements
Interaction	Target
Form validation	< 100 ms
Image preview	< 500 ms
Liveness initialization	< 2 sec
Processing screen	Real-time updates
15. Anti-Fraud UI Controls

Optional enhancements:

Detect multiple failed attempts

Limit retry count

Rate limit submissions

Block copy-paste for SSN

16. Internationalization (Future Phase)

UI must support:

Configurable language packs

Date format localization

Address format variations

17. UX Anti-Patterns to Avoid

Do NOT:

Show internal fraud flags

Display confidence scores

Show “you failed AML”

Blame user for compliance restrictions

Overload screen with legal text

18. Audit & Event Tracking

Front-end must emit events:

KYC started

Document uploaded

Liveness initiated

Liveness completed

Submission timestamp

Result displayed

All events must include:

Session ID

Timestamp

Device metadata

19. Shadow Mode UI (Pre-Production)

In shadow mode:

Show PASS result

But do not block underwriting

Log comparison metrics internally

User experience must remain identical.

20. UI Versioning & Compliance

Every UI release must:

Tag KYC flow version

Track consent language version

Log biometric disclosure version

Maintain change history

Conclusion

The KYC front-end must ensure:

Trust-building user experience

Compliance-safe messaging

Secure data handling

Clear escalation paths

Accessibility compliance

Human review support

Fraud-resistant interaction patterns

It must balance:

Regulatory rigor

Security

Low friction

User confidence