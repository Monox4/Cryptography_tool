from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.audio import encode_text_in_audio, encode_audio_in_audio
from db.mongo import encode_logs
from datetime import datetime, timezone

router = APIRouter()

ALLOWED = {'wav', 'mp3', 'flac'}

def check_audio(filename: str):
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail="Only WAV, MP3, and FLAC files are supported.")
    return ext


@router.post("/text")
async def encode_text(
    audio: UploadFile = File(...),
    message: str = Form(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    """Hide a text message inside an audio file."""
    check_audio(audio.filename)
    audio_bytes = await audio.read()

    try:
        result_bytes, out_fmt = encode_text_in_audio(audio_bytes, audio.filename, message, key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":      user_code,
        "filename":       audio.filename,
        "message_length": len(message),
        "timestamp":      datetime.now(timezone.utc),
        "status":         "success",
        "type":           "audio_text"
    })

    return Response(
        content=result_bytes,
        media_type=f"audio/{out_fmt}",
        headers={"Content-Disposition": f"attachment; filename=stego_{audio.filename.rsplit('.', 1)[0]}.{out_fmt}"}
    )


@router.post("/audio")
async def encode_audio_in_audio(
    carrier: UploadFile = File(...),
    hidden: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    """Hide an audio file inside another audio file."""
    check_audio(carrier.filename)
    check_audio(hidden.filename)

    carrier_bytes = await carrier.read()
    hidden_bytes = await hidden.read()

    try:
        from stego.audio import encode_audio_in_audio as _encode
        result_bytes, out_fmt = _encode(carrier_bytes, carrier.filename,
                                        hidden_bytes, hidden.filename, key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":   user_code,
        "filename":    carrier.filename,
        "hidden_file": hidden.filename,
        "timestamp":   datetime.now(timezone.utc),
        "status":      "success",
        "type":        "audio_audio"
    })

    return Response(
        content=result_bytes,
        media_type=f"audio/{out_fmt}",
        headers={"Content-Disposition": f"attachment; filename=stego_{carrier.filename.rsplit('.', 1)[0]}.{out_fmt}"}
    )