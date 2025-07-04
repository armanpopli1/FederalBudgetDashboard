from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from ..database import get_db
from ..models.outlays import Outlay
from ..models.dimensions import Agency, Bureau, Account, BudgetFunction, BudgetSubfunction, ObjectClass
from ..models.bill import Bill, BBBChange

router = APIRouter()

@router.get("/compare")
async def compare_budget_with_bill(
    bill_id: str = Query(..., description="Bill identifier to compare against (e.g., 'bbb')"),
    fiscal_year: Optional[int] = Query(None, description="Fiscal year (defaults to latest)"),
    period: Optional[str] = Query("BY", description="Period: PY, CY, or BY"),
    db: Session = Depends(get_db)
):
    """
    Compare current federal budget with proposed bill changes using real budget data
    
    Returns:
    - Current budget totals by function (aggregated from real data)
    - Proposed changes from the bill
    - New totals after changes
    - Percentage changes
    """
    
    try:
        # Verify bill exists
        bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail=f"Bill '{bill_id}' not found")
        
        # Get current budget data aggregated by function from real Outlay data
        budget_query = db.query(
            BudgetFunction.title.label('category'),
            BudgetFunction.code.label('function_code'),
            func.sum(Outlay.amount).label('total_amount')
        ).join(
            BudgetFunction, Outlay.function_id == BudgetFunction.id
        ).filter(
            Outlay.period == period
        )
        
        # Get latest fiscal year if not specified
        if fiscal_year is None:
            latest_year = db.query(func.max(Outlay.fiscal_year)).scalar()
            fiscal_year = latest_year
        
        budget_query = budget_query.filter(Outlay.fiscal_year == fiscal_year)
        budget_results = budget_query.group_by(BudgetFunction.title, BudgetFunction.code).all()
        
        # Get bill changes
        bill_changes = db.query(BBBChange).filter(BBBChange.bill_id == bill.id).all()
        
        # Aggregate current budget by category
        current_budget = {}
        total_current = 0
        
        for result in budget_results:
            category = result.category
            amount = result.total_amount or 0
            current_budget[category] = amount
            total_current += amount
        
        # Aggregate changes by category
        changes_by_category = {}
        total_changes = 0
        
        for change in bill_changes:
            if change.category not in changes_by_category:
                changes_by_category[change.category] = 0
            changes_by_category[change.category] += change.change_amount
            total_changes += change.change_amount
        
        # Combine current budget with changes
        comparison_data = []
        all_categories = set(current_budget.keys()) | set(changes_by_category.keys())
        
        for category in all_categories:
            current_amount = current_budget.get(category, 0)
            change_amount = changes_by_category.get(category, 0)
            new_amount = current_amount + change_amount
            
            # Calculate percentage change
            if current_amount > 0:
                change_percentage = (change_amount / current_amount) * 100
            elif change_amount != 0:
                change_percentage = float('inf') if change_amount > 0 else float('-inf')
            else:
                change_percentage = 0
            
            comparison_data.append({
                "category": category,
                "current_amount": current_amount,
                "proposed_change": change_amount,
                "new_amount": new_amount,
                "change_percentage": round(change_percentage, 2) if abs(change_percentage) != float('inf') else change_percentage,
                "change_direction": "increase" if change_amount > 0 else "decrease" if change_amount < 0 else "no_change"
            })
        
        # Sort by current amount (largest first)
        comparison_data.sort(key=lambda x: x["current_amount"], reverse=True)
        
        # Calculate totals
        total_new = total_current + total_changes
        total_change_percentage = (total_changes / total_current) * 100 if total_current > 0 else 0
        
        return {
            "bill": bill.to_dict(),
            "fiscal_year": fiscal_year,
            "period": period,
            "summary": {
                "current_total": total_current,
                "total_changes": total_changes,
                "new_total": total_new,
                "total_change_percentage": round(total_change_percentage, 2),
                "categories_affected": len([c for c in comparison_data if c["proposed_change"] != 0]),
                "total_categories": len(comparison_data)
            },
            "category_comparisons": comparison_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing comparison: {str(e)}")

@router.get("/compare/summary")
async def get_comparison_summary(
    bill_id: str = Query(..., description="Bill identifier"),
    fiscal_year: Optional[int] = Query(None, description="Fiscal year"),
    period: Optional[str] = Query("BY", description="Period: PY, CY, or BY"),
    db: Session = Depends(get_db)
):
    """
    Get high-level summary of budget vs bill comparison using real budget data
    
    Returns key metrics without detailed breakdowns
    """
    
    try:
        # Get bill
        bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail=f"Bill '{bill_id}' not found")
        
        # Get fiscal year
        if fiscal_year is None:
            fiscal_year = db.query(func.max(Outlay.fiscal_year)).scalar()
        
        # Get current total from real Outlay data
        current_total = db.query(func.sum(Outlay.amount)).filter(
            Outlay.fiscal_year == fiscal_year,
            Outlay.period == period
        ).scalar() or 0
        
        # Get total changes
        total_changes = db.query(func.sum(BBBChange.change_amount)).filter(
            BBBChange.bill_id == bill.id
        ).scalar() or 0
        
        # Count affected categories
        affected_categories = db.query(func.count(func.distinct(BBBChange.category))).filter(
            BBBChange.bill_id == bill.id
        ).scalar() or 0
        
        # Calculate new total and percentage
        new_total = current_total + total_changes
        change_percentage = (total_changes / current_total) * 100 if current_total > 0 else 0
        
        return {
            "bill_id": bill_id,
            "bill_title": bill.title,
            "fiscal_year": fiscal_year,
            "period": period,
            "current_total": current_total,
            "total_changes": total_changes,
            "new_total": new_total,
            "change_percentage": round(change_percentage, 2),
            "categories_affected": affected_categories,
            "impact_level": "high" if abs(change_percentage) > 5 else "medium" if abs(change_percentage) > 1 else "low"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting comparison summary: {str(e)}") 