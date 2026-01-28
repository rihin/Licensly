from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
import sys
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import shutil
import os
import uuid
from database import get_db
from models import LicenseRequest, User
from auth import get_current_user
from config import settings
from .websocket_manager import manager

router = APIRouter(prefix="/requests", tags=["requests"])

@router.post("/")
async def create_request(
    server_name: str = Form(...),
    screenshot: UploadFile = File(...),
    support_comment: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "support":
            raise HTTPException(status_code=403, detail="Only support can create requests")

        # Handle file upload
        file_extension = screenshot.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        
        content = await screenshot.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        screenshot_url = f"/uploads/{file_name}"

        db_request = LicenseRequest(
            server_name=server_name,
            screenshot_url=screenshot_url,
            support_comment=support_comment
        )

        db.add(db_request)
        db.commit()
        db.refresh(db_request)

        await manager.broadcast("request_update")

        return db_request
    except Exception as e:
        print(f"ERROR CREATING REQUEST: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)
        print("TRACEBACK END", flush=True)
        raise e

@router.get("/")
async def get_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Everyone can see their relevant requests.
    # Support: All ?? Or just theirs? Prompt says "Each user can access ONLY their own dashboard". 
    # But usually support needs to see all requests they created or all requests in progress. 
    # Accounts: Needs to see accounts_verified=False or True?
    # License: Needs to see accounts_verified=True AND license_given=False (pending) or all?
    
    # Prompt: "Request must instantly appear in: Accounts Dashboard, License Dashboard" when submitted.
    # So all teams see the list.
    
    return db.query(LicenseRequest).order_by(LicenseRequest.created_at.desc()).all()


@router.put("/{request_id}/license")
async def grant_license(
    request_id: str,
    license_comment: str = Form("Granted"),
    # license_key removed, auto-generated
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "license":
        raise HTTPException(status_code=403, detail="Only license team can grant license")

    req = db.query(LicenseRequest).filter(LicenseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    # 🔒 ENFORCE ORDER
    # Remove explicit verification check
    # if not req.license_verified:
    #     raise HTTPException(status_code=400, detail="Request not verified yet")

    req.license_verified = True # Implicitly verify
    req.license_verified_at = datetime.utcnow()

    req.license_given = True
    req.license_given_at = datetime.utcnow()
    req.license_comment = license_comment
    
    # User requested NO license key generation
    # req.license_key = str(uuid.uuid4())[:8].upper()
    req.license_key = None 
    
    db.commit()

    await manager.broadcast("request_update")
    return {"status": "license_granted"}

@router.put("/{request_id}/reject")
async def reject_license(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "license":
        raise HTTPException(status_code=403, detail="Only license team can reject")

    req = db.query(LicenseRequest).filter(LicenseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.license_rejected = True
    req.license_rejected_at = datetime.utcnow()
    db.commit()

    await manager.broadcast("request_update")
    return {"status": "license_rejected"}

@router.put("/{request_id}/accounts-check")
async def accounts_check(
    request_id: str,
    approved: bool = Form(...),  # YES / NO
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "accounts":
        raise HTTPException(status_code=403, detail="Only accounts team allowed")

    req = db.query(LicenseRequest).filter(LicenseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if not req.license_given:
        raise HTTPException(status_code=400, detail="License not granted yet")

    req.accounts_verified = approved
    req.accounts_verified_at = datetime.utcnow()
    db.commit()

    await manager.broadcast("request_update")
    return {"status": "accounts_checked", "approved": approved}

@router.put("/{request_id}/finalize")
async def finalize_request(
    request_id: str,
    client_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "support":
        raise HTTPException(status_code=403, detail="Only support can finalize")
        
    req = db.query(LicenseRequest).filter(LicenseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Handle file upload if provided
    if client_file:
        file_extension = client_file.filename.split(".")[-1]
        file_name = f"client_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(client_file.file, buffer)
            
        req.client_upload_url = f"/uploads/{file_name}"

    req.sent_to_client = True
    # We might want to store the timestamp if we added that column, but user said "show time". 
    # The updated_at column will update automatically on commit.
    
    db.commit()
    
    await manager.broadcast("request_update")
    return {"status": "finalized"}
