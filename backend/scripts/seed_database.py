"""
Database seeding script for Federal Budget Dashboard

This script populates the database with:
1. Sample federal budget data (based on realistic FY 2024 figures)
2. Sample "Big Beautiful Bill" changes
3. Bill metadata

Uses SQLite for Phase 1 - simple, fast, and cost-effective!
"""
 
import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import BudgetData, Bill, BBBChange, Base

def get_database_url():
    """Get database URL - defaults to SQLite for Phase 1"""
    
    # Check for custom DATABASE_URL (for testing different databases)
    if database_url := os.getenv("DATABASE_URL"):
        return database_url
    
    # Default: SQLite database file in backend directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "..", "federal_budget.db")
    db_path = os.path.abspath(db_path)
    
    print(f"Using SQLite database: {db_path}")
    return f"sqlite:///{db_path}"

def create_tables(engine):
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("✅ Tables created successfully")

def seed_budget_data(session):
    """Seed sample federal budget data for FY 2024"""
    print("Seeding budget data...")
    
    # Sample federal budget data (simplified, based on FY 2024 estimates)
    budget_data = [
        # Major mandatory spending
        {"category": "Social Security", "subcategory": "OASDI", "agency": "SSA", 
         "amount": 1350000000000, "function_code": "651", "function_title": "Social Security"},
        
        {"category": "Medicare", "subcategory": "Part A", "agency": "HHS", 
         "amount": 450000000000, "function_code": "571", "function_title": "Medicare"},
        {"category": "Medicare", "subcategory": "Part B", "agency": "HHS", 
         "amount": 350000000000, "function_code": "571", "function_title": "Medicare"},
        {"category": "Medicare", "subcategory": "Part D", "agency": "HHS", 
         "amount": 120000000000, "function_code": "571", "function_title": "Medicare"},
        
        {"category": "Medicaid", "subcategory": "Federal Share", "agency": "HHS", 
         "amount": 680000000000, "function_code": "551", "function_title": "Health Care Services"},
        
        # Major discretionary spending
        {"category": "Defense", "subcategory": "DoD Operations", "agency": "DoD", 
         "amount": 600000000000, "function_code": "051", "function_title": "National Defense"},
        {"category": "Defense", "subcategory": "Military Personnel", "agency": "DoD", 
         "amount": 180000000000, "function_code": "051", "function_title": "National Defense"},
        {"category": "Defense", "subcategory": "R&D", "agency": "DoD", 
         "amount": 140000000000, "function_code": "051", "function_title": "National Defense"},
        
        {"category": "Education", "subcategory": "Title I", "agency": "Education", 
         "amount": 18000000000, "function_code": "501", "function_title": "Education, Training, Employment"},
        {"category": "Education", "subcategory": "Special Education", "agency": "Education", 
         "amount": 15000000000, "function_code": "501", "function_title": "Education, Training, Employment"},
        {"category": "Education", "subcategory": "Pell Grants", "agency": "Education", 
         "amount": 28000000000, "function_code": "501", "function_title": "Education, Training, Employment"},
        
        {"category": "Veterans Affairs", "subcategory": "Disability Compensation", "agency": "VA", 
         "amount": 140000000000, "function_code": "701", "function_title": "Veterans Benefits and Services"},
        {"category": "Veterans Affairs", "subcategory": "Healthcare", "agency": "VA", 
         "amount": 120000000000, "function_code": "701", "function_title": "Veterans Benefits and Services"},
        
        {"category": "Transportation", "subcategory": "Highways", "agency": "Transportation", 
         "amount": 50000000000, "function_code": "401", "function_title": "Transportation"},
        {"category": "Transportation", "subcategory": "Aviation", "agency": "Transportation", 
         "amount": 18000000000, "function_code": "401", "function_title": "Transportation"},
        
        {"category": "Health and Human Services", "subcategory": "NIH", "agency": "HHS", 
         "amount": 47000000000, "function_code": "552", "function_title": "Health Research and Training"},
        {"category": "Health and Human Services", "subcategory": "CDC", "agency": "HHS", 
         "amount": 8000000000, "function_code": "551", "function_title": "Health Care Services"},
        
        {"category": "Homeland Security", "subcategory": "Border Security", "agency": "DHS", 
         "amount": 15000000000, "function_code": "054", "function_title": "National Defense"},
        {"category": "Homeland Security", "subcategory": "TSA", "agency": "DHS", 
         "amount": 8000000000, "function_code": "054", "function_title": "National Defense"},
        
        {"category": "Justice", "subcategory": "FBI", "agency": "DOJ", 
         "amount": 10000000000, "function_code": "754", "function_title": "Administration of Justice"},
        {"category": "Justice", "subcategory": "Prisons", "agency": "DOJ", 
         "amount": 8000000000, "function_code": "754", "function_title": "Administration of Justice"},
        
        {"category": "Interest on Debt", "subcategory": "Public Debt", "agency": "Treasury", 
         "amount": 640000000000, "function_code": "901", "function_title": "Net Interest"},
    ]
    
    fiscal_year = 2024
    
    for item in budget_data:
        budget_item = BudgetData(
            category=item["category"],
            subcategory=item["subcategory"],
            agency=item["agency"],
            amount=item["amount"],
            fiscal_year=fiscal_year,
            data_type="outlays",
            function_code=item["function_code"],
            function_title=item["function_title"]
        )
        session.add(budget_item)
    
    print(f"✅ Added {len(budget_data)} budget items for FY {fiscal_year}")

def seed_bbb_data(session):
    """Seed Big Beautiful Bill metadata and changes"""
    print("Seeding Big Beautiful Bill data...")
    
    # Create the bill record
    bbb_bill = Bill(
        bill_id="bbb",
        title="Big Beautiful Bill - Federal Budget Reform Act of 2024",
        sponsor="Rep. Jane Doe (D-CA)",
        purpose="Comprehensive federal budget reform focusing on education, infrastructure, and deficit reduction",
        date_introduced=datetime(2024, 1, 15),
        status="Introduced in House",
        full_text_url="https://www.congress.gov/bill/118th-congress/house-bill/1234"
    )
    session.add(bbb_bill)
    session.commit()  # Commit to get the bill ID
    
    # Sample BBB changes (in dollars)
    bbb_changes = [
        # Education increases
        {"category": "Education", "change_amount": 25000000000, 
         "description": "Increase funding for Title I schools and teacher training programs"},
        
        # Defense reductions
        {"category": "Defense", "change_amount": -50000000000, 
         "description": "Reduce overseas operations and legacy weapons programs"},
        
        # Infrastructure increases
        {"category": "Transportation", "change_amount": 30000000000, 
         "description": "Invest in high-speed rail, bridge repair, and electric vehicle charging"},
        
        # Healthcare increases
        {"category": "Health and Human Services", "change_amount": 15000000000, 
         "description": "Expand community health centers and mental health programs"},
        
        # Veterans slight increase
        {"category": "Veterans Affairs", "change_amount": 5000000000, 
         "description": "Improve VA facilities and expand veteran job training"},
        
        # Justice reform
        {"category": "Justice", "change_amount": -2000000000, 
         "description": "Reduce federal prison population through sentencing reform"},
        
        # Homeland Security efficiency
        {"category": "Homeland Security", "change_amount": -3000000000, 
         "description": "Streamline overlapping security programs"},
    ]
    
    for change in bbb_changes:
        bbb_change = BBBChange(
            bill_id=bbb_bill.id,
            category=change["category"],
            change_amount=change["change_amount"],
            change_type="spending",
            description=change["description"]
        )
        session.add(bbb_change)
    
    print(f"✅ Added BBB bill with {len(bbb_changes)} proposed changes")

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("=" * 50)
    
    # Get database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # Create tables
    create_tables(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if data already exists
        existing_budget = session.query(BudgetData).first()
        existing_bill = session.query(Bill).first()
        
        if existing_budget or existing_bill:
            print("⚠️  Data already exists in database")
            response = input("Do you want to continue and add more data? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        # Seed the data
        seed_budget_data(session)
        seed_bbb_data(session)
        
        # Commit all changes
        session.commit()
        print("=" * 50)
        print("✅ Database seeding completed successfully!")
        
        # Show summary
        budget_count = session.query(BudgetData).count()
        bill_count = session.query(Bill).count()
        change_count = session.query(BBBChange).count()
        
        print(f"📊 Summary:")
        print(f"   - Budget items: {budget_count}")
        print(f"   - Bills: {bill_count}")
        print(f"   - Bill changes: {change_count}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main() 