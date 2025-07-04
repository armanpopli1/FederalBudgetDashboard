"""
Dimension tables for Federal Budget Dashboard

These tables store the reference data (agencies, functions, object classes, etc.)
that are referenced by the fact tables (outlays).
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    omb_code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., "091"
    title = Column(String(200), nullable=False)  # e.g., "Department of Education"
    abbreviation = Column(String(20), nullable=True)  # e.g., "ED"
    website = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bureaus = relationship("Bureau", back_populates="agency")
    
    def __repr__(self):
        return f"<Agency(code='{self.omb_code}', title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "omb_code": self.omb_code,
            "title": self.title,
            "abbreviation": self.abbreviation,
            "website": self.website
        }

class Bureau(Base):
    __tablename__ = "bureaus"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id"), nullable=False)
    omb_code = Column(String(10), nullable=False, index=True)  # e.g., "091-0001"
    title = Column(String(200), nullable=False)
    abbreviation = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agency = relationship("Agency", back_populates="bureaus")
    accounts = relationship("Account", back_populates="bureau")
    
    def __repr__(self):
        return f"<Bureau(code='{self.omb_code}', title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "agency_id": str(self.agency_id),
            "omb_code": self.omb_code,
            "title": self.title,
            "abbreviation": self.abbreviation
        }

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bureau_id = Column(UUID(as_uuid=True), ForeignKey("bureaus.id"), nullable=False)
    omb_account_code = Column(String(20), nullable=False, index=True)  # e.g., "091-0001-0-1-501"
    budget_account_number = Column(String(20), nullable=True)  # Treasury account number
    title = Column(String(500), nullable=False)  # Account title can be long
    description = Column(Text, nullable=True)
    account_type = Column(String(50), nullable=True)  # Direct, Reimbursable, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bureau = relationship("Bureau", back_populates="accounts")
    outlays = relationship("Outlay", back_populates="account")
    
    def __repr__(self):
        return f"<Account(code='{self.omb_account_code}', title='{self.title[:50]}...')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "bureau_id": str(self.bureau_id),
            "omb_account_code": self.omb_account_code,
            "budget_account_number": self.budget_account_number,
            "title": self.title,
            "account_type": self.account_type
        }

class BudgetFunction(Base):
    __tablename__ = "budget_functions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., "501"
    title = Column(String(200), nullable=False)  # e.g., "Education, Training, Employment"
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # Discretionary, Mandatory, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subfunctions = relationship("BudgetSubfunction", back_populates="function")
    
    def __repr__(self):
        return f"<BudgetFunction(code='{self.code}', title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "category": self.category
        }

class BudgetSubfunction(Base):
    __tablename__ = "budget_subfunctions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    function_id = Column(UUID(as_uuid=True), ForeignKey("budget_functions.id"), nullable=False)
    code = Column(String(10), nullable=False, index=True)  # e.g., "501.1"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    function = relationship("BudgetFunction", back_populates="subfunctions")
    
    def __repr__(self):
        return f"<BudgetSubfunction(code='{self.code}', title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "function_id": str(self.function_id),
            "code": self.code,
            "title": self.title,
            "description": self.description
        }

class ObjectClass(Base):
    __tablename__ = "object_classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., "25.1"
    title = Column(String(200), nullable=False)  # e.g., "Advisory and assistance services"
    group_code = Column(String(10), nullable=True)  # e.g., "25"
    group_title = Column(String(200), nullable=True)  # e.g., "Contractual services and supplies"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ObjectClass(code='{self.code}', title='{self.title}')>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "code": self.code,
            "title": self.title,
            "group_code": self.group_code,
            "group_title": self.group_title,
            "description": self.description
        } 