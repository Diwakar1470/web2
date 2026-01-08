-- Create Roles Table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL -- 'CREATOR', 'HOD', 'FACULTY_COORDINATOR', 'STUDENT'
);

-- Create Departments Table
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Create Activities Table
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) -- 'MAIN', 'SUB'
);

-- Update Users Table
ALTER TABLE users ADD COLUMN IF NOT EXISTS role_id INT REFERENCES roles(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_department_id INT REFERENCES departments(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_activity_id INT REFERENCES activities(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS registration_status VARCHAR(20) DEFAULT 'PENDING'; -- 'PENDING', 'APPROVED', 'REJECTED'

-- Profile Fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS age INT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(10);
ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_group VARCHAR(5);
ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT;

-- Seed Roles
INSERT INTO roles (name) VALUES ('CREATOR'), ('HOD'), ('FACULTY_COORDINATOR'), ('STUDENT') 
ON CONFLICT (name) DO NOTHING;

-- Seed Departments (Example)
INSERT INTO departments (name) VALUES ('AI & DS'), ('CSE'), ('ECE') 
ON CONFLICT (name) DO NOTHING;

-- Seed Creator Account (Password: 1234)
-- Note: In production, ensure password is hashed.
INSERT INTO users (email, password, role_id, profile_completed, full_name, registration_status) 
SELECT 'create', '1234', id, TRUE, 'Super Admin', 'APPROVED' 
FROM roles WHERE name = 'CREATOR'
ON CONFLICT DO NOTHING;