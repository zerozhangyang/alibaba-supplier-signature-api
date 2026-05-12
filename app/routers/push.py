# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.push_service import handle_push

router = APIRouter(prefix="/openapi/ali/register", tags=["ali-push"])


class PushRequest(BaseModel):
    requestId: str
    data: str


@router.post("/push")
def receive_push_third(payload: PushRequest, db: Session = Depends(get_db)):
    """2.1 三方资源推送接口"""
    return handle_push(db, payload.requestId, payload.data, supplier_type="third")


@router.post("/direct/push")
def receive_push_direct(payload: PushRequest, db: Session = Depends(get_db)):
    """2.1 直连供应商推送接口"""
    return handle_push(db, payload.requestId, payload.data, supplier_type="direct")
