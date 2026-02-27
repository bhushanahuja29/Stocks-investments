# Authentication & Subscription Management System

## Overview
Complete user authentication and subscription management system with admin controls.

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique, required),
  mobile: String (unique, required),
  password: String (hashed with bcrypt),
  role: String (enum: ['admin', 'user']),
  name: String,
  subscription_type: String (enum: ['monthly', 'quarterly']),
  subscription_start: Date,
  subscription_end: Date,
  is_active: Boolean,
  created_at: Date,
  updated_at: Date
}
```

## Features

### Authentication
- Login with email OR mobile number + password
- JWT token-based authentication
- Password hashing with bcrypt
- Session management

### Admin Features
1. Pre-configured admin account:
   - Email: Bhushan.stonks@gmail.com
   - Password: BePatient
   - Role: admin

2. User Management:
   - Add new users
   - View all users with subscription status
   - Renew subscriptions
   - Change user passwords
   - View subscription end dates

3. Admin UI:
   - Hamburger menu in navbar
   - User management dashboard
   - Subscription renewal interface

### User Features
1. Login access only if subscription is valid
2. Auto-logout if subscription expired
3. Message: "Your subscription has expired. Please contact admin on WhatsApp to renew."

### Subscription Types
- **Monthly**: 30 days access
- **Quarterly**: 90 days access

### Subscription Validation
- Check on every protected route
- Calculate days remaining
- Auto-disable access when expired

## API Endpoints

### Auth Routes
- POST /api/auth/login - Login with email/mobile + password
- POST /api/auth/logout - Logout
- GET /api/auth/me - Get current user info
- POST /api/auth/change-password - Change own password

### Admin Routes (Protected)
- GET /api/admin/users - Get all users
- POST /api/admin/users - Add new user
- PUT /api/admin/users/:id/renew - Renew subscription
- PUT /api/admin/users/:id/password - Change user password
- DELETE /api/admin/users/:id - Delete user

### Protected Routes
- All existing routes require valid JWT + active subscription

## Implementation Files
1. Backend:
   - auth.py - Authentication logic
   - middleware.py - JWT verification & subscription check
   - admin_routes.py - Admin user management

2. Frontend:
   - Login.js - Login page
   - AdminUsers.js - User management page
   - ProtectedRoute.js - Route guard component
   - Navbar updates - Hamburger menu for admin

## Security
- Passwords hashed with bcrypt
- JWT tokens with expiration
- Role-based access control
- Subscription validation on each request
