-- HOD Management Database Schema

-- HOD Credentials Table
CREATE TABLE IF NOT EXISTS hod_credentials (
    hod_id INT PRIMARY KEY AUTO_INCREMENT,
    hod_user_id INT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    dept_code VARCHAR(10) NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_temp VARCHAR(10) NOT NULL,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    created_by VARCHAR(100),
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_code (dept_code),
    INDEX idx_username (username),
    INDEX idx_status (status)
);

-- HOD Profiles Table
CREATE TABLE IF NOT EXISTS hod_profiles (
    profile_id INT PRIMARY KEY AUTO_INCREMENT,
    hod_id INT NOT NULL,
    designation VARCHAR(100),
    office_location VARCHAR(255),
    office_hours VARCHAR(100),
    profile_image VARCHAR(255),
    bio TEXT,
    specialization VARCHAR(255),
    qualifications VARCHAR(255),
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hod_id) REFERENCES hod_credentials(hod_id),
    UNIQUE KEY unique_hod_profile (hod_id)
);

-- HOD Roles and Permissions Table
CREATE TABLE IF NOT EXISTS hod_roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    access_level INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HOD Permissions Table
CREATE TABLE IF NOT EXISTS hod_permissions (
    permission_id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES hod_roles(role_id),
    INDEX idx_role_id (role_id),
    UNIQUE KEY unique_role_permission (role_id, permission_name)
);

-- Department Access Control Table
CREATE TABLE IF NOT EXISTS department_access (
    access_id INT PRIMARY KEY AUTO_INCREMENT,
    hod_id INT NOT NULL,
    dept_code VARCHAR(10) NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    student_filter VARCHAR(500),
    can_view_students BOOLEAN DEFAULT TRUE,
    can_approve_requests BOOLEAN DEFAULT TRUE,
    can_view_reports BOOLEAN DEFAULT TRUE,
    can_manage_courses BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hod_id) REFERENCES hod_credentials(hod_id),
    INDEX idx_hod_id (hod_id),
    INDEX idx_dept_code (dept_code),
    UNIQUE KEY unique_hod_dept (hod_id, dept_code)
);

-- HOD Login History Table
CREATE TABLE IF NOT EXISTS hod_login_history (
    login_id INT PRIMARY KEY AUTO_INCREMENT,
    hod_id INT NOT NULL,
    username VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL,
    status ENUM('success', 'failed', 'active') DEFAULT 'success',
    failure_reason VARCHAR(255),
    FOREIGN KEY (hod_id) REFERENCES hod_credentials(hod_id),
    INDEX idx_hod_id (hod_id),
    INDEX idx_login_time (login_time)
);

-- HOD Action Audit Log Table
CREATE TABLE IF NOT EXISTS hod_audit_log (
    audit_id INT PRIMARY KEY AUTO_INCREMENT,
    hod_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INT,
    details JSON,
    ip_address VARCHAR(45),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hod_id) REFERENCES hod_credentials(hod_id),
    INDEX idx_hod_id (hod_id),
    INDEX idx_action_time (action_time),
    INDEX idx_action (action)
);

-- Create indexes for better query performance
CREATE INDEX idx_hod_dept ON hod_credentials(dept_code);
CREATE INDEX idx_hod_status ON hod_credentials(status);
CREATE INDEX idx_hod_profile_id ON hod_profiles(hod_id);
CREATE INDEX idx_dept_access_hod ON department_access(hod_id);
CREATE INDEX idx_dept_access_dept ON department_access(dept_code);
