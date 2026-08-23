from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from stego.video import decode_video
from db.mongo import decode_logs
from datetime import datetime, timezone

router = APIRouter()

@router.post("/")
async def decode_video_route(
    video: UploadFile = File(...),
    key: str = Form(...),
    user_code: str = Form(default="anonymous")
):
    ext = video.filename.rsplit('.', 1)[-1].lower()
    if ext != 'mp4':
        raise HTTPException(status_code=400, detail="Only MP4 files are supported.")

    video_bytes = await video.read()

    try:
        result = decode_video(video_bytes, key)
    except ValueError as e:
        decode_logs.insert_one({
            "user_code": user_code,
            "filename":  video.filename,
            "timestamp": datetime.now(timezone.utc),
            "status":    "failed",
            "error":     str(e),
            "type":      "video"
        })
        raise HTTPException(status_code=400, detail=str(e))

    decode_logs.insert_one({
        "user_code": user_code,
        "filename":  video.filename,
        "timestamp": datetime.now(timezone.utc),
        "status":    "success",
        "type":      "video_" + result['type']
    })

    if result['type'] == 'text':
        return {"type": "text", "message": result['content']}

    else:
        # image or audio — return as file download
        ext = result['filename'].rsplit('.', 1)[-1].lower() if result['filename'] else 'bin'
        media_map = {
            'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'gif': 'image/gif', 'webp': 'image/webp',
            'wav': 'audio/wav', 'mp3': 'audio/mpeg', 'flac': 'audio/flac'
        }
        media_type = media_map.get(ext, 'application/octet-stream')
        return Response(
            content=result['content'],
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )