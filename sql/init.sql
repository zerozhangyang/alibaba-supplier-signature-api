CREATE DATABASE IF NOT EXISTS `ali_supplier` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `ali_supplier`;

CREATE TABLE IF NOT EXISTS `signature_register_task` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `flow_id` VARCHAR(64) NOT NULL,
  `request_id` VARCHAR(64) DEFAULT NULL,
  `supplier_id` VARCHAR(32) NOT NULL,
  `supplier_type` VARCHAR(16) NOT NULL DEFAULT 'third' COMMENT 'third=三方资源, direct=直连供应商',
  `signature` VARCHAR(64) DEFAULT NULL,
  `ext_code` VARCHAR(16) DEFAULT NULL COMMENT '三方资源扩展码',
  `sub_sms_port` VARCHAR(16) DEFAULT NULL COMMENT '直连供应商子端口号',
  `account` VARCHAR(32) DEFAULT NULL,
  `produce_type` VARCHAR(4) DEFAULT NULL,
  `register_type` INT DEFAULT NULL,
  `priority` VARCHAR(4) DEFAULT NULL,
  `raw_push_data_json` LONGTEXT NOT NULL,
  `current_status` VARCHAR(32) NOT NULL,
  `last_error_code` VARCHAR(32) DEFAULT NULL,
  `last_error_msg` VARCHAR(1024) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_flow_id` (`flow_id`),
  KEY `idx_account` (`account`),
  KEY `idx_status` (`current_status`),
  KEY `idx_supplier_type` (`supplier_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `signature_register_event_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `flow_id` VARCHAR(64) DEFAULT NULL,
  `event_type` VARCHAR(32) NOT NULL,
  `request_id` VARCHAR(64) DEFAULT NULL,
  `http_url` VARCHAR(255) DEFAULT NULL,
  `http_status` INT DEFAULT NULL,
  `success` TINYINT NOT NULL DEFAULT 0,
  `req_payload` LONGTEXT DEFAULT NULL,
  `resp_payload` LONGTEXT DEFAULT NULL,
  `error_message` VARCHAR(1024) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_flow_id` (`flow_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 如果是从旧版升级，执行以下语句添加新字段：
-- ALTER TABLE signature_register_task ADD COLUMN `supplier_type` VARCHAR(16) NOT NULL DEFAULT 'third' AFTER `supplier_id`;
-- ALTER TABLE signature_register_task ADD COLUMN `sub_sms_port` VARCHAR(16) DEFAULT NULL AFTER `ext_code`;
-- ALTER TABLE signature_register_task ADD INDEX `idx_supplier_type` (`supplier_type`);
