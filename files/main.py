from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.responses import HTMLResponse
from routes import encode, decode, logs, audio_encode, audio_decode, video_encode, video_decode, cipher, text_stego
import os
app = FastAPI(title="Steganography Tool API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(encode.router,        prefix="/api/encode",        tags=["Image Encode"])
app.include_router(decode.router,        prefix="/api/decode",        tags=["Image Decode"])
app.include_router(logs.router,          prefix="/api/logs",          tags=["Logs"])
app.include_router(audio_encode.router,  prefix="/api/audio/encode",  tags=["Audio Encode"])
app.include_router(audio_decode.router,  prefix="/api/audio/decode",  tags=["Audio Decode"])
app.include_router(video_encode.router,  prefix="/api/video/encode",  tags=["Video Encode"])
app.include_router(video_decode.router,  prefix="/api/video/decode",  tags=["Video Decode"])
app.include_router(cipher.router,        prefix="/api/cipher",        tags=["Text Cipher"])
app.include_router(text_stego.router,    prefix="/api/text",          tags=["Text Stego"])

@app.get("/")
def root():
    return RedirectResponse(url="/ui")

@app.get("/ui")
def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )

@app.get("/debug")
def debug():
    cwd = os.getcwd()
    files = os.listdir(cwd)
    index_exists = os.path.exists("index.html")
    return {"cwd": cwd, "files": files, "index_exists": index_exists}
@app.get("/debug2")
def debug2():
    with open("index.html", "r") as f:
        content = f.read()
    # Find the login-overlay line
    for i, line in enumerate(content.split("\n")):
        if "login-overlay" in line and "div id" in line:
            return {"line_number": i, "content": line}
    return {"error": "not found"}