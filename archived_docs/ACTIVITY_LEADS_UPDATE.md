# Auto-Fill Form Fields Update - Activity Lead Information

## Overview
Updated the course registration form (Page 2) to automatically fetch and populate:
- **Incharge Name** = Activity Head Name
- **Coordinator Name** = Sub-Activity Lead Name  
- **HOD Details** = From database

## Changes Made

### 1. Database Schema Update
**File**: `backend/app.py` - SubActivity Model

Added 4 new columns to the `sub_activities` table:
- `sub_activity_lead_name` (VARCHAR 255) - Name of the sub-activity lead/coordinator
- `sub_activity_lead_phone` (VARCHAR 20) - Phone of the sub-activity lead
- `activity_head_name` (VARCHAR 255) - Name of the main activity head
- `activity_head_phone` (VARCHAR 20) - Phone of the activity head

**Migration**: `004_add_activity_lead_fields.sql` and `004_add_activity_lead_fields.py`

### 2. API Endpoint Update
**File**: `backend/app.py` - PUT /api/sub-activities/<int:sub_id>

Updated the endpoint to handle the new fields when updating sub-activities:
```python
if 'subActivityLeadName' in payload:
    sub.sub_activity_lead_name = payload['subActivityLeadName']
if 'subActivityLeadPhone' in payload:
    sub.sub_activity_lead_phone = payload['subActivityLeadPhone']
if 'activityHeadName' in payload:
    sub.activity_head_name = payload['activityHeadName']
if 'activityHeadPhone' in payload:
    sub.activity_head_phone = payload['activityHeadPhone']
```

### 3. Frontend Changes
**File**: `web/pages/student/course-details.html`

#### New Function: `fetchSubActivityDetails()`
- Fetches sub-activity data from `/api/sub-activities/{id}` endpoint
- Auto-populates all 4 contact fields:
  - Incharge Name & Phone (Activity Head)
  - Coordinator Name & Phone (Sub-Activity Lead)

#### Updated: `selectSubActivity()`
- Now calls `fetchSubActivityDetails()` when a sub-activity is selected
- Automatically fills in all lead information from the database
- Falls back gracefully if data is unavailable

### 4. Data Seeding
**File**: `backend/seed_activity_leads.py`

Script to populate the new fields with sample data for all activities:
- SPORTS: Cricket, Football, Badminton, Table Tennis, Basketball
- NCC: Army Wing, Naval Wing, Air Wing
- YOGA: Hatha Yoga, Power Yoga
- GYM: Strength Training, Cardio
- GOOD HABITS CLUB: Meditation, Reading
- NSS: Community Service, Environmental Drive
- CULTURALS: Dance, Music, Drama

## How to Use

### 1. Run the Migration (if needed)
```bash
python backend/004_add_activity_lead_fields.py
```

### 2. Seed Sample Data
```bash
python backend/seed_activity_leads.py
```

Output:
```
🔄 Seeding activity lead information...
  ✓ SPORTS → Cricket
    Head: Dr. Kavya Sharma
    Lead: Mr. Rajesh Kumar
  ...
✅ Seeding completed!
   Updated: 15/15 sub-activities
```

### 3. Test in the Form
1. Navigate to Course Registration Page 2 (course-details.html)
2. Select an activity from available slots
3. The form will automatically fetch and display:
   - **Incharge Name**: Activity Head Name (auto-filled, editable)
   - **Incharge Mobile**: Activity Head Phone (auto-filled, editable)
   - **Coordinator Name (Auto)**: Sub-Activity Lead Name (readonly)
   - **Coordinator Phone (Auto)**: Sub-Activity Lead Phone (readonly)
   - **HOD Name (Auto)**: Department HOD (readonly)
   - **HOD Phone (Auto)**: HOD Phone (readonly)

## Form Field Behavior

| Field | Source | Editable | Auto-Fill |
|-------|--------|----------|-----------|
| Incharge Name | Activity Head | ✓ Yes | ✓ Yes |
| Incharge Mobile | Activity Head Phone | ✓ Yes | ✓ Yes |
| Coordinator Name | Sub-Activity Lead | ✗ No | ✓ Yes |
| Coordinator Phone | Sub-Activity Lead Phone | ✗ No | ✓ Yes |
| HOD Name | Department HOD | ✗ No | ✓ Yes |
| HOD Phone | Department HOD Phone | ✗ No | ✓ Yes |

## API Response Example

When fetching `/api/sub-activities/1`:
```json
{
  "id": 1,
  "activityName": "SPORTS",
  "subActivityName": "Cricket",
  "activityHeadName": "Dr. Kavya Sharma",
  "activityHeadPhone": "+91 98765 43210",
  "subActivityLeadName": "Mr. Rajesh Kumar",
  "subActivityLeadPhone": "+91 98765 43211",
  "totalSlots": 30,
  "filledSlots": 15,
  "availableSlots": 15,
  "isFull": false
}
```

## Future Enhancements
- Store PDF/CV links for HOD and activity leads
- Update admin panel to manage these fields
- Add validation for phone numbers
- Support for multiple contact persons per activity
