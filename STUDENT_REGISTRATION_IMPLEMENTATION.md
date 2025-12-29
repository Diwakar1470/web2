# STUDENT REGISTRATION & ACTIVITY APPLICATION SYSTEM

## ✅ IMPLEMENTATION COMPLETE

### Overview
Complete student registration and activity application system with approval workflow. Students can only apply for ONE activity at a time, with coordinator and HOD approval required.

---

## 🔄 APPLICATION WORKFLOW

```
1. STUDENT REGISTERS
   ↓
2. STUDENT LOGS IN (credentials verified from database)
   ↓
3. STUDENT APPLIES FOR ACTIVITY (only if no pending/approved application)
   ↓
4. COORDINATOR REVIEWS
   ├─ APPROVE → Goes to HOD
   └─ REJECT → Student can apply for another activity
      ↓
5. HOD REVIEWS (only if coordinator approved)
   ├─ APPROVE → FINAL APPROVAL (student locked, cannot apply again)
   └─ REJECT → Student can apply for another activity
```

---

## 📡 NEW BACKEND ENDPOINTS

### 1. Student Registration
**Endpoint:** `POST /api/students`

**Purpose:** Register a new student account and save to database

**Request Body:**
```json
{
  "email": "237706p@pbsiddhartha.ac.in",
  "admissionId": "12345",
  "studentName": "John Doe",
  "rollNo": "237706p",
  "department": "Computer Science",
  "year": "2023"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Student registered successfully",
  "student": {
    "email": "237706p@pbsiddhartha.ac.in",
    "admissionId": "12345",
    "studentName": "John Doe",
    ...
  }
}
```

**Error Response (409 Conflict):**
```json
{
  "error": "Student already registered with this email"
}
```

---

### 2. Check Application Status
**Endpoint:** `POST /api/students/application-status`

**Purpose:** Check if student can apply (no pending/approved applications)

**Request Body:**
```json
{
  "email": "237706p@pbsiddhartha.ac.in",
  "admissionId": "12345"
}
```

**Response (Can Apply):**
```json
{
  "canApply": true,
  "message": "You can apply for an activity"
}
```

**Response (Cannot Apply):**
```json
{
  "canApply": false,
  "reason": "You already have a pending application for NCC",
  "existingApplication": { ... }
}
```

---

### 3. Apply for Activity
**Endpoint:** `POST /api/registrations`

**Purpose:** Submit activity application (enforces one-at-a-time rule)

**Request Body:**
```json
{
  "email": "237706p@pbsiddhartha.ac.in",
  "admissionId": "12345",
  "studentName": "John Doe",
  "activityName": "NCC",
  "activityCategory": "DEFENSE",
  "course": "Army Wing"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "registration": {
    "id": 1,
    "studentEmail": "237706p@pbsiddhartha.ac.in",
    "activityName": "NCC",
    "status": "pending",
    "coordinatorStatus": "pending",
    "hodStatus": "pending",
    "timestamp": "2025-12-29T06:30:00Z"
  }
}
```

**Error Response (409 Conflict - Duplicate Application):**
```json
{
  "error": "You already have a pending application for NCC. You can only apply for one activity at a time."
}
```

---

### 4. Coordinator Approval/Rejection
**Endpoint:** `POST /api/registrations/<reg_id>/coordinator-approve`

**Purpose:** Coordinator approves or rejects application

**Request Body (Approve):**
```json
{
  "action": "approve"
}
```

**Request Body (Reject):**
```json
{
  "action": "reject",
  "reason": "Insufficient documents"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "registration": {
    "id": 1,
    "status": "coordinator_approved",  // or "rejected"
    "coordinatorStatus": "approved",
    "rejectionReason": null  // or reason if rejected
  }
}
```

---

### 5. HOD Approval/Rejection
**Endpoint:** `POST /api/registrations/<reg_id>/hod-approve`

**Purpose:** HOD final approval (only if coordinator approved)

**Request Body (Approve):**
```json
{
  "action": "approve"
}
```

**Request Body (Reject):**
```json
{
  "action": "reject",
  "reason": "Activity quota full"
}
```

**Response (200 OK - Approved):**
```json
{
  "success": true,
  "registration": {
    "id": 1,
    "status": "hod_approved",  // FINAL - student locked
    "coordinatorStatus": "approved",
    "hodStatus": "approved"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Registration must be approved by coordinator first"
}
```

---

## 🗄️ DATABASE CHANGES

### Updated Registration Model

**New Fields:**
- `student_email` (String, indexed) - Student's email
- `admission_id` (String, indexed) - Student's admission ID
- `activity_name` (String, indexed) - Activity name
- `status` (String) - Overall status
  - `pending` - Initial state
  - `coordinator_approved` - Coordinator approved, pending HOD
  - `hod_approved` - Fully approved (FINAL)
  - `rejected` - Rejected by coordinator or HOD
- `coordinator_status` (String) - pending/approved/rejected
- `hod_status` (String) - pending/approved/rejected
- `rejection_reason` (Text) - Why rejected
- `updated_at` (DateTime) - Last update timestamp

---

## 🎯 BUSINESS RULES ENFORCED

### ✅ Rule 1: One Activity at a Time
- Students can only have ONE pending or approved application
- Enforced in `/api/registrations` endpoint
- Database query checks for existing applications with status:
  - `pending`
  - `coordinator_approved`
  - `hod_approved`

### ✅ Rule 2: Rejection Allows Reapplication
- If application is rejected (by coordinator or HOD)
- Status becomes `rejected`
- Student can apply for another activity
- Previous rejection record is kept for history

### ✅ Rule 3: Sequential Approval
- Coordinator must approve first
- HOD can only approve if coordinator approved
- Both must approve for final acceptance

### ✅ Rule 4: Final Approval Locks Student
- Once HOD approves (`status = 'hod_approved'`)
- Student CANNOT apply for any other activity
- Permanent lock until admin intervention

---

## 🖥️ FRONTEND CHANGES

### student-login.html Updates

**Registration Function:**
- Now calls `POST /api/students` to save to database
- Removed localStorage-only storage
- Shows proper error messages
- Pre-fills login form after successful registration

**Before:**
```javascript
// OLD: Only saved to localStorage
localStorage.setItem('studentProfiles', JSON.stringify(studentProfiles));
```

**After:**
```javascript
// NEW: Saves to database via API
const response = await fetch('http://localhost:5000/api/students', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        email: email.toLowerCase(),
        admissionId: admissionId,
        studentName: fullName,
        rollNo: email.split('@')[0],
        role: 'student'
    })
});
```

---

## 🧪 TESTING

### Test Scenarios

1. **Register New Student**
   ```bash
   curl -X POST http://localhost:5000/api/students \
     -H "Content-Type: application/json" \
     -d '{"email":"237706p@pbsiddhartha.ac.in","admissionId":"12345","studentName":"John Doe","rollNo":"237706p"}'
   ```

2. **Check If Can Apply**
   ```bash
   curl -X POST http://localhost:5000/api/students/application-status \
     -H "Content-Type: application/json" \
     -d '{"email":"237706p@pbsiddhartha.ac.in","admissionId":"12345"}'
   ```

3. **Apply for Activity**
   ```bash
   curl -X POST http://localhost:5000/api/registrations \
     -H "Content-Type: application/json" \
     -d '{"email":"237706p@pbsiddhartha.ac.in","admissionId":"12345","studentName":"John Doe","activityName":"NCC"}'
   ```

4. **Coordinator Approve**
   ```bash
   curl -X POST http://localhost:5000/api/registrations/1/coordinator-approve \
     -H "Content-Type: application/json" \
     -d '{"action":"approve"}'
   ```

5. **HOD Approve (Final)**
   ```bash
   curl -X POST http://localhost:5000/api/registrations/1/hod-approve \
     -H "Content-Type: application/json" \
     -d '{"action":"approve"}'
   ```

---

## 📋 STATUS VALUES REFERENCE

### Overall Status (`status` field)
| Value | Meaning | Student Can Apply? |
|-------|---------|-------------------|
| `pending` | Waiting for coordinator | ❌ No |
| `coordinator_approved` | Coordinator approved, pending HOD | ❌ No |
| `hod_approved` | Fully approved (FINAL) | ❌ No (Permanent) |
| `rejected` | Rejected by coordinator or HOD | ✅ Yes |

### Coordinator Status
- `pending` - Not reviewed yet
- `approved` - Coordinator approved
- `rejected` - Coordinator rejected

### HOD Status
- `pending` - Not reviewed yet (or coordinator hasn't approved)
- `approved` - HOD approved (final approval)
- `rejected` - HOD rejected

---

## 🔍 USAGE EXAMPLES

### Example 1: Successful Application Flow
```
1. Student registers → Saved to database
2. Student applies for NCC → status: "pending"
3. Coordinator approves → status: "coordinator_approved"
4. HOD approves → status: "hod_approved" (LOCKED)
5. Student cannot apply for another activity ✓
```

### Example 2: Rejection and Reapplication
```
1. Student applies for Sports → status: "pending"
2. Coordinator rejects → status: "rejected"
3. Student can now apply for NCC → New application created
4. Coordinator approves → status: "coordinator_approved"
5. HOD approves → status: "hod_approved" (LOCKED)
```

### Example 3: Blocked Duplicate Application
```
1. Student applies for NCC → status: "pending"
2. Student tries to apply for Sports → ❌ BLOCKED
   Error: "You already have a pending application for NCC"
```

---

## 🚀 DEPLOYMENT NOTES

1. **Database Migration Required:**
   - New columns added to `registrations` table
   - Run `python backend/app.py` to auto-create tables
   - Existing registrations will have NULL values for new fields

2. **Frontend Update:**
   - Clear browser cache/localStorage
   - Registration now requires backend to be running

3. **Coordinator/HOD Panels:**
   - Need to integrate new approval endpoints
   - Use `/api/registrations/<id>/coordinator-approve`
   - Use `/api/registrations/<id>/hod-approve`

---

## ✅ VERIFICATION CHECKLIST

- [x] Student registration saves to database
- [x] Student login retrieves from database
- [x] Application status checking endpoint
- [x] One-activity-at-a-time enforcement
- [x] Coordinator approval endpoint
- [x] HOD approval endpoint
- [x] Rejection allows reapplication
- [x] Final approval locks student
- [x] Frontend calls backend API
- [x] Error handling implemented

---

## 📞 API SUMMARY

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/students` | Register new student |
| POST | `/api/auth/student` | Login student |
| POST | `/api/students/application-status` | Check if can apply |
| POST | `/api/registrations` | Apply for activity |
| POST | `/api/registrations/<id>/coordinator-approve` | Coordinator decision |
| POST | `/api/registrations/<id>/hod-approve` | HOD decision |
| GET | `/api/registrations` | Get all registrations |

---

**Implementation Date:** December 29, 2025  
**Status:** ✅ Complete and tested  
**Backend:** Flask + PostgreSQL  
**Frontend:** HTML + JavaScript (Vanilla)
