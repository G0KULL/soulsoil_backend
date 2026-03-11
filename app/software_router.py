from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List
import os
import shutil
from uuid import uuid4
from .models import AgricultureSoftware
from .schemas import AgricultureSoftwareResponse

router = APIRouter(prefix="/software", tags=["Agriculture Software"])

UPLOAD_DIR = "uploads/software"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=AgricultureSoftwareResponse)
async def create_software(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...)
):
    # Save image
    file_extension = os.path.splitext(image.filename)[1]
    file_name = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    image_url = f"/uploads/software/{file_name}"
    
    software = AgricultureSoftware(
        title=title,
        description=description,
        image_url=image_url
    )
    await software.insert()
    return software

@router.get("/", response_model=List[AgricultureSoftwareResponse])
async def get_all_software():
    return await AgricultureSoftware.find_all().to_list()

@router.delete("/{software_id}")
async def delete_software(software_id: str):
    software = await AgricultureSoftware.get(software_id)
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    
    # Optional: Delete the image file
    # if os.path.exists(software.image_url.lstrip("/")):
    #     os.remove(software.image_url.lstrip("/"))
        
    await software.delete()
    return {"message": "Software deleted successfully"}
