from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.audio import decode_audio_payload
from db.mongo import decode_logs
from datetime import datetime, timezone

router = APIRouter()

@router.post("/")
async def decode_audio(
    audio: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    """
    Extract hidden payload from a stego audio file.
    If the payload is text, returns JSON with the message.
    If the payload is audio, returns the hidden audio file as a download.
    """
    audio_bytes = await audio.read()

    try:
        result = decode_audio_payload(audio_bytes, audio.filename, key)
    except ValueError as e:
        decode_logs.insert_one({
            "user_code": user_code,
            "filename":  audio.filename,
            "timestamp": datetime.now(timezone.utc),
            "status":    "failed",
            "error":     str(e),
            "type":      "audio"
        })
        raise HTTPException(status_code=400, detail=str(e))

    decode_logs.insert_one({
        "user_code": user_code,
        "filename":  audio.filename,
        "timestamp": datetime.now(timezone.utc),
        "status":    "success",
        "type":      "audio_" + result['type']
    })

    if result['type'] == 'text':
        return {"type": "text", "message": result['content']}

    elif result['type'] == 'audio':
        hidden_name = result['filename']
        ext = hidden_name.rsplit('.', 1)[-1].lower()
        return Response(
            content=result['content'],
            media_type=f"audio/{ext}",
            headers={"Content-Disposition": f"attachment; filename={hidden_name}"}
        )