-- Unified User Management Schema

-- Roles Table
CREATE TABLE IF NOT EXISTS roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_code VARCHAR(10) NOT NULL UNIQUE,
    dept_name VARCHAR(100) NOT NULL
);

-- Activities Table
CREATE TABLE IF NOT EXISTS activities (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    activity_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    assigned_department_id INT,
    profile_completed BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (assigned_department_id) REFERENCES departments(department_id)
);

-- Faculty Activity Mapping Table
CREATE TABLE IF NOT EXISTS faculty_activity_mapping (
    mapping_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    activity_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (activity_id) REFERENCES activities(activity_id),
    UNIQUE KEY unique_user_activity (user_id, activity_id)
);

-- Seed Roles
INSERT INTO roles (role_name, description) VALUES
('CREATOR', 'Super Admin with all privileges'),
('HOD', 'Head of Department'),
('FACULTY_COORDINATOR', 'Coordinator for a specific activity'),
('STUDENT', 'Student');

-- Seed Creator User (password is 'admin')
INSERT INTO users (full_name, email, password_hash, role_id) VALUES
('Creator Admin', 'creator@admin.com', '$2b$12$DbmIZg.x2Gv3/4e6aJzL5u.UuWj.jE/9e8b4e7b8c9d0a1b2c3d4e5f', (SELECT role_id FROM roles WHERE role_name = 'CREATOR'));
