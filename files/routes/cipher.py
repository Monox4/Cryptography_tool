from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from stego.ciphers import apply_cipher

router = APIRouter()

class CipherRequest(BaseModel):
    text: str
    cipher: str
    mode: str
    key: str = ''
    shift: int = 3
    rails: int = 3

@router.post("/")
def run_cipher(req: CipherRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if not req.cipher:
        raise HTTPException(status_code=400, detail="Cipher type is required.")
    if req.mode not in ('encrypt', 'decrypt'):
        raise HTTPException(status_code=400, detail="Mode must be 'encrypt' or 'decrypt'.")

    try:
        result = apply_cipher(
            cipher=req.cipher,
            text=req.text,
            mode=req.mode,
            key=req.key,
            shift=req.shift,
            rails=req.rails
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "input":  req.text,
        "output": result,
        "cipher": req.cipher,
        "mode":   req.mode
    }