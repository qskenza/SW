"""
Migration script to fix nurses that were incorrectly registered as doctors.
This script will:
1. Find all users with role='nurse' but who have a doctor profile
2. Move them from the doctors table to the nurses table
3. Update their display information
"""

from database import SessionLocal
from models import User, Doctor, Nurse

def fix_nurse_data():
    db = SessionLocal()

    try:
        # Find all users with role='nurse'
        nurses_users = db.query(User).filter(User.role == 'nurse').all()

        print(f"Found {len(nurses_users)} users with role='nurse'")

        for user in nurses_users:
            print(f"\nProcessing: {user.full_name} (ID: {user.id})")

            # Check if they have a doctor profile (incorrect)
            doctor_profile = db.query(Doctor).filter(Doctor.user_id == user.id).first()

            if doctor_profile:
                print(f"  ❌ Found incorrect doctor profile for nurse {user.full_name}")

                # Check if nurse profile already exists
                nurse_profile = db.query(Nurse).filter(Nurse.user_id == user.id).first()

                if not nurse_profile:
                    # Create nurse profile from doctor data
                    print(f"  ✅ Creating nurse profile...")

                    # Generate avatar initials
                    name_parts = user.full_name.split()
                    avatar = ''.join([n[0].upper() for n in name_parts[:2]]) if len(name_parts) >= 2 else user.full_name[:2].upper()

                    nurse_profile = Nurse(
                        user_id=user.id,
                        name=user.full_name,
                        license_number=doctor_profile.license_number,  # Transfer license
                        department=doctor_profile.specialty or "General",  # Use specialty as department
                        email=doctor_profile.email,
                        phone=doctor_profile.phone,
                        avatar=avatar,
                        shift=None,  # Can be updated later
                        is_available=True
                    )
                    db.add(nurse_profile)

                    # Delete doctor profile
                    print(f"  🗑️  Removing doctor profile...")
                    db.delete(doctor_profile)
                else:
                    print(f"  ✅ Nurse profile already exists")
                    # Just delete the doctor profile
                    print(f"  🗑️  Removing duplicate doctor profile...")
                    db.delete(doctor_profile)
            else:
                # Check if nurse profile exists
                nurse_profile = db.query(Nurse).filter(Nurse.user_id == user.id).first()
                if nurse_profile:
                    print(f"  ✅ Nurse profile already correct")
                else:
                    print(f"  ⚠️  No nurse profile found, creating one...")

                    # Generate avatar initials
                    name_parts = user.full_name.split()
                    avatar = ''.join([n[0].upper() for n in name_parts[:2]]) if len(name_parts) >= 2 else user.full_name[:2].upper()

                    nurse_profile = Nurse(
                        user_id=user.id,
                        name=user.full_name,
                        license_number=f"N{user.id}",  # Generate a license number
                        department="General",
                        email=user.email,
                        phone=user.phone,
                        avatar=avatar,
                        shift=None,
                        is_available=True
                    )
                    db.add(nurse_profile)

        # Commit all changes
        db.commit()
        print("\n✅ Migration completed successfully!")

        # Show summary
        total_nurses = db.query(Nurse).count()
        print(f"\nSummary:")
        print(f"  Total nurses in system: {total_nurses}")

        # List all nurses
        all_nurses = db.query(Nurse).all()
        for nurse in all_nurses:
            print(f"    - {nurse.name} (Dept: {nurse.department}, License: {nurse.license_number})")

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Nurse Data Migration Script")
    print("=" * 60)
    fix_nurse_data()
