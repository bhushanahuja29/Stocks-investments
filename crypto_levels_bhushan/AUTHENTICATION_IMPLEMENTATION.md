# Authentication System Implementation Guide

## Overview
Complete authentication and subscription management system with admin controls.

## Backend Implementation

### 1. Install Required Packages
```bash
cd crypto_levels_bhushan/backend
pip install bcrypt pyjwt python-multipart motor
```

### 2. Update requirements.txt
Add these lines:
```
bcrypt==4.1.2
PyJWT==2.8.0
python-multipart==0.0.6
motor==3.3.2
```

### 3. Update main.py

Add these imports at the top:
```python
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
```

Replace MongoDB client initialization with Motor (async):
```python
# MongoDB Configuration (Async)
motor_client = None
motor_db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global motor_client, motor_db
    motor_client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    motor_db = motor_client[DB_NAME]
    
    # Create admin user if doesn't exist
    from .auth import create_admin_if_not_exists
    await create_admin_if_not_exists(motor_db)
    
    print("✅ Database connected and admin user initialized")
    
    yield
    
    # Shutdown
    motor_client.close()
    print("✅ Database connection closed")

# Update FastAPI app initialization
app = FastAPI(
    title="Crypto Levels API",
    version="2.0.0",
    lifespan=lifespan
)
```

Add dependency injection for database:
```python
from fastapi import Depends

async def get_db():
    return motor_db

# Include auth routes
from .auth_routes import router as auth_router
from .admin_routes import router as admin_router

auth_router_with_db = APIRouter()
admin_router_with_db = APIRouter()

# Wrap routes to inject db
@auth_router_with_db.post("/api/auth/login")
async def login_endpoint(request, db = Depends(get_db)):
    from .auth_routes import login
    return await login(request, db)

# ... similar for other routes

app.include_router(auth_router)
app.include_router(admin_router)
```

### 4. Protect Existing Routes

Add authentication to existing routes:
```python
from .middleware import get_current_user

@app.post("/api/zones/search")
async def search_zones(
    request: ZoneSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    # ... existing code
```

## Frontend Implementation

### 1. Create Login Page

File: `frontend/src/pages/Login.js`
```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login({ setUser }) {
  const [loginId, setLoginId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login_id: loginId, password })
      });

      const data = await response.json();

      if (data.success) {
        // Store token and user
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        
        // Redirect based on role
        if (data.user.role === 'admin') {
          navigate('/admin/users');
        } else {
          navigate('/monitor');
        }
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError(err.message || 'Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Delta Levels Tracker</h1>
        <h2>Login</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Email or Mobile</label>
            <input
              type="text"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="Enter email or mobile number"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
```

### 2. Create Admin Users Page

File: `frontend/src/pages/AdminUsers.js`
```jsx
import React, { useState, useEffect } from 'react';
import './AdminUsers.css';

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState({
    email: '',
    mobile: '',
    password: '',
    name: '',
    subscription_type: 'monthly'
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('http://localhost:8000/api/admin/users', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    if (data.success) {
      setUsers(data.users);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    
    const response = await fetch('http://localhost:8000/api/admin/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(newUser)
    });

    const data = await response.json();
    if (data.success) {
      alert('User added successfully!');
      setShowAddUser(false);
      setNewUser({ email: '', mobile: '', password: '', name: '', subscription_type: 'monthly' });
      fetchUsers();
    } else {
      alert(data.detail || 'Failed to add user');
    }
  };

  const handleRenew = async (userId, subscriptionType) => {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`http://localhost:8000/api/admin/users/${userId}/renew`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ subscription_type: subscriptionType })
    });

    const data = await response.json();
    if (data.success) {
      alert(`Subscription renewed! Valid for ${data.days} days`);
      fetchUsers();
    }
  };

  const handleChangePassword = async (userId) => {
    const newPassword = prompt('Enter new password:');
    if (!newPassword) return;

    const token = localStorage.getItem('token');
    
    const response = await fetch(`http://localhost:8000/api/admin/users/${userId}/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ new_password: newPassword })
    });

    const data = await response.json();
    if (data.success) {
      alert('Password changed successfully!');
    }
  };

  return (
    <div className="admin-users">
      <div className="admin-header">
        <h1>User Management</h1>
        <button onClick={() => setShowAddUser(true)}>+ Add User</button>
      </div>

      {showAddUser && (
        <div className="modal">
          <div className="modal-content">
            <h2>Add New User</h2>
            <form onSubmit={handleAddUser}>
              <input
                type="text"
                placeholder="Name"
                value={newUser.name}
                onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={newUser.email}
                onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Mobile"
                value={newUser.mobile}
                onChange={(e) => setNewUser({...newUser, mobile: e.target.value})}
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={newUser.password}
                onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                required
              />
              <select
                value={newUser.subscription_type}
                onChange={(e) => setNewUser({...newUser, subscription_type: e.target.value})}
              >
                <option value="monthly">Monthly (30 days)</option>
                <option value="quarterly">Quarterly (90 days)</option>
              </select>
              <div className="modal-buttons">
                <button type="submit">Add User</button>
                <button type="button" onClick={() => setShowAddUser(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <table className="users-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Mobile</th>
            <th>Subscription</th>
            <th>Status</th>
            <th>Days Remaining</th>
            <th>End Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.mobile}</td>
              <td>{user.subscription_type}</td>
              <td className={user.subscription_status}>
                {user.subscription_status}
              </td>
              <td>{user.days_remaining}</td>
              <td>{user.subscription_end ? new Date(user.subscription_end).toLocaleDateString() : 'N/A'}</td>
              <td>
                <div className="action-buttons">
                  <select onChange={(e) => {
                    if (e.target.value) {
                      handleRenew(user.id, e.target.value);
                      e.target.value = '';
                    }
                  }}>
                    <option value="">Renew...</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                  </select>
                  <button onClick={() => handleChangePassword(user.id)}>
                    Change Password
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AdminUsers;
```

### 3. Update App.js with Routes

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Login from './pages/Login';
import AdminUsers from './pages/AdminUsers';
import Monitor from './pages/Monitor';
import ZoneFinder from './pages/ZoneFinder';
import Navbar from './components/Navbar';

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (!user) {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Navbar user={user} onLogout={handleLogout} />
      <Routes>
        {user.role === 'admin' ? (
          <>
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/monitor" element={<Monitor />} />
            <Route path="/zone-finder" element={<ZoneFinder />} />
            <Route path="*" element={<Navigate to="/admin/users" />} />
          </>
        ) : (
          <>
            <Route path="/monitor" element={<Monitor />} />
            <Route path="/zone-finder" element={<ZoneFinder />} />
            <Route path="*" element={<Navigate to="/monitor" />} />
          </>
        )}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### 4. Create Navbar with Hamburger Menu

File: `frontend/src/components/Navbar.js`
```jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar({ user, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h2>Delta Levels</h2>
      </div>

      {user.role === 'admin' && (
        <button 
          className="hamburger"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>
      )}

      <div className={`navbar-menu ${menuOpen ? 'open' : ''}`}>
        <Link to="/monitor" onClick={() => setMenuOpen(false)}>Monitor</Link>
        <Link to="/zone-finder" onClick={() => setMenuOpen(false)}>Zone Finder</Link>
        {user.role === 'admin' && (
          <Link to="/admin/users" onClick={() => setMenuOpen(false)}>Users</Link>
        )}
        <div className="user-info">
          <span>{user.name}</span>
          {user.role !== 'admin' && user.days_remaining !== undefined && (
            <span className="days-remaining">
              {user.days_remaining} days left
            </span>
          )}
        </div>
        <button onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}

export default Navbar;
```

## Testing

### 1. Start Backend
```bash
cd crypto_levels_bhushan/backend
python main.py
```

### 2. Test Admin Login
- Email: Bhushan.stonks@gmail.com
- Password: BePatient

### 3. Add Test User
- Go to Admin > Users
- Click "Add User"
- Fill in details and select subscription type

### 4. Test User Login
- Logout
- Login with test user credentials
- Verify access expires after subscription period

## Security Notes

1. Change SECRET_KEY in auth.py before production
2. Use HTTPS in production
3. Store sensitive data in environment variables
4. Implement rate limiting on login endpoint
5. Add password strength requirements
6. Consider adding 2FA for admin account

## Next Steps

1. Add email notifications for subscription expiry
2. Add payment gateway integration
3. Add subscription auto-renewal
4. Add audit logs for admin actions
5. Add user activity tracking
