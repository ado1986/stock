-- Add PE/PB/ROE columns to stock_price_history
ALTER TABLE `stock_price_history`
  ADD COLUMN `pe_ttm` DECIMAL(10,2) DEFAULT NULL COMMENT '市盈率(TTM)',
  ADD COLUMN `pb` DECIMAL(10,2) DEFAULT NULL COMMENT '市净率',
  ADD COLUMN `roe` DECIMAL(6,2) DEFAULT NULL COMMENT '净资产收益率（百分比，保留两位）';

-- Note: Run this migration on your DB: mysql -u <user> -p < data/migrations/20260104_add_pe_pb_roe_to_stock_price_history.sql
