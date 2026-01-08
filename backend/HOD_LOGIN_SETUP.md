# HOD Login & Access Control System (Unified)

## Overview

The HOD login and access control system has been migrated to a new, unified user management system. This system is database-driven and managed through the main Flask application (`app.py`). The old system based on CSV files and a custom authentication manager is now obsolete.

## Key Changes

-   **Unified User Table**: All users, including HODs, are stored in the `users` table in the database.
-   **Role-Based Access Control (RBAC)**: User roles (including 'HOD') are defined in the `roles` table.
-   **Creator-Managed Accounts**: HOD accounts are created by a user with the 'CREATOR' role.
-   **Centralized Authentication**: All logins are handled by the `/api/auth/login` endpoint.
-   **Profile Completion**: HODs must complete their profile and set a new password on their first login.

## Integration

The HOD authentication and authorization is now fully integrated into the main application (`app.py`). No separate authentication files or configurations are needed.

### Key Components in `app.py`:

1.  **SQLAlchemy Models**:
    -   `User`: Represents a user in the system.
    -   `Role`: Defines user roles.
    -   `Department`: Defines academic departments.

2.  **Authentication Endpoints**:
    -   `POST /api/auth/login`: Handles login for all user types.
    -   `POST /api/auth/logout`: Handles user logout.
    -   `GET /api/auth/me`: Retrieves the current logged-in user's information.

3.  **Decorators for Security**:
    -   `@require_role('HOD')`: A decorator that can be used to protect routes, ensuring that only users with the 'HOD' role can access them.

## API Endpoints

### POST /api/auth/login

**Request:**

```json
{
  "email": "hod.email@example.com",
  "password": "your_password"
}
```

**Response (Successful Login):**

```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "hod.email@example.com",
    "fullName": "HOD Name",
    "role": "HOD",
    ...
  },
  "requiresProfileCompletion": true
}
```

### GET /api/auth/me

-   **Requires**: A valid session cookie.
-   **Returns**: The currently logged-in user's profile information.

### PUT /api/profile/update

-   **Requires**: A valid session cookie.
-   **Used for**: First-time profile completion and password change.

## Security Features

-   **Password Hashing**: Passwords are securely hashed using `bcrypt`.
-   **Role-Based Access Control**: Routes are protected based on user roles.
-   **Session Management**: Secure, server-side sessions are used to track authenticated users.
-   **Centralized User Management**: All user data is stored and managed in a central database, eliminating the risks associated with scattered CSV files.

## Production Enhancements

1.  **Password Security**:
    -   Password strength requirements are enforced on the frontend and backend.
    -   The system forces a password change on the first login.

2.  **Session Security**:
    -   Session cookies are configured with `HttpOnly` and `SameSite='Lax'` attributes.
    -   A permanent session lifetime is set.

3.  **Audit Logging**:
    -   (Recommended) Implement a logging mechanism to track significant events, such as logins, profile changes, and administrative actions.

## Testing

-   **HOD Account Creation**: Use the "Creator" dashboard to create a new HOD account.
-   **First-Time Login**: Log in with the temporary credentials provided. You should be redirected to the profile completion page.
-   **Profile Update**: Complete the profile and set a new password.
-   **Subsequent Logins**: Log in with the new password. You should be redirected to the HOD dashboard.
-   **Access Control**: Attempt to access non-HOD routes. Access should be denied.
