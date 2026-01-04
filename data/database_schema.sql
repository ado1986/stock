-- 
-- 股票数据系统数据库表结构定义
-- 

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE stock_db;

-- 
-- 关注股票表
-- 存储用户关注的股票信息，包括价格提醒设置
-- 
DROP TABLE IF EXISTS `stock_concern`;
CREATE TABLE `stock_concern` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `stockname` varchar(255) NOT NULL COMMENT '股票名称',
  `stock_code` varchar(50) NOT NULL COMMENT '股票代码',
  `stock_url` varchar(500) DEFAULT NULL COMMENT '股票地址',
  `price_low` decimal(10, 2) DEFAULT NULL COMMENT '价格低于此值提醒',
  `price_high` decimal(10, 2) DEFAULT NULL COMMENT '价格高于此值提醒',
  `state` tinyint(1) DEFAULT 1 COMMENT '状态 1-启用 0-禁用',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_code` (`stock_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注股票表';

-- 
-- 股票价格历史表
-- 存储股票价格历史数据，包括股票代码、日期、价格和抓取时间
-- 
DROP TABLE IF EXISTS `stock_price_history`;
CREATE TABLE `stock_price_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `stock_code` varchar(50) NOT NULL COMMENT '股票代码',
  `stock_date` date NOT NULL COMMENT '股票日期',
  `stock_time` datetime DEFAULT NULL COMMENT '股票精确时间（时分秒）',
  `stock_price` decimal(10, 2) NOT NULL COMMENT '股票价格',
  `fetch_date` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '抓取日期',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stock_code_date` (`stock_code`, `stock_date`, `stock_time`),
  INDEX `idx_stock_code` (`stock_code`),
  INDEX `idx_stock_date` (`stock_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票价格历史表';


-- ===== 告警相关表（由开发者新增，用于存储告警状态与历史）
-- 注意：此部分为 DDL 变更，请在本地数据库上手动执行（例如：mysql -u <user> -p < data/migrations/20260103_add_alert_tables.sql）

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