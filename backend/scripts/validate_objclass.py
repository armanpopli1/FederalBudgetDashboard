#!/usr/bin/env python3
"""
OBJCLASS CSV Validation Script

This script validates the structure and content of OBJCLASS CSV files
before importing them into the database.
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

def validate_csv_structure(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validate the CSV file structure
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Load CSV
        df = pd.read_csv(file_path)
        print(f"📄 Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Check for required columns (actual OBJCLASS column names)
        required_columns = [
            'OMB Agency Code', 'Agency Title',
            'OMB Bureau Code', 'Bureau Title',  
            'OMB Account', 'Account _Title',
            'Default Budget Function', 'Default Budget Subfunction',
            'OB Class Code', 'OB Class'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check for amount columns
        amount_columns = [col for col in df.columns if any(year in col for year in ['PY', 'CY', 'BY'])]
        if not amount_columns:
            issues.append("No amount columns found (expected PY, CY, BY columns)")
        else:
            print(f"✅ Found {len(amount_columns)} amount columns: {amount_columns}")
        
        # Check for empty required columns
        for col in required_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum()
                if empty_count > 0:
                    issues.append(f"Column '{col}' has {empty_count} empty values")
        
        # Check data types and formats
        for col in ['OMB Agency Code', 'OMB Bureau Code', 'Default Budget Function', 'OB Class Code']:
            if col in df.columns:
                # Check if codes are reasonable (not too long, not empty)
                max_len = df[col].astype(str).str.len().max()
                if max_len > 20:
                    issues.append(f"Column '{col}' has very long codes (max {max_len} characters)")
        
        # Sample data analysis
        print("\n📊 Sample Data Analysis:")
        print(f"   Unique agencies: {df['OMB Agency Code'].nunique() if 'OMB Agency Code' in df.columns else 'N/A'}")
        print(f"   Unique bureaus: {df['OMB Bureau Code'].nunique() if 'OMB Bureau Code' in df.columns else 'N/A'}")
        print(f"   Unique accounts: {df['OMB Account'].nunique() if 'OMB Account' in df.columns else 'N/A'}")
        print(f"   Unique functions: {df['Default Budget Function'].nunique() if 'Default Budget Function' in df.columns else 'N/A'}")
        print(f"   Unique object classes: {df['OB Class Code'].nunique() if 'OB Class Code' in df.columns else 'N/A'}")
        
        # Check amount columns for valid data
        for col in amount_columns:
            non_zero_count = (df[col] != 0).sum()
            print(f"   {col}: {non_zero_count} non-zero values")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        issues.append(f"Failed to load CSV: {str(e)}")
        return False, issues

def show_sample_data(file_path: str, num_rows: int = 5) -> None:
    """Show sample data from the CSV"""
    try:
        df = pd.read_csv(file_path)
        print(f"\n📋 Sample Data (first {num_rows} rows):")
        print("=" * 80)
        
        # Show key columns (actual OBJCLASS column names)
        key_columns = [
            'OMB Agency Code', 'Agency Title',
            'OMB Bureau Code', 'Bureau Title',
            'OMB Account', 'Account _Title',
            'Default Budget Function', 'Default Budget Subfunction',
            'OB Class Code', 'OB Class'
        ]
        
        available_columns = [col for col in key_columns if col in df.columns]
        
        if available_columns:
            sample_df = df[available_columns].head(num_rows)
            print(sample_df.to_string(index=False))
        
        # Show amount columns separately
        amount_columns = [col for col in df.columns if any(year in col for year in ['PY', 'CY', 'BY'])]
        if amount_columns:
            print(f"\n💰 Amount Columns (first {num_rows} rows):")
            print("=" * 80)
            amount_df = df[amount_columns].head(num_rows)
            print(amount_df.to_string(index=False))
        
    except Exception as e:
        print(f"❌ Error showing sample data: {str(e)}")

def analyze_data_quality(file_path: str) -> Dict[str, Any]:
    """Analyze data quality metrics"""
    try:
        df = pd.read_csv(file_path)
        
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'duplicates': df.duplicated().sum(),
            'empty_rows': df.isnull().all(axis=1).sum(),
        }
        
        # Column-specific analysis
        column_analysis = {}
        for col in df.columns:
            column_analysis[col] = {
                'null_count': df[col].isnull().sum(),
                'unique_values': df[col].nunique(),
                'data_type': str(df[col].dtype)
            }
        
        analysis['columns'] = column_analysis
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}

def main():
    """Main validation function"""
    if len(sys.argv) != 2:
        print("Usage: python validate_objclass.py <csv_file_path>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    print("🏛️  OBJCLASS CSV Validation")
    print("=" * 50)
    print(f"📄 Validating file: {csv_file}")
    
    # Validate structure
    is_valid, issues = validate_csv_structure(csv_file)
    
    if issues:
        print("\n❌ Validation Issues Found:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if is_valid:
        print("\n✅ CSV structure validation passed!")
        
        # Show sample data
        show_sample_data(csv_file)
        
        # Analyze data quality
        print("\n📊 Data Quality Analysis:")
        print("=" * 50)
        analysis = analyze_data_quality(csv_file)
        
        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
        else:
            print(f"Total rows: {analysis['total_rows']:,}")
            print(f"Total columns: {analysis['total_columns']}")
            print(f"Memory usage: {analysis['memory_usage']:,} bytes")
            print(f"Duplicate rows: {analysis['duplicates']}")
            print(f"Empty rows: {analysis['empty_rows']}")
            
            # Show columns with issues
            problematic_columns = []
            for col, stats in analysis['columns'].items():
                if stats['null_count'] > 0:
                    problematic_columns.append(f"{col}: {stats['null_count']} nulls")
            
            if problematic_columns:
                print("\n⚠️  Columns with missing data:")
                for col_info in problematic_columns:
                    print(f"   {col_info}")
        
        print("\n🎉 File is ready for import!")
        print(f"   Next step: python scripts/objclass_parser.py {csv_file}")
        
    else:
        print("\n❌ CSV validation failed!")
        print("   Please fix the issues above before importing.")
        sys.exit(1)

if __name__ == "__main__":
    main() 