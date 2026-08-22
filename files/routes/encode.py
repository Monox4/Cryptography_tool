from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.lsb import encode_image
from db.mongo import encode_logs
from datetime import datetime, timezone

router = APIRouter()

@router.post("/")
async def encode(
    image: UploadFile = File(...),
    message: str = Form(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()

    try:
        stego_bytes = encode_image(image_bytes, message, key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":      user_code,
        "filename":       image.filename,
        "message_length": len(message),
        "timestamp":      datetime.now(timezone.utc),
        "status":         "success"
    })

    return Response(
        content=stego_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=stego_{image.filename.rsplit('.', 1)[0]}.png"}
    )
