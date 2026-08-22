from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from routes import encode, decode, logs

app = FastAPI(title="Steganography Tool API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(encode.router, prefix="/api/encode", tags=["Encode"])
app.include_router(decode.router, prefix="/api/decode", tags=["Decode"])
app.include_router(logs.router,   prefix="/api/logs",   tags=["Logs"])

@app.get("/")
def root():
    return {"message": "Steganography Tool API is running."}

@app.get("/ui")
def serve_frontend():
    return FileResponse("index.html")
