from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models.outlays import Outlay
from ..models.dimensions import Agency, Bureau, Account, BudgetFunction, BudgetSubfunction, ObjectClass

router = APIRouter()

@router.get("/budget")
async def get_budget(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year (defaults to latest)"),
    period: Optional[str] = Query("BY", description="Period: PY, CY, or BY"),
    agency_code: Optional[str] = Query(None, description="Filter by agency OMB code"),
    function_code: Optional[str] = Query(None, description="Filter by budget function code"),
    db: Session = Depends(get_db)
):
    """
    Get federal budget data with optional filtering
    
    Returns budget data aggregated by function, with optional filters for:
    - fiscal_year: Specific fiscal year (defaults to latest available)
    - period: PY (Prior Year), CY (Current Year), or BY (Budget Year) 
    - agency_code: Specific agency OMB code
    - function_code: Specific budget function code
    """
    
    try:
        # Base query with joins to dimension tables
        query = db.query(
            Outlay,
            Agency.title.label('agency_title'),
            Agency.omb_code.label('agency_code'),
            BudgetFunction.title.label('function_title'),
            BudgetFunction.code.label('function_code'),
            BudgetSubfunction.title.label('subfunction_title'),
            BudgetSubfunction.code.label('subfunction_code'),
            ObjectClass.title.label('object_class_title'),
            ObjectClass.code.label('object_class_code')
        ).join(
            Account, Outlay.account_id == Account.id
        ).join(
            Bureau, Account.bureau_id == Bureau.id
        ).join(
            Agency, Bureau.agency_id == Agency.id
        ).join(
            BudgetFunction, Outlay.function_id == BudgetFunction.id
        ).outerjoin(
            BudgetSubfunction, Outlay.subfunction_id == BudgetSubfunction.id
        ).outerjoin(
            ObjectClass, Outlay.object_class_id == ObjectClass.id
        )
        
        # Filter by period
        query = query.filter(Outlay.period == period)
        
        # If no fiscal year specified, get the latest one
        if fiscal_year is None:
            latest_year_query = db.query(func.max(Outlay.fiscal_year))
            latest_year = latest_year_query.scalar()
            if latest_year:
                fiscal_year = latest_year
            else:
                # Return empty if no data
                return {"fiscal_year": None, "period": period, "total_amount": 0, "functions": []}
        
        query = query.filter(Outlay.fiscal_year == fiscal_year)
        
        # Filter by agency if specified
        if agency_code:
            query = query.filter(Agency.omb_code == agency_code)
        
        # Filter by function if specified
        if function_code:
            query = query.filter(BudgetFunction.code == function_code)
        
        results = query.all()
        
        if not results:
            return {"fiscal_year": fiscal_year, "period": period, "total_amount": 0, "functions": []}
        
        # Aggregate by budget function
        function_totals = {}
        total_amount = 0
        
        for result in results:
            outlay = result.Outlay
            function_key = result.function_code
            
            if function_key not in function_totals:
                function_totals[function_key] = {
                    "function_code": result.function_code,
                    "function_title": result.function_title,
                    "total_amount": 0,
                    "agencies": {}
                }
            
            # Add to function total
            function_totals[function_key]["total_amount"] += outlay.amount
            
            # Aggregate by agency within function
            agency_key = result.agency_code
            if agency_key not in function_totals[function_key]["agencies"]:
                function_totals[function_key]["agencies"][agency_key] = {
                    "agency_code": result.agency_code,
                    "agency_title": result.agency_title,
                    "amount": 0
                }
            
            function_totals[function_key]["agencies"][agency_key]["amount"] += outlay.amount
            total_amount += outlay.amount
        
        # Convert to list format
        functions_list = []
        for func_data in function_totals.values():
            func_data["agencies"] = list(func_data["agencies"].values())
            functions_list.append(func_data)
        
        # Sort by total amount (descending)
        functions_list.sort(key=lambda x: x["total_amount"], reverse=True)
        
        return {
            "fiscal_year": fiscal_year,
            "period": period,
            "total_amount": total_amount,
            "functions": functions_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving budget data: {str(e)}")

@router.get("/budget/functions")
async def get_budget_functions(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """Get list of available budget functions"""
    
    try:
        query = db.query(BudgetFunction.code, BudgetFunction.title).distinct()
        
        if fiscal_year:
            # Filter functions that have outlays in the specified year
            query = query.join(Outlay, Outlay.function_id == BudgetFunction.id)\
                         .filter(Outlay.fiscal_year == fiscal_year)
        
        functions = [{"code": row[0], "title": row[1]} for row in query.all()]
        return {"functions": sorted(functions, key=lambda x: x["code"])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving functions: {str(e)}")

@router.get("/budget/agencies")
async def get_budget_agencies(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year"),
    db: Session = Depends(get_db)
):
    """Get list of available agencies"""
    
    try:
        query = db.query(Agency.omb_code, Agency.title).distinct()
        
        if fiscal_year:
            # Filter agencies that have outlays in the specified year
            query = query.join(Bureau, Bureau.agency_id == Agency.id)\
                         .join(Account, Account.bureau_id == Bureau.id)\
                         .join(Outlay, Outlay.account_id == Account.id)\
                         .filter(Outlay.fiscal_year == fiscal_year)
        
        agencies = [{"code": row[0], "title": row[1]} for row in query.all()]
        return {"agencies": sorted(agencies, key=lambda x: x["code"])}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agencies: {str(e)}")

@router.get("/budget/years")
async def get_available_years(db: Session = Depends(get_db)):
    """Get list of available fiscal years"""
    
    try:
        years = db.query(Outlay.fiscal_year).distinct().order_by(Outlay.fiscal_year.desc()).all()
        return {"fiscal_years": [row[0] for row in years]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving fiscal years: {str(e)}")

@router.get("/budget/summary")
async def get_budget_summary(
    fiscal_year: Optional[int] = Query(None, description="Fiscal year"),
    period: Optional[str] = Query("BY", description="Period: PY, CY, or BY"),
    db: Session = Depends(get_db)
):
    """Get high-level budget summary statistics"""
    
    try:
        # If no fiscal year specified, get the latest one
        if fiscal_year is None:
            latest_year_query = db.query(func.max(Outlay.fiscal_year))
            fiscal_year = latest_year_query.scalar()
        
        if not fiscal_year:
            return {"fiscal_year": None, "period": period, "summary": {}}
        
        # Get total budget
        total_query = db.query(func.sum(Outlay.amount))\
                       .filter(Outlay.fiscal_year == fiscal_year)\
                       .filter(Outlay.period == period)
        total_amount = total_query.scalar() or 0
        
        # Get top 5 functions by spending
        top_functions_query = db.query(
            BudgetFunction.code,
            BudgetFunction.title,
            func.sum(Outlay.amount).label('total')
        ).join(
            Outlay, Outlay.function_id == BudgetFunction.id
        ).filter(
            Outlay.fiscal_year == fiscal_year,
            Outlay.period == period
        ).group_by(
            BudgetFunction.code, BudgetFunction.title
        ).order_by(
            func.sum(Outlay.amount).desc()
        ).limit(5)
        
        top_functions = [
            {
                "function_code": row[0],
                "function_title": row[1],
                "amount": row[2],
                "percentage": (row[2] / total_amount * 100) if total_amount > 0 else 0
            }
            for row in top_functions_query.all()
        ]
        
        # Get top 5 agencies by spending
        top_agencies_query = db.query(
            Agency.omb_code,
            Agency.title,
            func.sum(Outlay.amount).label('total')
        ).join(
            Bureau, Bureau.agency_id == Agency.id
        ).join(
            Account, Account.bureau_id == Bureau.id
        ).join(
            Outlay, Outlay.account_id == Account.id
        ).filter(
            Outlay.fiscal_year == fiscal_year,
            Outlay.period == period
        ).group_by(
            Agency.omb_code, Agency.title
        ).order_by(
            func.sum(Outlay.amount).desc()
        ).limit(5)
        
        top_agencies = [
            {
                "agency_code": row[0],
                "agency_title": row[1],
                "amount": row[2],
                "percentage": (row[2] / total_amount * 100) if total_amount > 0 else 0
            }
            for row in top_agencies_query.all()
        ]
        
        return {
            "fiscal_year": fiscal_year,
            "period": period,
            "summary": {
                "total_amount": total_amount,
                "top_functions": top_functions,
                "top_agencies": top_agencies
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving budget summary: {str(e)}") 