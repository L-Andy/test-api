# REST Client HTTP Files

Test the TotalFit API using the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension for VS Code.

## Setup

1. **Install REST Client Extension**
   ```
   ext install humao.rest-client
   ```

2. **Start the API Server**
   ```bash
   cd c:\Users\L1169514\dev\off\api
   uvicorn main:app --reload
   ```

3. **Update Variables**
   - Each `.http` file has variables at the top (e.g., `@token`, `@baseUrl`)
   - Update these values after registration/login
   - Replace placeholder IDs with actual resource IDs after creating them

## Usage

### 1. Create Sample Users
Open [auth.http](auth.http) and run all 10 user registration requests:
- Alice Johnson (Engineering)
- Bob Smith (Engineering)
- Carol White (Marketing)
- David Brown (Marketing)
- Eva Martinez (Sales)
- Frank Lee (Sales)
- Grace Kim (HR)
- Henry Davis (Finance)
- Ivy Wilson (Product)
- Jack Taylor (Operations)

All users use password: `SecurePass123!`

See [USERS_GUIDE.md](USERS_GUIDE.md) for the complete user list and suggested group assignments.

### 2. Login and Get Token
In [auth.http](auth.http), use the login endpoints:
- Copy the `access_token` from response (if needed for authenticated endpoints)
- Copy the user `id` for profile updates

### 3. Create a Campaign
Open `campaigns.http`:
- Use **Create Campaign** (requires admin user)
- Copy the campaign `id` from response
- Update `@campaignId` variable at the top of the file

### 3. Create Groups
Open `groups.http`:
- Use **Create Group in Campaign**
- Copy the group `id` from response
- Update `@groupId` variable at the top of the file

### 4. Join a Group
Still in `groups.http`:
- Use **Join Group** endpoint

## Files

| File | Endpoints |
|------|-----------|
| `auth.http` | Register 10 users, Login endpoints |
| `users.http` | User profile management |
| `campaigns.http` | Campaign CRUD, sessions |
| `groups.http` | Group management, join groups |
| `USERS_GUIDE.md` | Quick reference for all test users |

**Note:** Each file has its own variable definitions at the top. Update them with your actual tokens and IDs.

## Authentication Flow

**Recommended: Entra ID SSO**
1. Frontend authenticates with Microsoft Entra ID
2. Frontend receives Microsoft access token
3. POST to `/users/register` with `ms_access_token`
4. Backend validates token with Microsoft Graph API
5. Backend returns user profile + JWT token
6. Use JWT token for all subsequent requests

**Alternative: Email/Password**
1. POST to `/auth/register` with email/password
2. POST to `/auth/login` to get JWT token
3. Use JWT token for all requests

## Tips

- Click "Send Request" above any `###` line
- Use `Ctrl+Alt+R` / `Cmd+Alt+R` to send rvariableName` definitions at the top of each file
- Update tokens and IDs at the top of each file`@import environment.http`
- Update IDs in `environment.local.http` as you create resources
- Admin-only endpoints require `is_admin: true` user

## API Base URL

Development: `http://localhost:8000/api/v1`

## Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `401 Unauthorized` - Invalid/missing token
- `403 Forbidden` - Not admin (for admin-only endpoints)
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate (e.g., email already registered)
- `422 Unprocessable Entity` - Validation error
