### Quick Start Guide - Create 10 Users

This file contains quick commands to create all 10 sample users for testing.

**Base URL:** http://localhost:8000/api/v1

---

## Step 1: Create All Users (Run in Order)

All users use password: `SecurePass123!`

### Users by Department:

**Engineering Team:**
- alice.johnson@company.com - Alice Johnson
- bob.smith@company.com - Bob Smith

**Marketing Team:**
- carol.white@company.com - Carol White  
- david.brown@company.com - David Brown

**Sales Team:**
- eva.martinez@company.com - Eva Martinez
- frank.lee@company.com - Frank Lee

**HR Team:**
- grace.kim@company.com - Grace Kim

**Finance Team:**
- henry.davis@company.com - Henry Davis

**Product Team:**
- ivy.wilson@company.com - Ivy Wilson

**Operations Team:**
- jack.taylor@company.com - Jack Taylor

---

## Step 2: Login and Get User IDs

After creating users, login with each to get their user IDs:

```http
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "alice.johnson@company.com",
  "password": "SecurePass123!"
}
```

Copy the user `id` from each login response.

---

## Step 3: Update Profiles with Avatars

Use the PATCH `/users/me?user_id={id}` endpoint to add avatars.

Avatar URLs use DiceBear API:
- `https://api.dicebear.com/7.x/avataaars/svg?seed=Alice`
- `https://api.dicebear.com/7.x/avataaars/svg?seed=Bob`
- etc.

---

## User List (for reference)

| # | Name | Email | Department |
|---|------|-------|------------|
| 1 | Alice Johnson | alice.johnson@company.com | Engineering |
| 2 | Bob Smith | bob.smith@company.com | Engineering |
| 3 | Carol White | carol.white@company.com | Marketing |
| 4 | David Brown | david.brown@company.com | Marketing |
| 5 | Eva Martinez | eva.martinez@company.com | Sales |
| 6 | Frank Lee | frank.lee@company.com | Sales |
| 7 | Grace Kim | grace.kim@company.com | HR |
| 8 | Henry Davis | henry.davis@company.com | Finance |
| 9 | Ivy Wilson | ivy.wilson@company.com | Product |
| 10 | Jack Taylor | jack.taylor@company.com | Operations |

---

## Suggested Group Assignments

When creating groups in campaigns:

**Group 1 - Engineering:**
- Alice Johnson
- Bob Smith

**Group 2 - Marketing & Sales:**
- Carol White
- David Brown
- Eva Martinez
- Frank Lee

**Group 3 - Support Functions:**
- Grace Kim (HR)
- Henry Davis (Finance)

**Group 4 - Product & Ops:**
- Ivy Wilson
- Jack Taylor
