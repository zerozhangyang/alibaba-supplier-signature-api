# -*- coding: utf-8 -*-
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.crypto.aes_util import encrypt_data
from app.db.models import (
    SignatureRegisterEventLog,
    SignatureRegisterResultSnapshot,
    SignatureRegisterTask,
    SignatureRegisterVendorStatus,
)

TIMEOUT_SECONDS = 3.0
VALID_STATUSES = {1, 2, 3}
VALID_VENDOR_NAMES = {u"移动", u"联通", u"电信"}
VALID_VENDOR_STATUSES = {1, 2}


def _json_dumps(data: Any) -> Optional[str]:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def _add_event(
    db: Session,
    *,
    flow_id: Optional[str],
    supplier_type: Optional[str],
    direction: str,
    event_type: str,
    request_id: Optional[str],
    event_key: Optional[str],
    http_url: Optional[str],
    http_status: Optional[int],
    success: int,
    req_payload: Any,
    resp_payload: Any,
    error_message: Optional[str] = None,
):
    db.add(
        SignatureRegisterEventLog(
            flow_id=flow_id,
            supplier_type=supplier_type,
            event_type=event_type,
            direction=direction,
            request_id=request_id,
            event_key=event_key,
            http_url=http_url,
            http_status=http_status,
            success=success,
            req_payload=_json_dumps(req_payload),
            resp_payload=_json_dumps(resp_payload),
            error_message=error_message,
        )
    )


def _get_config(supplier_type: str):
    if supplier_type == "direct":
        return settings.direct_supplier_id, settings.direct_callback_url
    return settings.third_supplier_id, settings.third_callback_url


def _post_ali(url: str, payload: dict):
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload)
            try:
                data = resp.json()
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        data = {"raw": data}
                if not isinstance(data, dict):
                    data = {"raw": data}
            except Exception:
                data = {"raw": resp.text}
            return resp.status_code, data, None
    except Exception as e:
        return None, {}, str(e)


def _validate_vendor_status(vendor_status):
    if not isinstance(vendor_status, list) or len(vendor_status) == 0:
        return u"vendorStatus必须为非空数组"
    for vs in vendor_status:
        if not isinstance(vs, dict):
            return u"vendorStatus元素必须为对象"
        name = vs.get("vendorName") or vs.get("vendor")
        if name not in VALID_VENDOR_NAMES:
            return u"vendorName无效, 应为移动/联通/电信"
        if vs.get("status") not in VALID_VENDOR_STATUSES:
            return u"vendorStatus中status无效, 应为1或2"
    return None


def _normalized_vendor_status(vendor_status: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    result = []
    for item in vendor_status or []:
        if not isinstance(item, dict):
            continue
        name = item.get("vendorName") or item.get("vendor")
        if name not in VALID_VENDOR_NAMES:
            continue
        result.append(
            {
                "vendorName": name,
                "status": item.get("status"),
                "errorCode": item.get("errorCode") or item.get("error_code"),
                "errorDesc": item.get("errorDesc") or item.get("error_desc") or item.get("desc"),
            }
        )
    return result


def _register_status_label(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    mapping = {1: "成功", 2: "失败", 3: "失败", "1": "成功", "2": "失败", "3": "失败"}
    return mapping.get(value, str(value))


def _event_key(source_type: str, flow_id: str, request_id: str) -> str:
    return "{}:{}:{}".format(source_type, flow_id, request_id)


def _upsert_snapshot(db: Session, flow_id: str, source_type: str, data: Dict[str, Any], resp_data: Optional[Dict[str, Any]] = None):
    snapshot = (
        db.query(SignatureRegisterResultSnapshot)
        .filter(
            SignatureRegisterResultSnapshot.flow_id == flow_id,
            SignatureRegisterResultSnapshot.source_type == source_type,
        )
        .first()
    )
    if not snapshot:
        snapshot = SignatureRegisterResultSnapshot(flow_id=flow_id, source_type=source_type)
        db.add(snapshot)

    response_data = resp_data.get("data") if isinstance(resp_data, dict) else None
    if isinstance(response_data, list):
        response_data = response_data[0] if response_data else {}
    if not isinstance(response_data, dict):
        response_data = {}

    snapshot.register_status = _register_status_label(data.get("status") or response_data.get("registerStatus"))
    snapshot.available_status = response_data.get("availableStatus")
    snapshot.sub_sms_port = data.get("subSmsPort") or response_data.get("subSmsPort")
    snapshot.access_code = response_data.get("accessCode")
    snapshot.desc = data.get("desc") or response_data.get("desc")
    snapshot.raw_result_json = _json_dumps({"request": data, "response": resp_data})


def _replace_vendor_status(db: Session, flow_id: str, source_type: str, vendor_status: Optional[List[Dict[str, Any]]]):
    normalized = _normalized_vendor_status(vendor_status)
    db.query(SignatureRegisterVendorStatus).filter(
        SignatureRegisterVendorStatus.flow_id == flow_id,
        SignatureRegisterVendorStatus.source_type == source_type,
    ).delete()
    for item in normalized:
        db.add(
            SignatureRegisterVendorStatus(
                flow_id=flow_id,
                source_type=source_type,
                vendor_name=item["vendorName"],
                vendor_status=item.get("status"),
                error_code=item.get("errorCode"),
                error_desc=item.get("errorDesc"),
            )
        )


def _set_task_error(task: SignatureRegisterTask, code: Optional[Any], message: Optional[str]):
    task.last_error_code = str(code) if code not in (None, "") else None
    task.last_error_msg = message


def callback_result(db: Session, flow_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    task = db.query(SignatureRegisterTask).filter(SignatureRegisterTask.flow_id == flow_id).first()
    if not task:
        return {"code": 1004, "message": u"未找到推送的报备项", "error": None}
    if task.callback_status == "CALLBACK_SUCCESS":
        return {"code": 1001, "message": u"该报备项已回传过结果, 不可重复回传", "error": None}

    st = task.supplier_type or "third"
    data = body["data"]

    missing = []
    for field in ("id", "action", "vendorStatus", "signature"):
        if field not in data or data[field] is None:
            missing.append(field)
    if missing:
        return {"code": 1001, "message": u"缺少必填字段: {}".format(",".join(missing)), "error": None}

    if data.get("action") != "report":
        return {"code": 1001, "message": u"action必须为report", "error": None}

    if st == "third":
        if data.get("status") is None:
            return {"code": 1001, "message": u"缺少必填字段: status (三方资源)", "error": None}
        if data.get("status") not in VALID_STATUSES:
            return {"code": 1001, "message": u"status值无效, 应为1/2/3", "error": None}
        if data.get("status") == 2 and not data.get("subSmsPort"):
            return {"code": 1001, "message": u"status为2时subSmsPort必填", "error": None}
        if not data.get("extCode"):
            return {"code": 1001, "message": u"缺少必填字段: extCode (三方资源)", "error": None}
    else:
        if not data.get("subSmsPort"):
            return {"code": 1001, "message": u"缺少必填字段: subSmsPort (直连供应商)", "error": None}
        if data.get("status") is not None and data.get("status") not in VALID_STATUSES:
            return {"code": 1001, "message": u"status值无效, 应为1/2/3", "error": None}

    vs_err = _validate_vendor_status(data.get("vendorStatus"))
    if vs_err:
        return {"code": 1001, "message": vs_err, "error": None}

    supplier_id, callback_url = _get_config(st)
    request_id = body.get("requestId") or str(uuid.uuid4())
    event_key = _event_key("callback", flow_id, request_id)
    payload = {
        "requestId": request_id,
        "supplierId": supplier_id,
        "data": encrypt_data(json.dumps([data], ensure_ascii=False), st),
    }

    status_code, resp_data, err = _post_ali(callback_url, payload)
    _add_event(
        db,
        flow_id=flow_id,
        supplier_type=st,
        direction="outbound",
        event_type="CALLBACK_REQUEST",
        request_id=request_id,
        event_key=event_key,
        http_url=callback_url,
        http_status=status_code,
        success=1 if err is None else 0,
        req_payload=payload,
        resp_payload=resp_data,
        error_message=err,
    )

    task.last_callback_request_id = request_id
    task.last_callback_at = datetime.now()
    if err is None and resp_data.get("code") == 0:
        task.current_status = "CALLBACK_SUCCESS"
        task.callback_status = "CALLBACK_SUCCESS"
        _set_task_error(task, None, None)
    else:
        task.current_status = "CALLBACK_FAIL"
        task.callback_status = "CALLBACK_FAIL"
        task.callback_retry_count = (task.callback_retry_count or 0) + 1
        _set_task_error(task, resp_data.get("code") or "HTTP_ERROR", err or str(resp_data))

    _upsert_snapshot(db, flow_id, "callback", data, resp_data)
    _replace_vendor_status(db, flow_id, "callback", data.get("vendorStatus"))

    db.commit()
    return {"httpStatus": status_code, "response": resp_data, "error": err}


def submit_result(db: Session, flow_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
    task = db.query(SignatureRegisterTask).filter(SignatureRegisterTask.flow_id == flow_id).first()
    if not task:
        return {"code": 1004, "message": u"未找到推送的报备项", "error": None}
    if (task.supplier_type or "third") != "third":
        return {"code": 1001, "message": u"直连供应商不支持主动提交接口", "error": None}

    data = body["data"]
    missing = []
    for field in ("action", "signature", "account", "status", "vendorStatus"):
        if field not in data or data[field] is None:
            missing.append(field)
    if missing:
        return {"code": 1001, "message": u"缺少必填字段: {}".format(",".join(missing)), "error": None}

    if data.get("action") != "report":
        return {"code": 1001, "message": u"action必须为report", "error": None}
    if data.get("status") not in VALID_STATUSES:
        return {"code": 1001, "message": u"status值无效, 应为1/2/3", "error": None}
    if data.get("status") == 2 and not data.get("subSmsPort"):
        return {"code": 1001, "message": u"status为2时subSmsPort必填", "error": None}

    vs_err = _validate_vendor_status(data.get("vendorStatus"))
    if vs_err:
        return {"code": 1001, "message": vs_err, "error": None}

    request_id = body.get("requestId") or str(uuid.uuid4())
    event_key = _event_key("submit", flow_id, request_id)
    payload = {
        "requestId": request_id,
        "supplierId": settings.third_supplier_id,
        "data": encrypt_data(json.dumps([data], ensure_ascii=False), "third"),
    }

    status_code, resp_data, err = _post_ali(settings.third_submit_url, payload)
    _add_event(
        db,
        flow_id=flow_id,
        supplier_type="third",
        direction="outbound",
        event_type="SUBMIT_REQUEST",
        request_id=request_id,
        event_key=event_key,
        http_url=settings.third_submit_url,
        http_status=status_code,
        success=1 if err is None else 0,
        req_payload=payload,
        resp_payload=resp_data,
        error_message=err,
    )

    task.last_submit_request_id = request_id
    task.last_submit_at = datetime.now()
    if err is None and resp_data.get("code") == 0:
        task.current_status = "SUBMIT_SUCCESS"
        task.submit_status = "SUBMIT_SUCCESS"
        _set_task_error(task, None, None)
    else:
        task.current_status = "SUBMIT_FAIL"
        task.submit_status = "SUBMIT_FAIL"
        task.submit_retry_count = (task.submit_retry_count or 0) + 1
        _set_task_error(task, resp_data.get("code") or "HTTP_ERROR", err or str(resp_data))

    _upsert_snapshot(db, flow_id, "submit", data, resp_data)
    _replace_vendor_status(db, flow_id, "submit", data.get("vendorStatus"))

    db.commit()
    return {"httpStatus": status_code, "response": resp_data, "error": err}


def query_result(db: Session, body: Dict[str, Any]) -> Dict[str, Any]:
    request_id = body.get("requestId") or str(uuid.uuid4())
    flow_id = body.get("flowId")
    payload = {
        "requestId": request_id,
        "supplierId": settings.third_supplier_id,
        "data": encrypt_data(json.dumps(body["data"], ensure_ascii=False), "third"),
    }

    status_code, resp_data, err = _post_ali(settings.third_query_url, payload)
    _add_event(
        db,
        flow_id=flow_id,
        supplier_type="third",
        direction="outbound",
        event_type="QUERY_REQUEST",
        request_id=request_id,
        event_key=_event_key("query", flow_id or "unknown", request_id),
        http_url=settings.third_query_url,
        http_status=status_code,
        success=1 if err is None else 0,
        req_payload=payload,
        resp_payload=resp_data,
        error_message=err,
    )

    if flow_id:
        task = db.query(SignatureRegisterTask).filter(SignatureRegisterTask.flow_id == flow_id).first()
        if task:
            if err is None and resp_data.get("code") == 0:
                task.query_status = "QUERY_SUCCESS"
                _set_task_error(task, None, None)
            else:
                task.query_status = "QUERY_FAIL"
                _set_task_error(task, resp_data.get("code") or "HTTP_ERROR", err or str(resp_data))

    response_items = resp_data.get("data") if isinstance(resp_data, dict) else None
    if flow_id:
        first_item = response_items[0] if isinstance(response_items, list) and response_items else {}
        _upsert_snapshot(db, flow_id, "query", first_item or body["data"], resp_data)
        vendor_status = first_item.get("vendorStatus") if isinstance(first_item, dict) else None
        _replace_vendor_status(db, flow_id, "query", vendor_status)

    db.commit()
    return {"httpStatus": status_code, "response": resp_data, "error": err}
