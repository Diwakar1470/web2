CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) UNIQUE NOT NULL -- 'CREATOR', 'HOD', 'FACULTY_COORDINATOR', 'STUDENT'
);

-- Create Departments Table
CREATE TABLE IF NOT EXISTS `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) UNIQUE NOT NULL,
    `description` TEXT
);

-- Create Activities Table
CREATE TABLE IF NOT EXISTS `activities` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) UNIQUE NOT NULL,
    `type` VARCHAR(50) -- 'MAIN', 'SUB'
);

-- Update Users Table
-- NOTE: MySQL doesn't support 'ADD COLUMN IF NOT EXISTS' in all versions
-- Run this only once, or check column existence before running
-- These statements may fail if columns already exist - that's expected
ALTER TABLE `users` ADD COLUMN `role_id` INT;
ALTER TABLE `users` ADD CONSTRAINT `fk_role_id` FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`);
ALTER TABLE `users` ADD COLUMN `assigned_department_id` INT;
ALTER TABLE `users` ADD CONSTRAINT `fk_assigned_department_id` FOREIGN KEY (`assigned_department_id`) REFERENCES `departments`(`id`);
ALTER TABLE `users` ADD COLUMN `assigned_activity_id` INT;
ALTER TABLE `users` ADD CONSTRAINT `fk_assigned_activity_id` FOREIGN KEY (`assigned_activity_id`) REFERENCES `activities`(`id`);
ALTER TABLE `users` ADD COLUMN `profile_completed` BOOLEAN DEFAULT FALSE;
ALTER TABLE `users` ADD COLUMN `registration_status` VARCHAR(20) DEFAULT 'PENDING'; -- 'PENDING', 'APPROVED', 'REJECTED'

-- Profile Fields
ALTER TABLE `users` ADD COLUMN `phone` VARCHAR(20);
ALTER TABLE `users` ADD COLUMN `age` INT;
ALTER TABLE `users` ADD COLUMN `gender` VARCHAR(10);
ALTER TABLE `users` ADD COLUMN `blood_group` VARCHAR(5);
ALTER TABLE `users` ADD COLUMN `address` TEXT;
ALTER TABLE `users` ADD COLUMN `photo_url` TEXT;

-- Seed Roles
INSERT IGNORE INTO `roles` (name) VALUES ('CREATOR'), ('HOD'), ('FACULTY_COORDINATOR'), ('STUDENT');

-- Seed Departments (Example)
INSERT IGNORE INTO `departments` (name) VALUES ('AI & DS'), ('CSE'), ('ECE');

-- Seed Creator Account (Password: 1234)
-- Note: In production, ensure password is hashed.
INSERT IGNORE INTO `users` (email, password, role_id, profile_completed, full_name, registration_status) 
SELECT 'create', '1234', id, TRUE, 'Super Admin', 'APPROVED' 
FROM `roles` WHERE name = 'CREATOR';