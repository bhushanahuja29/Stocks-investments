# Application Routes Guide

## Frontend Routes

### Public Routes (No Authentication Required)
- `/login` - Login page (email or mobile + password)

### Protected Routes (Authentication Required)

#### User Routes (All authenticated users)
- `/monitor` - Monitor page (Premium version with real-time tracking)
- `/zone-finder` - Zone Finder page (Search and add support zones)
- `/monitor-classic` - Classic monitor view

#### Admin Routes (Admin role only)
- `/admin/users` - User management dashboard

### Route Behavior

#### Not Logged In
- All routes redirect to `/login`
- Only `/login` page is accessible

#### Logged In as User
- Default redirect: `/monitor`
- Can access: `/monitor`, `/zone-finder`, `/monitor-classic`
- Cannot access: `/admin/users`

#### Logged In as Admin
- Default redirect: `/admin/users`
- Can access: All routes including `/admin/users`
- Has hamburger menu in navbar

### Auto-Logout Scenarios
User will be automatically logged out and redirected to `/login` if:
1. JWT token expires (24 hours)
2. Subscription expires (for non-admin users)
3. API returns 401 or 403 error
4. User clicks Logout button

## Backend API Routes

### Public Endpoints (No Authentication)
- `GET /` - API info
- `GET /api/health` - Health check

### Authentication Endpoints
- `POST /api/auth/login` - Login (returns JWT token)
  ```json
  {
    "login_id": "email@example.com or 9876543210",
    "password": "password"
  }
  ```
- `GET /api/auth/me` - Get current user info (requires token)
- `POST /api/auth/change-password` - Change own password (requires token)
- `POST /api/auth/logout` - Logout (client-side token removal)

### Admin Endpoints (Requires Admin Role)
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create new user
  ```json
  {
    "email": "user@example.com",
    "mobile": "9876543210",
    "password": "password",
    "name": "User Name",
    "subscription_type": "monthly" // or "quarterly"
  }
  ```
- `PUT /api/admin/users/:id/renew` - Renew subscription
  ```json
  {
    "subscription_type": "monthly" // or "quarterly"
  }
  ```
- `PUT /api/admin/users/:id/password` - Change user password
  ```json
  {
    "new_password": "newpassword"
  }
  ```
- `DELETE /api/admin/users/:id` - Delete user

### Protected Endpoints (Requires Valid Subscription)
- `POST /api/zones/search` - Search for support zones
- `POST /api/zones/push` - Push zones to monitoring
- `GET /api/scrips` - Get all monitored scrips
- `GET /api/price/:symbol` - Get current price
- `PUT /api/scrips/:symbol/alert` - Update alert status
- `DELETE /api/scrips/:symbol` - Delete scrip
- `GET /api/usage` - Get API usage stats

## Authentication Flow

### Login Flow
1. User enters email/mobile + password on `/login`
2. Frontend sends POST to `/api/auth/login`
3. Backend validates credentials and subscription
4. Backend returns JWT token + user data
5. Frontend stores token in localStorage
6. Frontend redirects based on role:
   - Admin → `/admin/users`
   - User → `/monitor`

### API Request Flow
1. Frontend makes API request
2. Frontend includes `Authorization: Bearer <token>` header
3. Backend validates token
4. Backend checks subscription status (for non-admin)
5. Backend processes request or returns error

### Logout Flow
1. User clicks Logout button
2. Frontend removes token from localStorage
3. Frontend redirects to `/login`

### Auto-Logout Flow
1. API returns 401/403 error
2. Frontend detects unauthorized response
3. Frontend removes token from localStorage
4. Frontend redirects to `/login`
5. User sees message: "Your subscription has expired. Please contact admin on WhatsApp to renew."

## Using the API Utility

Import the API utility in your components:

```javascript
import api from '../utils/api';

// GET request
const data = await api.get('/api/scrips');

// POST request
const result = await api.post('/api/zones/search', {
  symbol: 'BTCUSD',
  timeframe: '1w'
});

// PUT request
await api.put('/api/scrips/BTCUSD/alert', {
  level_index: 0,
  disabled: true
});

// DELETE request
await api.delete('/api/scrips/BTCUSD');
```

The utility automatically:
- Adds Authorization header with token
- Handles 401/403 errors (auto-logout)
- Redirects to login if unauthorized

## Testing Routes

### Test Login
1. Start backend: `python main.py`
2. Start frontend: `npm start`
3. Navigate to `http://localhost:3000`
4. Should redirect to `http://localhost:3000/login`
5. Login with admin credentials:
   - Email: `Bhushan.stonks@gmail.com`
   - Password: `BePatient`
6. Should redirect to `http://localhost:3000/admin/users`

### Test Protected Routes
1. While logged in, navigate to `/monitor`
2. Should show monitor page
3. Open DevTools Network tab
4. Verify API requests include `Authorization: Bearer ...` header

### Test Auto-Logout
1. Clear localStorage in DevTools
2. Try to navigate to `/monitor`
3. Should redirect to `/login`

### Test Subscription Expiry
1. Create a test user with expired subscription
2. Login as that user
3. Should see error: "Your subscription has expired..."
4. Should not be able to access protected routes

## Route Protection Summary

| Route | Public | User | Admin |
|-------|--------|------|-------|
| `/login` | ✅ | ✅ | ✅ |
| `/monitor` | ❌ | ✅ | ✅ |
| `/zone-finder` | ❌ | ✅ | ✅ |
| `/admin/users` | ❌ | ❌ | ✅ |

✅ = Accessible
❌ = Redirects to login or home

## Notes

- Login page route: `/login`
- All other routes require authentication
- Token stored in localStorage
- Token expires after 24 hours
- Subscription checked on every API request
- Admin has access to all routes
- Users only see Monitor and Zone Finder in navbar
- Admin sees hamburger menu with Users option
