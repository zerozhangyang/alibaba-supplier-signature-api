# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import (
    SignatureRegisterEventLog,
    SignatureRegisterResultSnapshot,
    SignatureRegisterTask,
    SignatureRegisterVendorStatus,
)
from app.db.session import get_db
from app.services.ali_client import callback_result, query_result, submit_result

router = APIRouter(prefix="/internal/register", tags=["ali-outbound"])


class CallbackBody(BaseModel):
    requestId: str | None = None
    data: Dict[str, Any]


class SubmitBody(BaseModel):
    requestId: str | None = None
    data: Dict[str, Any]


class QueryBody(BaseModel):
    requestId: str | None = None
    flowId: str | None = None
    data: Dict[str, Any]


def _fmt_time(value):
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def _task_to_dict(task: SignatureRegisterTask):
    snapshots = {}
    for item in getattr(task, "_snapshots", []) or []:
        snapshots[item.source_type] = {
            "registerStatus": item.register_status,
            "availableStatus": item.available_status,
            "subSmsPort": item.sub_sms_port,
            "accessCode": item.access_code,
            "desc": item.desc,
            "updatedAt": _fmt_time(item.updated_at),
        }
    latest_query = snapshots.get("query", {})
    return {
        "id": task.id,
        "flowId": task.flow_id,
        "requestId": task.request_id,
        "supplierId": task.supplier_id,
        "supplierType": task.supplier_type,
        "signature": task.signature,
        "extCode": task.ext_code,
        "subSmsPort": task.sub_sms_port,
        "signSource": task.sign_source,
        "applySceneContent": task.apply_scene_content,
        "account": task.account,
        "companyName": task.company_name,
        "organizationCode": task.organization_code,
        "registName": task.regist_name,
        "registCertType": task.regist_cert_type,
        "registCertId": task.regist_cert_id,
        "legalName": task.legal_name,
        "legalCertType": task.legal_cert_type,
        "legalCertId": task.legal_cert_id,
        "agencyName": task.agency_name,
        "agencyCertType": task.agency_cert_type,
        "agencyCertId": task.agency_cert_id,
        "produceType": task.produce_type,
        "industryType": task.industry_type,
        "registerType": task.register_type,
        "priority": task.priority,
        "signCertificatePic": task.sign_certificate_pic,
        "businessLicensePic": task.business_license_pic,
        "status": task.current_status,
        "callbackStatus": task.callback_status,
        "submitStatus": task.submit_status,
        "queryStatus": task.query_status,
        "registerStatus": latest_query.get("registerStatus"),
        "availableStatus": latest_query.get("availableStatus"),
        "accessCode": latest_query.get("accessCode"),
        "queryDesc": latest_query.get("desc"),
        "errorCode": task.last_error_code,
        "errorMsg": task.last_error_msg,
        "rawData": task.raw_push_data_json,
        "createdAt": _fmt_time(task.created_at),
        "updatedAt": _fmt_time(task.updated_at),
        "lastCallbackAt": _fmt_time(task.last_callback_at),
        "lastSubmitAt": _fmt_time(task.last_submit_at),
        "callbackRetryCount": task.callback_retry_count,
        "submitRetryCount": task.submit_retry_count,
        "snapshots": snapshots,
    }


@router.get("/tasks")
def list_tasks(
    status: Optional[str] = Query(None),
    supplier_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    callback_status: Optional[str] = Query(None),
    submit_status: Optional[str] = Query(None),
    query_status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(SignatureRegisterTask).order_by(SignatureRegisterTask.created_at.desc())
    if status:
        q = q.filter(SignatureRegisterTask.current_status == status)
    if supplier_type:
        q = q.filter(SignatureRegisterTask.supplier_type == supplier_type)
    if callback_status:
        q = q.filter(SignatureRegisterTask.callback_status == callback_status)
    if submit_status:
        q = q.filter(SignatureRegisterTask.submit_status == submit_status)
    if query_status:
        q = q.filter(SignatureRegisterTask.query_status == query_status)
    if keyword:
        like = "%{}%".format(keyword)
        q = q.filter(
            or_(
                SignatureRegisterTask.signature.like(like),
                SignatureRegisterTask.account.like(like),
                SignatureRegisterTask.flow_id.like(like),
                SignatureRegisterTask.company_name.like(like),
            )
        )
    if start_date:
        try:
            q = q.filter(SignatureRegisterTask.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            q = q.filter(SignatureRegisterTask.created_at < end_dt)
        except ValueError:
            pass

    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    flow_ids = [item.flow_id for item in items]
    snapshot_map = {}
    if flow_ids:
        snapshots = (
            db.query(SignatureRegisterResultSnapshot)
            .filter(SignatureRegisterResultSnapshot.flow_id.in_(flow_ids))
            .all()
        )
        for snapshot in snapshots:
            snapshot_map.setdefault(snapshot.flow_id, []).append(snapshot)
    for item in items:
        item._snapshots = snapshot_map.get(item.flow_id, [])

    return {"total": total, "page": page, "size": size, "data": [_task_to_dict(item) for item in items]}


@router.get("/{flow_id}")
def get_task_detail(flow_id: str, db: Session = Depends(get_db)):
    task = db.query(SignatureRegisterTask).filter(SignatureRegisterTask.flow_id == flow_id).first()
    if not task:
        return {"code": 1004, "message": u"未找到推送的报备项"}

    snapshots = (
        db.query(SignatureRegisterResultSnapshot)
        .filter(SignatureRegisterResultSnapshot.flow_id == flow_id)
        .order_by(SignatureRegisterResultSnapshot.updated_at.desc())
        .all()
    )
    vendors = (
        db.query(SignatureRegisterVendorStatus)
        .filter(SignatureRegisterVendorStatus.flow_id == flow_id)
        .order_by(SignatureRegisterVendorStatus.source_type.asc(), SignatureRegisterVendorStatus.vendor_name.asc())
        .all()
    )
    events = (
        db.query(SignatureRegisterEventLog)
        .filter(SignatureRegisterEventLog.flow_id == flow_id)
        .order_by(SignatureRegisterEventLog.created_at.desc())
        .limit(20)
        .all()
    )
    task._snapshots = snapshots
    return {
        "task": _task_to_dict(task),
        "snapshots": [
            {
                "sourceType": item.source_type,
                "registerStatus": item.register_status,
                "availableStatus": item.available_status,
                "subSmsPort": item.sub_sms_port,
                "accessCode": item.access_code,
                "desc": item.desc,
                "updatedAt": _fmt_time(item.updated_at),
            }
            for item in snapshots
        ],
        "vendorStatuses": [
            {
                "sourceType": item.source_type,
                "vendorName": item.vendor_name,
                "vendorStatus": item.vendor_status,
                "errorCode": item.error_code,
                "errorDesc": item.error_desc,
                "updatedAt": _fmt_time(item.updated_at),
            }
            for item in vendors
        ],
        "events": [
            {
                "eventType": item.event_type,
                "direction": item.direction,
                "requestId": item.request_id,
                "eventKey": item.event_key,
                "httpUrl": item.http_url,
                "httpStatus": item.http_status,
                "success": item.success,
                "errorMessage": item.error_message,
                "reqPayload": item.req_payload,
                "respPayload": item.resp_payload,
                "createdAt": _fmt_time(item.created_at),
            }
            for item in events
        ],
    }


@router.get("/{flow_id}/events")
def get_task_events(flow_id: str, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    events = (
        db.query(SignatureRegisterEventLog)
        .filter(SignatureRegisterEventLog.flow_id == flow_id)
        .order_by(SignatureRegisterEventLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "data": [
            {
                "eventType": item.event_type,
                "direction": item.direction,
                "requestId": item.request_id,
                "eventKey": item.event_key,
                "httpUrl": item.http_url,
                "httpStatus": item.http_status,
                "success": item.success,
                "errorMessage": item.error_message,
                "reqPayload": item.req_payload,
                "respPayload": item.resp_payload,
                "createdAt": _fmt_time(item.created_at),
            }
            for item in events
        ]
    }


@router.post("/{flow_id}/callback")
def callback(flow_id: str, body: CallbackBody, db: Session = Depends(get_db)):
    return callback_result(db, flow_id, body.model_dump())


@router.post("/{flow_id}/submit")
def submit(flow_id: str, body: SubmitBody, db: Session = Depends(get_db)):
    return submit_result(db, flow_id, body.model_dump())


@router.post("/query")
def query(body: QueryBody, db: Session = Depends(get_db)):
    return query_result(db, body.model_dump())
