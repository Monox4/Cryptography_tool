from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.lsb import encode_image
from stego.dct import encode_dct
from stego.dwt import encode_dwt
from db.mongo import encode_logs
from datetime import datetime, timezone

router = APIRouter()

@router.post("/")
async def encode(
    image: UploadFile = File(...),
    message: str = Form(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous"),
    randomize: bool = Form(default=False),
    algorithm: str = Form(default="LSB-1"),
    preserve_exif: bool = Form(default=False)
):
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    image_bytes = await image.read()

    try:
        if algorithm == "DCT":
            stego_bytes = encode_dct(image_bytes, message, key)
        elif algorithm == "DWT":
            stego_bytes = encode_dwt(image_bytes, message, key)
        else:
            if algorithm not in ("LSB-1", "LSB-2", "LSB-4"):
                raise ValueError("Invalid algorithm.")
            stego_bytes = encode_image(image_bytes, message, key, randomize, algorithm, preserve_exif)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":      user_code,
        "filename":       image.filename,
        "message_length": len(message),
        "timestamp":      datetime.now(timezone.utc),
        "status":         "success",
        "randomize":      randomize,
        "algorithm":      algorithm,
        "preserve_exif":  preserve_exif
    })

    return Response(
        content=stego_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=stego_{image.filename.rsplit('.', 1)[0]}.png"}
    )