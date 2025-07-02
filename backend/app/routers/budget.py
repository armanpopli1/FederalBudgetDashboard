from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models.budget import BudgetData

router = APIRouter()

@router.get("/budget")
async def get_budget(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year (defaults to latest)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    data_type: Optional[str] = Query("outlays", description="outlays or budget_authority"),
    db: Session = Depends(get_db)
):
    """
    Get federal budget data with optional filtering
    
    Returns budget data aggregated by category, with optional filters for:
    - fiscal_year: Specific fiscal year (defaults to latest available)
    - category: Specific budget category
    - data_type: outlays (default) or budget_authority
    """
    
    try:
        query = db.query(BudgetData)
        
        # Filter by data type
        query = query.filter(BudgetData.data_type == data_type)
        
        # If no fiscal year specified, get the latest one
        if fiscal_year is None:
            latest_year_query = db.query(func.max(BudgetData.fiscal_year))
            latest_year = latest_year_query.scalar()
            if latest_year:
                fiscal_year = latest_year
            else:
                # Return empty if no data
                return {"fiscal_year": None, "total_amount": 0, "categories": []}
        
        query = query.filter(BudgetData.fiscal_year == fiscal_year)
        
        # Filter by category if specified
        if category:
            query = query.filter(BudgetData.category.ilike(f"%{category}%"))
        
        budget_items = query.all()
        
        if not budget_items:
            return {"fiscal_year": fiscal_year, "total_amount": 0, "categories": []}
        
        # Aggregate by category
        category_totals = {}
        total_amount = 0
        
        for item in budget_items:
            if item.category not in category_totals:
                category_totals[item.category] = {
                    "category": item.category,
                    "total_amount": 0,
                    "subcategories": []
                }
            
            category_totals[item.category]["total_amount"] += item.amount
            category_totals[item.category]["subcategories"].append({
                "subcategory": item.subcategory,
                "agency": item.agency,
                "amount": item.amount,
                "function_code": item.function_code,
                "function_title": item.function_title
            })
            
            total_amount += item.amount
        
        return {
            "fiscal_year": fiscal_year,
            "data_type": data_type,
            "total_amount": total_amount,
            "categories": list(category_totals.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving budget data: {str(e)}")

@router.get("/budget/categories")
async def get_budget_categories(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """Get list of available budget categories"""
    
    try:
        query = db.query(BudgetData.category).distinct()
        
        if fiscal_year:
            query = query.filter(BudgetData.fiscal_year == fiscal_year)
        
        categories = [row[0] for row in query.all()]
        return {"categories": sorted(categories)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")

@router.get("/budget/years")
async def get_available_years(db: Session = Depends(get_db)):
    """Get list of available fiscal years"""
    
    try:
        years = db.query(BudgetData.fiscal_year).distinct().order_by(BudgetData.fiscal_year.desc()).all()
        return {"fiscal_years": [row[0] for row in years]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving fiscal years: {str(e)}") 