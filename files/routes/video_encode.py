from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.video import encode_video
from db.mongo import encode_logs
from datetime import datetime, timezone

router = APIRouter()

MAX_VIDEO_MB = 50

def check_video(file: UploadFile):
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext != 'mp4':
        raise HTTPException(status_code=400, detail="Only MP4 files are supported.")

@router.post("/text")
async def encode_text(
    video: UploadFile = File(...),
    message: str = Form(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    check_video(video)
    video_bytes = await video.read()

    if len(video_bytes) > MAX_VIDEO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Video must be under {MAX_VIDEO_MB}MB.")

    try:
        result = encode_video(video_bytes, 'text', message.encode('utf-8'), key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":      user_code,
        "filename":       video.filename,
        "message_length": len(message),
        "timestamp":      datetime.now(timezone.utc),
        "status":         "success",
        "type":           "video_text"
    })

    return Response(
        content=result,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=stego_{video.filename}"}
    )


@router.post("/image")
async def encode_image(
    video: UploadFile = File(...),
    image: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    check_video(video)
    video_bytes = await video.read()
    image_bytes = await image.read()

    if len(video_bytes) > MAX_VIDEO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Video must be under {MAX_VIDEO_MB}MB.")

    try:
        result = encode_video(video_bytes, 'image', image_bytes, key, image.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":    user_code,
        "filename":     video.filename,
        "hidden_file":  image.filename,
        "timestamp":    datetime.now(timezone.utc),
        "status":       "success",
        "type":         "video_image"
    })

    return Response(
        content=result,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=stego_{video.filename}"}
    )


@router.post("/audio")
async def encode_audio(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    check_video(video)
    video_bytes = await video.read()
    audio_bytes = await audio.read()

    if len(video_bytes) > MAX_VIDEO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Video must be under {MAX_VIDEO_MB}MB.")

    allowed_audio = {'wav', 'mp3', 'flac'}
    ext = audio.filename.rsplit('.', 1)[-1].lower()
    if ext not in allowed_audio:
        raise HTTPException(status_code=400, detail="Audio must be WAV, MP3, or FLAC.")

    try:
        result = encode_video(video_bytes, 'audio', audio_bytes, key, audio.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    encode_logs.insert_one({
        "user_code":   user_code,
        "filename":    video.filename,
        "hidden_file": audio.filename,
        "timestamp":   datetime.now(timezone.utc),
        "status":      "success",
        "type":        "video_audio"
    })

    return Response(
        content=result,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=stego_{video.filename}"}
    )