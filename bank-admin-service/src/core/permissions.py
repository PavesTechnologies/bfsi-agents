from enum import Enum
from typing import Set


class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    CREDIT_MANAGER = "CREDIT_MANAGER"
    UNDERWRITER = "UNDERWRITER"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


class Permission(str, Enum):
    # Applications
    VIEW_APPLICATIONS = "view_applications"
    EXPORT_APPLICATIONS = "export_applications"

    # Rules
    VIEW_RULES = "view_rules"
    EDIT_LOW_RISK_RULES = "edit_low_risk_rules"
    EDIT_HIGH_RISK_RULES = "edit_high_risk_rules"
    APPROVE_RULE_CHANGES = "approve_rule_changes"

    # Documents
    VIEW_DOCUMENTS = "view_documents"
    UPLOAD_DOCUMENTS = "upload_documents"
    REPLACE_DOCUMENTS = "replace_documents"
    DELETE_DOCUMENTS = "delete_documents"

    # Users
    MANAGE_USERS = "manage_users"
    MANAGE_USER_RULES = "manage_user_rules"

    # Audit
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # Loan pipeline (HITL)
    APPROVE_LOAN = "approve_loan"


ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),  # all permissions
    Role.CREDIT_MANAGER: {
        Permission.VIEW_APPLICATIONS,
        Permission.VIEW_RULES,
        Permission.EDIT_LOW_RISK_RULES,
        Permission.VIEW_DOCUMENTS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.APPROVE_LOAN,
    },
    Role.UNDERWRITER: {
        Permission.VIEW_APPLICATIONS,
        Permission.VIEW_RULES,
        Permission.VIEW_DOCUMENTS,
        Permission.APPROVE_LOAN,
    },
    Role.COMPLIANCE_OFFICER: {
        Permission.VIEW_APPLICATIONS,
        Permission.VIEW_RULES,
        Permission.VIEW_DOCUMENTS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.REPLACE_DOCUMENTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_APPLICATIONS,
    },
    Role.AUDITOR: {
        Permission.VIEW_APPLICATIONS,
        Permission.VIEW_RULES,
        Permission.VIEW_DOCUMENTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.EXPORT_APPLICATIONS,
    },
    Role.VIEWER: {
        Permission.VIEW_APPLICATIONS,
        Permission.VIEW_RULES,
        Permission.VIEW_DOCUMENTS,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
