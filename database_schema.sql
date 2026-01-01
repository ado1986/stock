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

