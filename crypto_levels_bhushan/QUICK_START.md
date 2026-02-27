# Quick Start Guide - Authentication System

## What You Have Now

✅ **Backend Files Created**
- `backend/auth.py` - Authentication logic
- `backend/auth_routes.py` - Auth endpoints
- `backend/admin_routes.py` - Admin endpoints
- `backend/middleware.py` - Auth middleware
- `backend/requirements.txt` - Updated with new packages

✅ **Frontend Files Created**
- `frontend/src/pages/Login.js` + `Login.css` - Login page
- `frontend/src/pages/AdminUsers.js` + `AdminUsers.css` - User management
- `frontend/src/components/Navbar.js` + `Navbar.css` - Navigation with hamburger menu
- `frontend/src/utils/api.js` - API utility with auth headers
- `frontend/src/App.js` - Updated with authentication and protected routes

✅ **Dependencies Installed**
- bcrypt, PyJWT, python-multipart, motor (in backend venv)

## Login Page Route

**Route:** `/login`

**Behavior:**
- If user is NOT logged in → All routes redirect to `/login`
- If user IS logged in → `/login` redirects to home page
- Login page is the ONLY accessible page when not authenticated

## Quick Test

### 1. Start Backend (Terminal 1)
```bash
cd crypto_levels_bhushan/backend
venv\Scripts\activate
python main.py
```

### 2. Start Frontend (Terminal 2)
```bash
cd crypto_levels_bhushan/frontend
npm start
```

### 3. Test Login Flow
1. Open browser: `http://localhost:3000`
2. Should automatically redirect to: `http://localhost:3000/login`
3. Try to access `/monitor` → Redirects to `/login`
4. Try to access `/zone-finder` → Redirects to `/login`
5. Login with admin credentials:
   - **Email:** `Bhushan.stonks@gmail.com`
   - **Password:** `BePatient`
6. Should redirect to `/admin/users`
7. Now you can access `/monitor` and `/zone-finder`

## What Still Needs to be Done

### ⚠️ Backend Integration Required

The `main.py` file needs to be updated to integrate authentication. You have two options:

#### Option 1: Manual Integration (Recommended)
Follow the guide in `backend/MAIN_PY_CHANGES.md` to manually update `main.py`

Key changes needed:
1. Replace PyMongo with Motor (async MongoDB)
2. Add authentication middleware
3. Add auth route handlers
4. Protect existing routes with `Depends(get_current_user)`
5. Convert MongoDB operations to async

#### Option 2: Quick Integration
I can create a complete integrated `main.py` file for you that includes:
- All existing functionality (forex, indian stocks, crypto)
- Authentication system
- Protected routes
- Admin endpoints

### Frontend Updates (Optional)

The Monitor and ZoneFinder pages should use the new `api.js` utility for authenticated requests:

```javascript
// Instead of:
const response = await fetch('http://localhost:8000/api/scrips');

// Use:
import api from '../utils/api';
const data = await api.get('/api/scrips');
```

This ensures:
- Authorization header is automatically added
- Auto-logout on 401/403 errors
- Consistent error handling

## Current Route Protection

### Not Logged In
- ✅ Can access: `/login`
- ❌ Cannot access: Everything else (redirects to `/login`)

### Logged In as User
- ✅ Can access: `/monitor`, `/zone-finder`
- ❌ Cannot access: `/admin/users`
- Default page: `/monitor`

### Logged In as Admin
- ✅ Can access: Everything including `/admin/users`
- Default page: `/admin/users`
- Has hamburger menu in navbar

## Admin Credentials

```
Email: Bhushan.stonks@gmail.com
Password: BePatient
```

## User Management Features

Once logged in as admin, you can:
1. **Add Users** - Create new users with email, mobile, password
2. **Set Subscription** - Choose Monthly (30 days) or Quarterly (90 days)
3. **Renew Subscription** - Extend user access
4. **Change Password** - Reset user passwords
5. **View Status** - See days remaining, subscription status
6. **Delete Users** - Remove user access

## Subscription Management

- **Monthly**: 30 days access
- **Quarterly**: 90 days access
- Days remaining shown in navbar for users
- Warning when < 7 days remaining
- Auto-logout when subscription expires
- Message: "Your subscription has expired. Please contact admin on WhatsApp to renew."

## Next Steps

1. **Integrate Authentication into main.py**
   - Follow `backend/MAIN_PY_CHANGES.md`
   - Or ask me to create the complete integrated version

2. **Test the System**
   - Login as admin
   - Add a test user
   - Logout and login as test user
   - Verify access restrictions

3. **Update API Calls** (Optional but recommended)
   - Update Monitor.js to use `api.js` utility
   - Update ZoneFinder.js to use `api.js` utility
   - Ensures consistent auth handling

4. **Production Preparation**
   - Change SECRET_KEY in auth.py
   - Use environment variables
   - Enable HTTPS
   - Update CORS origins
   - Add rate limiting

## Troubleshooting

### "Cannot access /monitor"
- Check if logged in (token in localStorage)
- Check if subscription is active
- Check browser console for errors

### "401 Unauthorized"
- Token expired or invalid
- Should auto-redirect to login
- Try logging in again

### "403 Forbidden - Subscription expired"
- User subscription has ended
- Contact admin to renew
- Admin can renew from `/admin/users`

### Backend not starting
- Check if venv is activated
- Check if all packages installed: `pip install -r requirements.txt`
- Check if MongoDB connection works

### Frontend not starting
- Check if node_modules installed: `npm install`
- Check if backend is running
- Check API_URL in code

## Files Reference

- **Routes Guide**: `ROUTES_GUIDE.md` - Complete route documentation
- **Auth Plan**: `AUTHENTICATION_PLAN.md` - System architecture
- **Implementation**: `AUTHENTICATION_IMPLEMENTATION.md` - Detailed guide
- **Main.py Changes**: `backend/MAIN_PY_CHANGES.md` - Integration steps
- **Complete Summary**: `AUTHENTICATION_COMPLETE.md` - Full overview

## Need Help?

If you want me to:
1. Create the complete integrated main.py file
2. Update Monitor/ZoneFinder to use api.js utility
3. Add more features

Just ask!
