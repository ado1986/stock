-- Migration: 2026-01-03
-- Add alert tables for threshold-based notifications
-- IMPORTANT: This file only defines the DDL. Execute it manually on your MySQL instance (for example via `mysql -u <user> -p < data/migrations/20260103_add_alert_tables.sql`).

DROP TABLE IF EXISTS `stock_alert_state`;
CREATE TABLE `stock_alert_state` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `concern_id` INT(11) DEFAULT NULL COMMENT '引用 stock_concern 表的 ID',
  `stock_code` VARCHAR(50) NOT NULL COMMENT '股票代码（冗余）',
  `alert_type` ENUM('low','high') NOT NULL COMMENT '告警类型：low=低于阈值, high=高于阈值',
  `threshold` DECIMAL(10,2) NOT NULL COMMENT '触发阈值（来自 stock_concern 的 price_low/price_high）',
  `is_triggered` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '当前是否处于已触发（冷却中）状态',
  `last_triggered_at` DATETIME DEFAULT NULL COMMENT '上次触发时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_concern_alert_type` (`concern_id`, `alert_type`),
  INDEX `idx_stock_code` (`stock_code`),
  CONSTRAINT `fk_alert_state_concern` FOREIGN KEY (`concern_id`) REFERENCES `stock_concern` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票告警当前状态表';


DROP TABLE IF EXISTS `stock_alert_history`;
CREATE TABLE `stock_alert_history` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `concern_id` INT(11) DEFAULT NULL COMMENT '引用 stock_concern 表的 ID',
  `stock_code` VARCHAR(50) NOT NULL COMMENT '股票代码（冗余）',
  `alert_type` ENUM('low','high') NOT NULL COMMENT '告警类型',
  `threshold` DECIMAL(10,2) NOT NULL COMMENT '触发阈值',
  `stock_price` DECIMAL(10,2) NOT NULL COMMENT '触发时股票价格',
  `notified` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '邮件是否发送成功（1=成功, 0=失败）',
  `error_message` VARCHAR(500) DEFAULT NULL COMMENT '发送失败时的错误信息',
  `alert_sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '告警发送时间',
  PRIMARY KEY (`id`),
  INDEX `idx_alert_sent_at` (`alert_sent_at`),
  INDEX `idx_stock_code` (`stock_code`),
  CONSTRAINT `fk_alert_history_concern` FOREIGN KEY (`concern_id`) REFERENCES `stock_concern` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票告警历史记录表';
