from sqlalchemy import Column, Integer, String, BigInteger, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base

class BudgetData(Base):
    __tablename__ = "budget_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    agency = Column(String(100), nullable=True, index=True)
    amount = Column(BigInteger, nullable=False)  # Amount in dollars
    fiscal_year = Column(Integer, nullable=False, index=True)
    data_type = Column(String(20), nullable=False, default="outlays")  # outlays, budget_authority
    function_code = Column(String(10), nullable=True)  # OMB function codes
    function_title = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f"<BudgetData(category='{self.category}', amount={self.amount}, fy={self.fiscal_year})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "category": self.category,
            "subcategory": self.subcategory,
            "agency": self.agency,
            "amount": self.amount,
            "fiscal_year": self.fiscal_year,
            "data_type": self.data_type,
            "function_code": self.function_code,
            "function_title": self.function_title
        } 