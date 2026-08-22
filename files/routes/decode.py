from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from stego.lsb import decode_image
from db.mongo import decode_logs
from datetime import datetime, timezone

router = APIRouter()

@router.post("/")
async def decode(
    image: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()

    try:
        message = decode_image(image_bytes, key)
    except ValueError as e:
        decode_logs.insert_one({
            "user_code": user_code,
            "filename":  image.filename,
            "timestamp": datetime.now(timezone.utc),
            "status":    "failed",
            "error":     str(e)
        })
        raise HTTPException(status_code=400, detail=str(e))

    decode_logs.insert_one({
        "user_code":      user_code,
        "filename":       image.filename,
        "message_length": len(message),
        "timestamp":      datetime.now(timezone.utc),
        "status":         "success"
    })

    return {"message": message}
