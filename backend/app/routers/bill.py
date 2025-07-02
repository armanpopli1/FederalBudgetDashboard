from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.bill import Bill, BBBChange

router = APIRouter()

@router.get("/bill/{bill_id}")
async def get_bill(
    bill_id: str = Path(..., description="Bill identifier (e.g., 'bbb')"),
    db: Session = Depends(get_db)
):
    """
    Get bill metadata and summary information
    
    Returns:
    - Bill metadata (title, sponsor, purpose, etc.)
    - Summary of proposed changes
    """
    
    try:
        # Get bill metadata
        bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
        
        if not bill:
            raise HTTPException(status_code=404, detail=f"Bill '{bill_id}' not found")
        
        # Get associated changes
        changes = db.query(BBBChange).filter(BBBChange.bill_id == bill.id).all()
        
        # Calculate summary statistics
        total_spending_change = sum(change.change_amount for change in changes if change.change_type == "spending")
        positive_changes = [c for c in changes if c.change_amount > 0]
        negative_changes = [c for c in changes if c.change_amount < 0]
        
        return {
            "bill": bill.to_dict(),
            "summary": {
                "total_spending_change": total_spending_change,
                "total_changes": len(changes),
                "increases": len(positive_changes),
                "decreases": len(negative_changes),
                "categories_affected": len(set(change.category for change in changes))
            },
            "changes": [change.to_dict() for change in changes]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bill data: {str(e)}")

@router.get("/bill/{bill_id}/changes")
async def get_bill_changes(
    bill_id: str = Path(..., description="Bill identifier"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed changes proposed by a bill
    
    Returns list of changes with optional category filtering
    """
    
    try:
        # Verify bill exists
        bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
        if not bill:
            raise HTTPException(status_code=404, detail=f"Bill '{bill_id}' not found")
        
        # Get changes
        query = db.query(BBBChange).filter(BBBChange.bill_id == bill.id)
        
        if category:
            query = query.filter(BBBChange.category.ilike(f"%{category}%"))
        
        changes = query.all()
        
        # Group by category for easier frontend consumption
        category_changes = {}
        for change in changes:
            if change.category not in category_changes:
                category_changes[change.category] = {
                    "category": change.category,
                    "total_change": 0,
                    "changes": []
                }
            
            category_changes[change.category]["total_change"] += change.change_amount
            category_changes[change.category]["changes"].append(change.to_dict())
        
        return {
            "bill_id": bill_id,
            "category_filter": category,
            "total_categories": len(category_changes),
            "category_changes": list(category_changes.values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bill changes: {str(e)}")

@router.get("/bills")
async def get_all_bills(db: Session = Depends(get_db)):
    """Get list of all available bills"""
    
    try:
        bills = db.query(Bill).all()
        
        return {
            "bills": [bill.to_dict() for bill in bills],
            "total": len(bills)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bills: {str(e)}") 