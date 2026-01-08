# HOD Panel Setup - Complete Guide

## Overview

The HOD Panel has been updated with a new unified login system. HOD accounts are now created by a "Creator" (admin) and HODs will receive their credentials to log in.

- ✅ HOD login with email and password.
- ✅ First-time login requires profile completion and password change.
- ✅ Department-based access control is automatically applied based on the HOD's assigned department.
- ✅ Student analytics by class and department.
- ✅ Part 4 registration status tracking.
- ✅ Comprehensive dashboards and reports.

## Files Created/Modified

### Frontend Files

1.  **web/LOGIN-PANEL/hod-login.html** - HOD Login Page
    -   Email and password input fields.
2.  **web/hod-panel.html** - HOD Dashboard
    -   4 main tabs:
        -   📊 Overview: Statistics and registration distribution chart
        -   📚 Class Wise Analysis: Students grouped by class
        -   🏢 Department Analysis: Statistics by department
        -   👥 All Students: Complete student list
3.  **web/complete-profile.html** - Profile Completion Page
    -   Appears on first login to update profile and password.

### Backend Routes (in app.py)

1.  **POST /api/auth/login** - Authenticate all users (including HODs).
2.  **GET /api/auth/me** - Get current user's info.
3.  **PUT /api/profile/update** - Update user profile.
4.  **POST /api/auth/logout** - Logout HOD.

## How to Access

### Step 1: HOD Account Creation

HOD accounts are no longer pre-seeded. A "Creator" (admin) user will create your HOD account and provide you with your email and a temporary password.

### Step 2: HOD Login

**URL:** `http://localhost:5000/LOGIN-PANEL/hod-login.html`

**Steps:**

1.  Open the page.
2.  Enter the email and temporary password provided by the Creator.
3.  Click "Login".

### Step 3: Complete Your Profile (First-Time Login)

If you are logging in for the first time, you will be redirected to the "Complete Your Profile" page.

1.  Fill in your profile details (phone, age, etc.).
2.  Set a new, permanent password.
3.  Click "Save Profile".

You will then be redirected to the HOD Dashboard.

### Step 4: HOD Dashboard

After successful login, you'll be redirected to the HOD Panel where you can:

**Overview Tab:**

-   See total students in your department.
-   View registration statistics (Part 4).
-   Chart showing distribution of registered/pending/not-registered students.

**Class Wise Analysis Tab:**

-   View students grouped by class.
-   Expandable class sections showing student details.

**Department Analysis Tab:**

-   Statistics for your department.
-   Registration rates.

**All Students Tab:**

-   Complete list of students in your department.
-   Filter by registration status.

## Database Schema

The new unified user management system uses the following main tables:

1.  **users**: Stores all user information, including HODs, Coordinators, and the Creator.
2.  **roles**: Defines the different user roles (CREATOR, HOD, FACULTY_COORDINATOR, STUDENT).
3.  **departments**: Stores the list of academic departments.

## API Endpoints

### 1. Unified Login
```
POST /api/auth/login
Body: {
  "email": "hod.email@example.com",
  "password": "your_password"
}
Response: {
  "success": true,
  "user": {...},
  "requiresProfileCompletion": true/false
}
```

### 2. Get Current User
```
GET /api/auth/me
Headers: Session cookie
Response: {
  "success": true,
  "user": {...}
}
```

### 3. Update Profile
```
PUT /api/profile/update
Headers: Session cookie
Body: {
    "phone": "1234567890",
    "age": 45,
    ...
    "newPassword": "a_strong_password"
}
Response: {
    "success": true,
    "message": "Profile updated successfully",
    "user": {...}
}
```

### 4. Logout
```
POST /api/auth/logout
Headers: Session cookie
Response: Logout confirmation
```
