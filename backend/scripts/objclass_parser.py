"""
OBJCLASS CSV Parser for Federal Budget Dashboard

This script parses OMB OBJCLASS CSV files and imports them into the normalized database.
It handles complex mapping between CSV data and our dimension tables.
"""

import pandas as pd
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pathlib import Path
import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal, engine
from app.models.dimensions import Agency, Bureau, Account, BudgetFunction, BudgetSubfunction, ObjectClass
from app.models.outlays import Outlay, ImportBatch, RawImportData, MappingLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OBJCLASSParser:
    """
    Parser for OMB OBJCLASS CSV files
    
    This parser handles the complex structure of OBJCLASS data:
    - Agency/Bureau/Account hierarchy
    - Function/Object Class categorization
    - Multi-year financial data (PY/CY/BY)
    - Strict mapping with confidence scoring
    """
    
    def __init__(self, csv_file_path: str, data_source: str = "OBJCLASS_2026"):
        self.csv_file_path = Path(csv_file_path)
        self.data_source = data_source
        self.session = SessionLocal()
        self.import_batch = None
        
        # Mapping cache (to avoid repeated DB queries)
        self.agency_cache: Dict[str, Agency] = {}
        self.bureau_cache: Dict[str, Bureau] = {}
        self.account_cache: Dict[str, Account] = {}
        self.function_cache: Dict[str, BudgetFunction] = {}
        self.subfunction_cache: Dict[str, BudgetSubfunction] = {}
        self.object_class_cache: Dict[str, ObjectClass] = {}
        
        # Import statistics
        self.stats = {
            'total_rows': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'warnings': 0,
            'mapping_misses': {
                'agencies': 0,
                'bureaus': 0,
                'accounts': 0,
                'functions': 0,
                'object_classes': 0
            }
        }
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        
    def validate_csv_structure(self, df: pd.DataFrame) -> bool:
        """
        Validate that the CSV has the expected OBJCLASS structure
        
        Expected columns:
        - OMB Agency Code, Agency Title
        - OMB Bureau Code, Bureau Title  
        - OMB Account, Account _Title
        - Default Budget Function, Default Budget Subfunction
        - OB Class Code, OB Class
        - PY Amount, CY Amount, BY Amount
        """
        required_columns = [
            'OMB Agency Code', 'Agency Title',
            'OMB Bureau Code', 'Bureau Title',
            'OMB Account', 'Account _Title',
            'Default Budget Function', 'Default Budget Subfunction',
            'OB Class Code', 'OB Class'
        ]
        
        # Check for amount columns (flexible naming)
        amount_columns = [col for col in df.columns if any(year in col for year in ['PY', 'CY', 'BY'])]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
            
        if not amount_columns:
            logger.error("No amount columns found (expecting PY, CY, BY columns)")
            return False
            
        logger.info(f"✅ CSV structure validated. Found {len(amount_columns)} amount columns")
        return True
        
    def create_import_batch(self, df: pd.DataFrame) -> ImportBatch:
        """Create a new import batch record"""
        file_hash = self._calculate_file_hash()
        
        batch = ImportBatch(
            source_file=str(self.csv_file_path),
            data_source=self.data_source,
            file_hash=file_hash,
            total_rows=len(df),
            successful_imports=0,
            failed_imports=0,
            warnings=0,
            status="processing"
        )
        
        self.session.add(batch)
        self.session.commit()
        
        logger.info(f"📦 Created import batch {batch.id} for {len(df)} rows")
        return batch
        
    def _calculate_file_hash(self) -> str:
        """Calculate SHA256 hash of the CSV file"""
        hasher = hashlib.sha256()
        with open(self.csv_file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def get_or_create_agency(self, code: str, title: str) -> Optional[Agency]:
        """Get or create an agency record"""
        # Check cache first
        if code in self.agency_cache:
            return self.agency_cache[code]
            
        # Check database
        agency = self.session.query(Agency).filter_by(omb_code=code).first()
        
        if not agency:
            # Create new agency
            agency = Agency(
                omb_code=code,
                title=title.strip(),
                abbreviation=self._extract_abbreviation(title)
            )
            self.session.add(agency)
            self.session.commit()
            logger.info(f"📊 Created new agency: {code} - {title}")
            
        # Add to cache
        self.agency_cache[code] = agency
        return agency
        
    def get_or_create_bureau(self, agency: Agency, code: str, title: str) -> Optional[Bureau]:
        """Get or create a bureau record"""
        cache_key = f"{agency.omb_code}:{code}"
        
        if cache_key in self.bureau_cache:
            return self.bureau_cache[cache_key]
            
        bureau = self.session.query(Bureau).filter_by(
            agency_id=agency.id,
            omb_code=code
        ).first()
        
        if not bureau:
            bureau = Bureau(
                agency_id=agency.id,
                omb_code=code,
                title=title.strip(),
                abbreviation=self._extract_abbreviation(title)
            )
            self.session.add(bureau)
            self.session.commit()
            logger.info(f"🏢 Created new bureau: {code} - {title}")
            
        self.bureau_cache[cache_key] = bureau
        return bureau
        
    def get_or_create_account(self, bureau: Bureau, code: str, title: str) -> Optional[Account]:
        """Get or create an account record"""
        cache_key = f"{bureau.omb_code}:{code}"
        
        if cache_key in self.account_cache:
            return self.account_cache[cache_key]
            
        account = self.session.query(Account).filter_by(
            bureau_id=bureau.id,
            omb_account_code=code
        ).first()
        
        if not account:
            account = Account(
                bureau_id=bureau.id,
                omb_account_code=code,
                title=title.strip(),
                description=title.strip()
            )
            self.session.add(account)
            self.session.commit()
            logger.info(f"💰 Created new account: {code} - {title[:50]}...")
            
        self.account_cache[cache_key] = account
        return account
        
    def get_or_create_function(self, code: str, title: str) -> Optional[BudgetFunction]:
        """Get or create a budget function record"""
        if code in self.function_cache:
            return self.function_cache[code]
            
        function = self.session.query(BudgetFunction).filter_by(code=code).first()
        
        if not function:
            function = BudgetFunction(
                code=code,
                title=title.strip(),
                description=title.strip()
            )
            self.session.add(function)
            self.session.commit()
            logger.info(f"🎯 Created new function: {code} - {title}")
            
        self.function_cache[code] = function
        return function
        
    def get_or_create_subfunction(self, function: BudgetFunction, code: str, title: str) -> Optional[BudgetSubfunction]:
        """Get or create a budget subfunction record"""
        cache_key = f"{function.code}:{code}"
        
        if cache_key in self.subfunction_cache:
            return self.subfunction_cache[cache_key]
        
        subfunction = self.session.query(BudgetSubfunction).filter_by(
            function_id=function.id,
            code=code
        ).first()
        
        if not subfunction:
            subfunction = BudgetSubfunction(
                function_id=function.id,
                code=code,
                title=title.strip(),
                description=title.strip()
            )
            self.session.add(subfunction)
            self.session.commit()
            logger.info(f"🎯 Created new subfunction: {code} - {title}")
            
        self.subfunction_cache[cache_key] = subfunction
        return subfunction
        
    def get_or_create_object_class(self, code: str, title: str) -> Optional[ObjectClass]:
        """Get or create an object class record"""
        if code in self.object_class_cache:
            return self.object_class_cache[code]
            
        obj_class = self.session.query(ObjectClass).filter_by(code=code).first()
        
        if not obj_class:
            # Extract group info from code (e.g., "25.1" -> group "25")
            group_code = code.split('.')[0] if '.' in code else code
            
            obj_class = ObjectClass(
                code=code,
                title=title.strip(),
                group_code=group_code,
                description=title.strip()
            )
            self.session.add(obj_class)
            self.session.commit()
            logger.info(f"📋 Created new object class: {code} - {title}")
            
        self.object_class_cache[code] = obj_class
        return obj_class
        
    def _extract_abbreviation(self, title: str) -> Optional[str]:
        """Extract abbreviation from title (e.g., "Department of Education (ED)" -> "ED")"""
        if '(' in title and ')' in title:
            start = title.rfind('(') + 1
            end = title.rfind(')')
            if start < end:
                return title[start:end].strip()
        return None
        
    def _parse_function_field(self, field_value: str) -> Tuple[str, str]:
        """
        Parse function field in "code - name" format
        
        Args:
            field_value: Field like "800 - General Government" or "801 - Legislative functions"
            
        Returns:
            Tuple of (code, name)
        """
        field_value = field_value.strip()
        
        # Handle "code - name" format
        if ' - ' in field_value:
            parts = field_value.split(' - ', 1)
            if len(parts) == 2:
                code = parts[0].strip()
                name = parts[1].strip()
                return code, name
        
        # Fallback: use entire field as both code and name
        return field_value, field_value
        
    def process_csv(self) -> bool:
        """
        Main processing function
        
        Returns:
            bool: True if processing was successful
        """
        try:
            logger.info(f"🏛️  Processing OBJCLASS CSV: {self.csv_file_path}")
            
            # Load CSV
            df = pd.read_csv(self.csv_file_path)
            logger.info(f"📄 Loaded {len(df)} rows from CSV")
            
            # Validate structure
            if not self.validate_csv_structure(df):
                return False
                
            # Create import batch
            self.import_batch = self.create_import_batch(df)
            
            # Process rows
            for idx, row in df.iterrows():
                try:
                    self._process_row(idx, row)
                except Exception as e:
                    logger.error(f"❌ Error processing row {idx}: {str(e)}")
                    self.stats['failed_imports'] += 1
                    
            # Finalize batch
            self._finalize_import_batch()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process CSV: {str(e)}")
            if self.import_batch:
                self.import_batch.status = "failed"
                self.import_batch.error_log = str(e)
                self.import_batch.end_time = datetime.utcnow()
                self.session.commit()
            return False
            
    def _process_row(self, idx: int, row: pd.Series) -> None:
        """Process a single CSV row"""
        # Create raw data record
        raw_data = RawImportData(
            import_batch_id=self.import_batch.id,
            row_number=idx + 1,
            raw_data=json.dumps(row.to_dict()),
            import_status="processing"
        )
        
        try:
            # Get/create dimension records
            agency = self.get_or_create_agency(
                str(row['OMB Agency Code']).strip(),
                str(row['Agency Title']).strip()
            )
            
            bureau = self.get_or_create_bureau(
                agency,
                str(row['OMB Bureau Code']).strip(),
                str(row['Bureau Title']).strip()
            )
            
            account = self.get_or_create_account(
                bureau,
                str(row['OMB Account']).strip(),
                str(row['Account _Title']).strip()
            )
            
            function_code, function_name = self._parse_function_field(str(row['Default Budget Function']))
            function = self.get_or_create_function(function_code, function_name)
            
            subfunction_code, subfunction_name = self._parse_function_field(str(row['Default Budget Subfunction']))
            subfunction = self.get_or_create_subfunction(function, subfunction_code, subfunction_name)
            
            object_class = self.get_or_create_object_class(
                str(row['OB Class Code']).strip(),
                str(row['OB Class']).strip()
            )
            
            # Process amount columns
            amount_columns = [col for col in row.index if any(year in col for year in ['PY', 'CY', 'BY'])]
            
            for amount_col in amount_columns:
                amount = self._parse_amount(row[amount_col])
                if amount is not None and amount != 0:
                    # Determine period from column name
                    period = self._extract_period(amount_col)
                    fiscal_year = self._extract_fiscal_year(amount_col)
                    
                    # Create outlay record
                    outlay = Outlay(
                        account_id=account.id,
                        function_id=function.id,
                        subfunction_id=subfunction.id,
                        object_class_id=object_class.id,
                        fiscal_year=fiscal_year,
                        period=period,
                        amount=amount,
                        data_source=self.data_source,
                        import_batch_id=self.import_batch.id,
                        confidence_score=1.0  # Exact match confidence
                    )
                    
                    self.session.add(outlay)
                    
            raw_data.import_status = "success"
            self.stats['successful_imports'] += 1
            
        except Exception as e:
            raw_data.import_status = "failed"
            raw_data.error_message = str(e)
            self.stats['failed_imports'] += 1
            logger.error(f"❌ Row {idx + 1} failed: {str(e)}")
            
        finally:
            self.session.add(raw_data)
            
            # Commit every 100 rows
            if idx % 100 == 0:
                self.session.commit()
                logger.info(f"📊 Processed {idx + 1} rows...")
                
    def _parse_amount(self, value: Any) -> Optional[int]:
        """Parse amount value (handle various formats)"""
        if pd.isna(value):
            return None
            
        # Convert to string and clean
        str_value = str(value).replace(',', '').replace('$', '').strip()
        
        try:
            # Convert to float first, then to int (thousands)
            return int(float(str_value) * 1000) if str_value else None
        except (ValueError, TypeError):
            return None
            
    def _extract_period(self, column_name: str) -> str:
        """Extract period from column name (PY/CY/BY)"""
        if 'PY' in column_name:
            return 'PY'
        elif 'CY' in column_name:
            return 'CY'
        elif 'BY' in column_name:
            return 'BY'
        else:
            return 'CY'  # Default
            
    def _extract_fiscal_year(self, column_name: str) -> int:
        """Extract fiscal year from column name or use default"""
        # Try to extract year from column name
        import re
        year_match = re.search(r'20\d{2}', column_name)
        if year_match:
            return int(year_match.group())
        
        # Default to 2026 for now
        return 2026
        
    def _finalize_import_batch(self) -> None:
        """Finalize the import batch with statistics"""
        self.session.commit()
        
        self.import_batch.successful_imports = self.stats['successful_imports']
        self.import_batch.failed_imports = self.stats['failed_imports']
        self.import_batch.warnings = self.stats['warnings']
        self.import_batch.status = "completed"
        self.import_batch.end_time = datetime.utcnow()
        
        self.session.commit()
        
        logger.info(f"✅ Import completed!")
        logger.info(f"   Total rows: {self.stats['total_rows']}")
        logger.info(f"   Successful: {self.stats['successful_imports']}")
        logger.info(f"   Failed: {self.stats['failed_imports']}")
        logger.info(f"   Warnings: {self.stats['warnings']}")

def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse OBJCLASS CSV files')
    parser.add_argument('csv_file', help='Path to OBJCLASS CSV file')
    parser.add_argument('--data-source', default='OBJCLASS_2026', help='Data source identifier')
    
    args = parser.parse_args()
    
    with OBJCLASSParser(args.csv_file, args.data_source) as parser:
        success = parser.process_csv()
        
    if success:
        logger.info("🎉 OBJCLASS import completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ OBJCLASS import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 