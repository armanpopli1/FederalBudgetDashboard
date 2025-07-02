from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "bbb"
    title = Column(String(500), nullable=False)
    sponsor = Column(String(200), nullable=True)
    purpose = Column(Text, nullable=True)
    date_introduced = Column(DateTime, nullable=True)
    status = Column(String(100), nullable=True)
    full_text_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to changes
    changes = relationship("BBBChange", back_populates="bill")
    
    def __repr__(self):
        return f"<Bill(id='{self.bill_id}', title='{self.title[:50]}...')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "bill_id": self.bill_id,
            "title": self.title,
            "sponsor": self.sponsor,
            "purpose": self.purpose,
            "date_introduced": self.date_introduced.isoformat() if self.date_introduced else None,
            "status": self.status,
            "full_text_url": self.full_text_url,
            "created_at": self.created_at.isoformat()
        }

class BBBChange(Base):
    __tablename__ = "bbb_changes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    change_amount = Column(BigInteger, nullable=False)  # Change in dollars (can be negative)
    change_type = Column(String(50), nullable=False, default="spending")  # spending, revenue, etc.
    description = Column(Text, nullable=True)
    
    # Relationship to bill
    bill = relationship("Bill", back_populates="changes")
    
    def __repr__(self):
        return f"<BBBChange(category='{self.category}', change={self.change_amount})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "bill_id": str(self.bill_id),
            "category": self.category,
            "subcategory": self.subcategory,
            "change_amount": self.change_amount,
            "change_type": self.change_type,
            "description": self.description
        } 