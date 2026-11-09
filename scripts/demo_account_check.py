"""
SIGNHEAR Demo Account Verification & Emergency Unlock Utility
Run this script anytime before or during a demo:
    python scripts/demo_account_check.py
"""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from models.accounts import Accounts
from utils.enum import RoleEnum, AccountStatusEnum, VerificationStatus


def verify_and_unlock_demo_accounts():
    db = SessionLocal()
    try:
        print("=" * 70)
        print(" SIGNHEAR: Pre-Demo Account Status Verification & Unlocking")
        print("=" * 70)

        accounts = db.query(Accounts).all()
        unlocked_count = 0

        # Known critical demo accounts
        critical_demo_emails = {
            "adminteacher09@gmail.com": RoleEnum.admin,
            "denmhardimaculangan12@gmail.com": RoleEnum.teacher,
            "bugarinrymuel@gmail.com": RoleEnum.teacher,
            "0323-3664@lspu.edu.ph": RoleEnum.teacher,
        }

        print("\n[1] Checking Demo Staff & Administrator Accounts:")
        print("-" * 70)
        for email, expected_role in critical_demo_emails.items():
            acc = db.query(Accounts).filter(Accounts.email == email).first()
            if acc:
                changed = False
                if acc.account_status != AccountStatusEnum.active:
                    acc.account_status = AccountStatusEnum.active
                    changed = True
                if acc.verification_status != VerificationStatus.verified:
                    acc.verification_status = VerificationStatus.verified
                    changed = True

                if changed:
                    unlocked_count += 1
                    status_str = "FIXED (Unlocked/Verified)"
                else:
                    status_str = "READY (Active & Verified)"

                print(f"  * [{acc.role.value.upper():7}] {acc.email:<35} -> {status_str}")
            else:
                print(f"  ! [{expected_role.value.upper():7}] {email:<35} -> NOT FOUND IN DB")

        print("\n[2] Checking Active Student Accounts:")
        print("-" * 70)
        students = db.query(Accounts).filter(Accounts.role == RoleEnum.student).limit(6).all()
        for st in students:
            changed = False
            if st.account_status != AccountStatusEnum.active:
                st.account_status = AccountStatusEnum.active
                changed = True
            if st.verification_status != VerificationStatus.verified:
                st.verification_status = VerificationStatus.verified
                changed = True
            if changed:
                unlocked_count += 1

            print(f"  * [STUDENT] Username: {st.username:<25} -> READY (Active)")

        if unlocked_count > 0:
            db.commit()
            print(f"\n[OK] Successfully unlocked {unlocked_count} account(s) for demo!")
        else:
            print("\n[OK] All demo accounts are active, verified, and unlocked.")

        print("\n[3] Demo Portal Access Reference:")
        print("-" * 70)
        print("  * Administrator Portal : http://localhost:5173/admin/login")
        print("    Email                : adminteacher09@gmail.com")
        print("  * Science Teacher Portal: http://localhost:5173/login (Click 'Teacher')")
        print("    Email                : denmhardimaculangan12@gmail.com or bugarinrymuel@gmail.com")
        print("  * Grade 4 Student Portal: http://localhost:5173/login (Click 'Student')")
        print("    Username             : darrty123 or denpogi")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    verify_and_unlock_demo_accounts()
