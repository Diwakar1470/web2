ALTER TABLE attendance ADD COLUMN approval_status VARCHAR(20) DEFAULT 'approved';
ALTER TABLE attendance ADD COLUMN submitted_by VARCHAR(255);
ALTER TABLE attendance ADD COLUMN approved_by VARCHAR(255);
ALTER TABLE attendance ADD COLUMN approved_at DATETIME;
ALTER TABLE attendance ADD COLUMN batch_id VARCHAR(100);
