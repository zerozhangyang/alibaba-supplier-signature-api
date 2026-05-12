# -*- coding: utf-8 -*-
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.crypto.aes_util import decrypt_data
from app.db.models import SignatureRegisterEventLog, SignatureRegisterTask

MAX_PUSH_ITEMS = 1000

VALID_PRODUCE_TYPES_THIRD = {"0", "1", "2"}
VALID_PRODUCE_TYPES_DIRECT = {"0", "1", "2", "3"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_REGISTER_TYPES = {0, 1, "0", "1"}


def _json_dumps(data: Any) -> Optional[str]:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def _add_event(
    db: Session,
    *,
    flow_id: Optional[str],
    supplier_type: Optional[str],
    event_type: str,
    request_id: Optional[str],
    req_payload: Any,
    resp_payload: Any,
    success: int,
    error_message: Optional[str] = None,
):
    db.add(
        SignatureRegisterEventLog(
            flow_id=flow_id,
            supplier_type=supplier_type,
            event_type=event_type,
            direction="inbound",
            request_id=request_id,
            success=success,
            req_payload=_json_dumps(req_payload),
            resp_payload=_json_dumps(resp_payload),
            error_message=error_message,
        )
    )


def _item_value(item: dict, *keys: str):
    for key in keys:
        if key in item and item.get(key) not in (None, ""):
            return item.get(key)
    return None


def _normalize_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def _extract_task_fields(item: dict) -> Dict[str, Any]:
    register_type = _normalize_int(_item_value(item, "registerType", "register_type"))
    sign_source = _normalize_int(_item_value(item, "signSource", "SignSource"))
    return {
        "signature": _item_value(item, "signature"),
        "ext_code": _item_value(item, "extCode"),
        "sub_sms_port": _item_value(item, "subSmsPort"),
        "sign_source": sign_source,
        "apply_scene_content": _item_value(item, "applySceneContent", "ApplySceneContent"),
        "account": _item_value(item, "account"),
        "company_name": _item_value(item, "companyName"),
        "organization_code": _item_value(item, "organizationCode"),
        "regist_name": _item_value(item, "registName"),
        "regist_cert_type": _item_value(item, "registCertType"),
        "regist_cert_id": _item_value(item, "registCertId"),
        "legal_name": _item_value(item, "legalName"),
        "legal_cert_type": _item_value(item, "legalCertType"),
        "legal_cert_id": _item_value(item, "legalCertId"),
        "agency_name": _item_value(item, "agencyName"),
        "agency_cert_type": _item_value(item, "agencyCertType"),
        "agency_cert_id": _item_value(item, "agencyCertId"),
        "produce_type": _item_value(item, "produceType"),
        "industry_type": _item_value(item, "industryType"),
        "register_type": register_type if isinstance(register_type, int) else None,
        "priority": _item_value(item, "priority"),
        "sign_certificate_pic": _item_value(item, "signCertificatePic"),
        "business_license_pic": _item_value(item, "businessLicensePic"),
    }


def _validate_item(item: dict, supplier_type: str) -> Optional[str]:
    required_str = {"flowId": 64, "signature": 64, "produceType": 4, "account": 32, "priority": 4}
    for field, max_len in required_str.items():
        val = item.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return u"缺少必填字段: {}".format(field)
        if isinstance(val, str) and len(val) > max_len:
            return u"字段{}超过最大长度{}".format(field, max_len)

    if supplier_type == "third":
        if not item.get("extCode"):
            return u"缺少必填字段: extCode (三方资源)"
    else:
        if not item.get("subSmsPort"):
            return u"缺少必填字段: subSmsPort (直连供应商)"

    rt = item.get("registerType")
    if rt is None:
        return u"缺少必填字段: registerType"
    if rt not in VALID_REGISTER_TYPES:
        return u"registerType值无效, 应为0或1"

    valid_pt = VALID_PRODUCE_TYPES_DIRECT if supplier_type == "direct" else VALID_PRODUCE_TYPES_THIRD
    if item.get("produceType") not in valid_pt:
        return u"produceType值无效"

    if item.get("priority") not in VALID_PRIORITIES:
        return u"priority值无效, 应为P0/P1/P2/P3"

    return None


def handle_push(db: Session, request_id: str, encrypted_data: str, supplier_type: str = "third") -> Dict[str, Any]:
    failed_items: List[Dict[str, str]] = []

    try:
        plain = decrypt_data(encrypted_data, supplier_type)
        items = json.loads(plain)
        if not isinstance(items, list):
            return {"code": 1001, "message": u"参数错误: data解密后不是数组", "requestId": request_id, "data": []}
    except Exception as e:
        return {"code": 1001, "message": u"参数错误: {}".format(str(e)), "requestId": request_id, "data": []}

    if len(items) > MAX_PUSH_ITEMS:
        return {"code": 1001, "message": u"参数错误", "requestId": request_id, "data": []}

    sid = settings.third_supplier_id if supplier_type == "third" else settings.direct_supplier_id

    for item in items:
        flow_id = item.get("flowId", "")

        err_msg = _validate_item(item, supplier_type)
        if err_msg:
            failed_items.append({"id": flow_id or "", "errorMsg": err_msg})
            continue

        existed = db.query(SignatureRegisterTask).filter(SignatureRegisterTask.flow_id == flow_id).first()
        if existed:
            _add_event(
                db,
                flow_id=flow_id,
                supplier_type=supplier_type,
                event_type="DUPLICATE_PUSH",
                request_id=request_id,
                req_payload=item,
                resp_payload=None,
                success=1,
            )
            continue

        sp = db.begin_nested()
        try:
            task_fields = _extract_task_fields(item)
            task = SignatureRegisterTask(
                flow_id=flow_id,
                request_id=request_id,
                supplier_id=sid,
                supplier_type=supplier_type,
                raw_push_data_json=_json_dumps(item),
                current_status="RECEIVED",
                **task_fields
            )
            db.add(task)
            sp.commit()
            _add_event(
                db,
                flow_id=flow_id,
                supplier_type=supplier_type,
                event_type="PUSH_RECEIVED",
                request_id=request_id,
                req_payload=item,
                resp_payload=None,
                success=1,
            )
        except IntegrityError:
            sp.rollback()
            _add_event(
                db,
                flow_id=flow_id,
                supplier_type=supplier_type,
                event_type="DUPLICATE_PUSH",
                request_id=request_id,
                req_payload=item,
                resp_payload=None,
                success=1,
            )
        except Exception as e:
            sp.rollback()
            failed_items.append({"id": flow_id, "errorMsg": u"系统错误"})
            _add_event(
                db,
                flow_id=flow_id,
                supplier_type=supplier_type,
                event_type="PUSH_ERROR",
                request_id=request_id,
                req_payload=item,
                resp_payload=None,
                success=0,
                error_message=str(e),
            )

    db.commit()

    if failed_items:
        return {"code": 1001, "message": u"部分记录处理失败", "requestId": request_id, "data": failed_items}
    return {"code": 0, "message": u"成功", "requestId": request_id, "data": []}
