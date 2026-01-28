from sqlalchemy import Column, String, Boolean, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'support', 'accounts', 'license'

class LicenseRequest(Base):
    __tablename__ = "license_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    server_name = Column(String, nullable=False)
    screenshot_url = Column(Text, nullable=False)
    support_comment = Column(Text, nullable=True)
    
    accounts_verified = Column(Boolean, default=False)
    accounts_verified_at = Column(DateTime, nullable=True)
    
    license_comment = Column(Text, nullable=True)
    license_given = Column(Boolean, default=False)
    license_given_at = Column(DateTime, nullable=True)
    license_verified = Column(Boolean, default=False)
    license_verified_at = Column(DateTime, nullable=True)
    license_rejected = Column(Boolean, default=False)
    license_rejected_at = Column(DateTime, nullable=True)
    license_key = Column(String, nullable=True)
    
    client_upload_url = Column(Text, nullable=True)
    sent_to_client = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
