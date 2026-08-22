from fastapi import APIRouter, Query
from db.mongo import encode_logs, decode_logs
from bson import ObjectId

router = APIRouter()

def serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/encode")
def get_encode_logs(user_code: str = Query(default=None), limit: int = 50):
    query = {"user_code": user_code} if user_code else {}
    docs = encode_logs.find(query).sort("timestamp", -1).limit(limit)
    return [serialize(d) for d in docs]


@router.get("/decode")
def get_decode_logs(user_code: str = Query(default=None), limit: int = 50):
    query = {"user_code": user_code} if user_code else {}
    docs = decode_logs.find(query).sort("timestamp", -1).limit(limit)
    return [serialize(d) for d in docs]


@router.get("/summary")
def get_summary(user_code: str = Query(default=None)):
    query = {"user_code": user_code} if user_code else {}
    total_encodes = encode_logs.count_documents(query)
    total_decodes = decode_logs.count_documents(query)

    return {
        "total_encodes": total_encodes,
        "total_decodes": total_decodes,
    }
