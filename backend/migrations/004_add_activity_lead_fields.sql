-- Migration: Add activity lead fields to sub_activities table
-- This adds fields for storing sub-activity lead and activity head information

ALTER TABLE `sub_activities`
ADD COLUMN `sub_activity_lead_name` VARCHAR(255),
ADD COLUMN `sub_activity_lead_phone` VARCHAR(20),
ADD COLUMN `activity_head_name` VARCHAR(255),
ADD COLUMN `activity_head_phone` VARCHAR(20);

-- Add a comment to the table for documentation
-- ALTER TABLE `sub_activities` MODIFY COLUMN `sub_activity_lead_name` VARCHAR(255) COMMENT 'Name of the sub-activity lead/coordinator';
-- ALTER TABLE `sub_activities` MODIFY COLUMN `sub_activity_lead_phone` VARCHAR(20) COMMENT 'Phone number of the sub-activity lead';
-- ALTER TABLE `sub_activities` MODIFY COLUMN `activity_head_name` VARCHAR(255) COMMENT 'Name of the main activity head/incharge';
-- ALTER TABLE `sub_activities` MODIFY COLUMN `activity_head_phone` VARCHAR(20) COMMENT 'Phone number of the activity head';

-- Log the migration
INSERT IGNORE INTO `migration_log` (migration_name, executed_at) 
VALUES ('004_add_activity_lead_fields', NOW());
