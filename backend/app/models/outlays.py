"""
Fact tables for Federal Budget Dashboard

These tables store the actual financial data (outlays) that reference
the dimension tables (agencies, functions, object classes, etc.).
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, BigInteger, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from ..database import Base

class Outlay(Base):
    __tablename__ = "outlays"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys to dimension tables
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    function_id = Column(UUID(as_uuid=True), ForeignKey("budget_functions.id"), nullable=True)
    subfunction_id = Column(UUID(as_uuid=True), ForeignKey("budget_subfunctions.id"), nullable=True)
    object_class_id = Column(UUID(as_uuid=True), ForeignKey("object_classes.id"), nullable=True)
    
    # Time dimensions
    fiscal_year = Column(Integer, nullable=False, index=True)
    period = Column(String(20), nullable=False)  # "PY" (Prior Year), "CY" (Current Year), "BY" (Budget Year)
    
    # Financial data (in thousands of dollars to match OMB format)
    amount = Column(BigInteger, nullable=False)  # Amount in thousands of dollars
    
    # Data tracking
    data_source = Column(String(100), nullable=False)  # e.g., "OBJCLASS_2026", "HISTORICAL_ACTUALS"
    import_batch_id = Column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.0 to 1.0 for mapping confidence
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="outlays")
    function = relationship("BudgetFunction")
    subfunction = relationship("BudgetSubfunction")
    object_class = relationship("ObjectClass")
    import_batch = relationship("ImportBatch", back_populates="outlays")
    
    def __repr__(self):
        return f"<Outlay(account='{self.account.title[:30]}...', fy={self.fiscal_year}, amount=${self.amount:,}k)>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "function_id": str(self.function_id) if self.function_id else None,
            "subfunction_id": str(self.subfunction_id) if self.subfunction_id else None,
            "object_class_id": str(self.object_class_id) if self.object_class_id else None,
            "fiscal_year": self.fiscal_year,
            "period": self.period,
            "amount": self.amount,
            "data_source": self.data_source,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "created_at": self.created_at.isoformat()
        }

class ImportBatch(Base):
    __tablename__ = "import_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Import metadata
    source_file = Column(String(500), nullable=False)  # Original filename
    data_source = Column(String(100), nullable=False)  # e.g., "OBJCLASS_2026"
    file_hash = Column(String(64), nullable=False)  # SHA256 hash of source file
    
    # Import stats
    total_rows = Column(Integer, nullable=False)
    successful_imports = Column(Integer, nullable=False)
    failed_imports = Column(Integer, nullable=False)
    warnings = Column(Integer, nullable=False, default=0)
    
    # Status tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Error tracking
    error_log = Column(Text, nullable=True)
    warning_log = Column(Text, nullable=True)
    
    # Relationships
    outlays = relationship("Outlay", back_populates="import_batch")
    raw_data = relationship("RawImportData", back_populates="import_batch")
    
    def __repr__(self):
        return f"<ImportBatch(source='{self.source_file}', status='{self.status}', rows={self.total_rows})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "source_file": self.source_file,
            "data_source": self.data_source,
            "file_hash": self.file_hash,
            "total_rows": self.total_rows,
            "successful_imports": self.successful_imports,
            "failed_imports": self.failed_imports,
            "warnings": self.warnings,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

class RawImportData(Base):
    __tablename__ = "raw_import_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_batch_id = Column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False)
    
    # Raw data from CSV (stored as JSON-like text)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(Text, nullable=False)  # JSON string of original row data
    
    # Mapping status
    import_status = Column(String(50), nullable=False)  # success, failed, warning
    error_message = Column(Text, nullable=True)
    
    # Links to processed data
    outlay_id = Column(UUID(as_uuid=True), ForeignKey("outlays.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    import_batch = relationship("ImportBatch", back_populates="raw_data")
    outlay = relationship("Outlay")
    
    def __repr__(self):
        return f"<RawImportData(batch={self.import_batch_id}, row={self.row_number}, status='{self.import_status}')>"

class MappingLog(Base):
    __tablename__ = "mapping_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What was being mapped
    source_field = Column(String(100), nullable=False)  # e.g., "agency_code", "function_title"
    source_value = Column(String(500), nullable=False)  # Original value from CSV
    
    # What it mapped to
    target_table = Column(String(100), nullable=False)  # e.g., "agencies", "budget_functions"
    target_id = Column(UUID(as_uuid=True), nullable=True)  # ID it mapped to (if successful)
    
    # Mapping metadata
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.0 to 1.0
    mapping_method = Column(String(100), nullable=False)  # exact_match, fuzzy_match, manual, etc.
    
    # When and where
    import_batch_id = Column(UUID(as_uuid=True), ForeignKey("import_batches.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    import_batch = relationship("ImportBatch")
    
    def __repr__(self):
        return f"<MappingLog(source='{self.source_value}', target='{self.target_table}', confidence={self.confidence_score})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "source_field": self.source_field,
            "source_value": self.source_value,
            "target_table": self.target_table,
            "target_id": str(self.target_id) if self.target_id else None,
            "confidence_score": float(self.confidence_score),
            "mapping_method": self.mapping_method,
            "import_batch_id": str(self.import_batch_id),
            "created_at": self.created_at.isoformat()
        } 