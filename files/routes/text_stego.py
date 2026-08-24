from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from stego.text_stego import encode_text_stego, decode_text_stego

router = APIRouter()

class TextEncodeRequest(BaseModel):
    cover_text: str
    secret: str

class TextDecodeRequest(BaseModel):
    stego_text: str

@router.post("/encode")
def encode(req: TextEncodeRequest):
    if not req.cover_text.strip():
        raise HTTPException(status_code=400, detail="Cover text cannot be empty.")
    if not req.secret.strip():
        raise HTTPException(status_code=400, detail="Secret message cannot be empty.")
    try:
        result = encode_text_stego(req.cover_text, req.secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"stego_text": result}

@router.post("/decode")
def decode(req: TextDecodeRequest):
    if not req.stego_text:
        raise HTTPException(status_code=400, detail="Stego text cannot be empty.")
    try:
        result = decode_text_stego(req.stego_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"secret": result}