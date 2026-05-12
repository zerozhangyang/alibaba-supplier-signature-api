# -*- coding: utf-8 -*-
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, BigInteger, DateTime, Integer, String, Text, UniqueConstraint

from app.db.session import Base

CN_TZ = timezone(timedelta(hours=8))


def _now_cn():
    return datetime.now(CN_TZ).replace(tzinfo=None)


class SignatureRegisterTask(Base):
    __tablename__ = "signature_register_task"
    __table_args__ = (UniqueConstraint("flow_id", name="uk_flow_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flow_id = Column(String(64), nullable=False)
    request_id = Column(String(64), nullable=True)
    supplier_id = Column(String(32), nullable=False)
    supplier_type = Column(String(16), nullable=False, default="third")

    signature = Column(String(64), nullable=True)
    ext_code = Column(String(16), nullable=True)
    sub_sms_port = Column(String(16), nullable=True)
    sign_source = Column(Integer, nullable=True)
    apply_scene_content = Column(Text, nullable=True)
    account = Column(String(32), nullable=True)
    company_name = Column(String(64), nullable=True)
    organization_code = Column(String(64), nullable=True)
    regist_name = Column(String(32), nullable=True)
    regist_cert_type = Column(String(32), nullable=True)
    regist_cert_id = Column(String(64), nullable=True)
    legal_name = Column(String(32), nullable=True)
    legal_cert_type = Column(String(32), nullable=True)
    legal_cert_id = Column(String(64), nullable=True)
    agency_name = Column(String(32), nullable=True)
    agency_cert_type = Column(String(32), nullable=True)
    agency_cert_id = Column(String(64), nullable=True)
    produce_type = Column(String(4), nullable=True)
    industry_type = Column(String(4), nullable=True)
    register_type = Column(Integer, nullable=True)
    priority = Column(String(4), nullable=True)
    sign_certificate_pic = Column(String(1024), nullable=True)
    business_license_pic = Column(String(1024), nullable=True)

    raw_push_data_json = Column(Text, nullable=False)
    current_status = Column(String(32), nullable=False, default="RECEIVED")
    callback_status = Column(String(32), nullable=True)
    submit_status = Column(String(32), nullable=True)
    query_status = Column(String(32), nullable=True)
    last_callback_request_id = Column(String(64), nullable=True)
    last_submit_request_id = Column(String(64), nullable=True)
    last_callback_at = Column(DateTime, nullable=True)
    last_submit_at = Column(DateTime, nullable=True)
    callback_retry_count = Column(Integer, nullable=False, default=0)
    submit_retry_count = Column(Integer, nullable=False, default=0)
    last_error_code = Column(String(32), nullable=True)
    last_error_msg = Column(String(1024), nullable=True)

    created_at = Column(DateTime, nullable=False, default=_now_cn)
    updated_at = Column(DateTime, nullable=False, default=_now_cn, onupdate=_now_cn)


class SignatureRegisterEventLog(Base):
    __tablename__ = "signature_register_event_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flow_id = Column(String(64), nullable=True)
    supplier_type = Column(String(16), nullable=True)
    event_type = Column(String(32), nullable=False)
    direction = Column(String(16), nullable=True)
    request_id = Column(String(64), nullable=True)
    event_key = Column(String(128), nullable=True)
    http_url = Column(String(255), nullable=True)
    http_status = Column(Integer, nullable=True)
    success = Column(Integer, nullable=False, default=0)
    req_payload = Column(Text, nullable=True)
    resp_payload = Column(Text, nullable=True)
    error_message = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_now_cn)


class SignatureRegisterResultSnapshot(Base):
    __tablename__ = "signature_register_result_snapshot"
    __table_args__ = (UniqueConstraint("flow_id", "source_type", name="uk_flow_source"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flow_id = Column(String(64), nullable=False)
    source_type = Column(String(16), nullable=False)
    register_status = Column(String(32), nullable=True)
    available_status = Column(String(32), nullable=True)
    sub_sms_port = Column(String(32), nullable=True)
    access_code = Column(String(64), nullable=True)
    desc = Column(String(1024), nullable=True)
    raw_result_json = Column(Text, nullable=True)
    synced_at = Column(DateTime, nullable=False, default=_now_cn)
    created_at = Column(DateTime, nullable=False, default=_now_cn)
    updated_at = Column(DateTime, nullable=False, default=_now_cn, onupdate=_now_cn)


class SignatureRegisterVendorStatus(Base):
    __tablename__ = "signature_register_vendor_status"
    __table_args__ = (UniqueConstraint("flow_id", "source_type", "vendor_name", name="uk_flow_source_vendor"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flow_id = Column(String(64), nullable=False)
    source_type = Column(String(16), nullable=False)
    vendor_name = Column(String(16), nullable=False)
    vendor_status = Column(Integer, nullable=True)
    error_code = Column(String(32), nullable=True)
    error_desc = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_now_cn)
    updated_at = Column(DateTime, nullable=False, default=_now_cn, onupdate=_now_cn)
