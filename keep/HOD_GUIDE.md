# HOD Guide: Departments and Workflow

This guide provides an overview of the Head of Department (HOD) role, including department details and the primary workflow within the system.

## Departments & Access Codes

HODs have access restricted to the students within their own department. The system uses the following department codes and names for filtering:

| Department Name         | Department Code | Access Filter/Code |
| ----------------------- | --------------- | ------------------ |
| Economics               | ECO             | `pcode 11`         |
| English                 | ENG             | `dept = 'ENG'`     |
| Telugu                  | TEL             | `dept = 'TEL'`     |
| Commerce                | COM             | `pcode 21-28`      |
| Computer Science        | CSC             | `pcode 41, 42, 71, 72, 73, 76` |
| Mathematics             | MAT             | `pcode 61`         |
| Chemistry               | CHE             | `pcode 62`         |
| Physics                 | PHY             | `pcode 63`         |
| Statistics              | STA             | `pcode 65`         |
| Electronics             | ELE             | `pcode 64`         |
| Botany                  | BOT             | `pcode 51`         |
| Zoology                 | ZOO             | `pcode 52`         |
| Data Science & AI       | DSAI            | `pcode 74, 75, 77` |

## HOD Workflow and Logic

The HOD role is crucial for the final approval of student activity registrations. Here is a breakdown of the HOD's workflow and responsibilities.

### 1. Authentication

*   HODs log in through a dedicated login page using their email and password.
*   The system uses a unified authentication endpoint (`/api/auth/login`) that verifies the user's credentials and their assigned role.
*   Upon successful login, a session is created, and the HOD is redirected to their dashboard.

### 2. Authorization and Access Control

*   **Department-Level Isolation**: The system is designed to ensure that HODs can only view and manage students and registrations belonging to their own department. This is enforced by backend decorators (`@hod_auth.hod_department_access` in the original design, now integrated into the unified user system).
*   **Role-Based Permissions**: HODs have specific permissions that allow them to perform actions such as approving registrations and viewing analytics. These are defined in the Role-Based Access Control (RBAC) configuration.

### 3. Core Functionality

#### a. Student Application Approval Process

The primary function of the HOD is to be the final approver in the student activity registration workflow.

1.  **Student Applies**: A student registers for an activity. The application status is `pending`.
2.  **Coordinator Approval**: The application is first sent to the relevant Activity Coordinator. If the coordinator approves, the status changes to `coordinator_approved`.
3.  **HOD Approval**: After coordinator approval, the application appears in the HOD's approval queue. The HOD can then:
    *   **Approve**: The HOD approves the registration. The status changes to `hod_approved`. The student is now officially enrolled in the activity, and the slot is marked as filled.
    *   **Reject**: The HOD rejects the registration. The status changes to `rejected`, and the student is notified. The reason for rejection can be recorded.

This logic is handled by the `/api/registrations/<int:reg_id>/hod-approve` endpoint in `backend/app.py`.

#### b. Viewing Department Data

HODs have access to dashboards and analytics that are automatically filtered for their department.

*   **Student Records**: HODs can view a list of all students enrolled in their department.
*   **Department Analytics**: HODs can view statistics for their department, such as the distribution of students across different activities. This is handled by the `/api/analytics/department/<department>` endpoint.
*   **Approval Queues**: The HOD panel includes a queue of pending student applications that require their attention.

This ensures that HODs have a comprehensive overview of their students' engagement in extracurricular activities while maintaining data privacy and a clear separation of duties.
