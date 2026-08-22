from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from routes import encode, decode, logs, audio_encode, audio_decode

app = FastAPI(title="Steganography Tool API", version="2.0.0")

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

@app.get("/")
def root():
    return RedirectResponse(url="/ui")

@app.get("/ui")
def serve_frontend():
    return FileResponse("index.html")