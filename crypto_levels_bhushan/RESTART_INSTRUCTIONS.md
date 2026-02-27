# 🔄 Restart Instructions

## Changes Applied

✅ **Case-insensitive email login** - Now works with any case
✅ **Password visibility toggle** - Eye button to show/hide password

## How to Apply Changes

### Step 1: Restart Backend

**Terminal 1:**
```bash
# Stop the current backend (Ctrl+C)

# Then restart:
cd crypto_levels_bhushan/backend
venv\Scripts\activate
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Restart Frontend (if needed)

**Terminal 2:**
```bash
# If frontend is running, stop it (Ctrl+C)

# Then restart:
cd crypto_levels_bhushan/frontend
npm start
```

Browser should open at `http://localhost:3000`

### Step 3: Test the Changes

1. **Test Case-Insensitive Login:**
   - Try: `bhushan.stonks@gmail.com` (lowercase)
   - Try: `BHUSHAN.STONKS@GMAIL.COM` (uppercase)
   - Try: `Bhushan.stonks@gmail.com` (original)
   - All should work! ✅

2. **Test Password Toggle:**
   - Type password in the field
   - Click the eye icon (👁️)
   - Password should become visible
   - Click again to hide
   - Works! ✅

## Quick Test

### Option 1: Test via Script
```bash
cd crypto_levels_bhushan/backend
venv\Scripts\activate
python test_case_insensitive.py
```

### Option 2: Test via Browser
1. Go to `http://localhost:3000`
2. Should redirect to `/login`
3. Enter: `bhushan.stonks@gmail.com` (lowercase)
4. Enter: `BePatient`
5. Click eye icon to verify password
6. Click "Login"
7. Should redirect to `/admin/users` ✅

## What Changed

### Backend (main.py)
```python
# Email search is now case-insensitive
{"email": {"$regex": f"^{re.escape(request.login_id)}$", "$options": "i"}}
```

### Frontend (Login.js)
```javascript
// Added password visibility toggle
const [showPassword, setShowPassword] = useState(false);

<input type={showPassword ? "text" : "password"} />
<button onClick={() => setShowPassword(!showPassword)}>
  {showPassword ? '👁️' : '👁️‍🗨️'}
</button>
```

## Credentials

**Admin Login (any case works):**
- Email: `Bhushan.stonks@gmail.com` or `bhushan.stonks@gmail.com`
- Password: `BePatient`

## Troubleshooting

### Backend not starting
```bash
# Make sure venv is activated
cd crypto_levels_bhushan/backend
venv\Scripts\activate

# Check if packages are installed
pip list | findstr bcrypt

# If missing, install
pip install -r requirements.txt

# Then start
python main.py
```

### Frontend not starting
```bash
# Make sure in frontend directory
cd crypto_levels_bhushan/frontend

# Install dependencies if needed
npm install

# Then start
npm start
```

### Login still failing
1. Check backend is running (Terminal 1)
2. Check frontend is running (Terminal 2)
3. Try lowercase email: `bhushan.stonks@gmail.com`
4. Use eye icon to verify password is correct
5. Check browser console (F12) for errors
6. Check backend terminal for error messages

### Eye icon not showing
1. Hard refresh browser (Ctrl+F5)
2. Clear browser cache
3. Check if Login.css loaded (F12 > Network tab)

## Success Indicators

✅ Backend shows: `INFO: Uvicorn running on http://0.0.0.0:8000`
✅ Frontend opens at: `http://localhost:3000`
✅ Redirects to: `http://localhost:3000/login`
✅ Can login with lowercase email
✅ Eye icon appears in password field
✅ Clicking eye shows/hides password
✅ Login redirects to `/admin/users`

---

**Ready to use!** 🎉
