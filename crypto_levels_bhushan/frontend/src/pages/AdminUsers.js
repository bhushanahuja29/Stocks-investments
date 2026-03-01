import React, { useState, useEffect } from 'react';
import './AdminUsers.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [showAddUser, setShowAddUser] = useState(false);
  const [loading, setLoading] = useState(false);
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
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (data.success) {
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      alert('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${API_URL}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newUser)
      });

      const data = await response.json();
      if (data.success) {
        alert(`User added successfully! Subscription valid for ${data.days} days`);
        setShowAddUser(false);
        setNewUser({ email: '', mobile: '', password: '', name: '', subscription_type: 'monthly' });
        fetchUsers();
      } else {
        alert(data.detail || 'Failed to add user');
      }
    } catch (error) {
      console.error('Error adding user:', error);
      alert('Failed to add user');
    }
  };

  const handleRenew = async (userId, subscriptionType) => {
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${userId}/renew`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ subscription_type: subscriptionType })
      });

      const data = await response.json();
      if (data.success) {
        alert(`✅ Subscription renewed! Valid for ${data.days} days`);
        fetchUsers();
      } else {
        alert(data.detail || 'Failed to renew subscription');
      }
    } catch (error) {
      console.error('Error renewing subscription:', error);
      alert('Failed to renew subscription');
    }
  };

  const handleChangePassword = async (userId, userEmail) => {
    const newPassword = prompt(`Enter new password for ${userEmail}:`);
    if (!newPassword) return;

    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${userId}/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ new_password: newPassword })
      });

      const data = await response.json();
      if (data.success) {
        alert('✅ Password changed successfully!');
      } else {
        alert(data.detail || 'Failed to change password');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      alert('Failed to change password');
    }
  };

  const handleDeleteUser = async (userId, userEmail) => {
    if (!window.confirm(`Are you sure you want to delete user ${userEmail}?`)) return;

    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      if (data.success) {
        alert('✅ User deleted successfully!');
        fetchUsers();
      } else {
        alert(data.detail || 'Failed to delete user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Failed to delete user');
    }
  };

  return (
    <div className="admin-users">
      <div className="admin-header">
        <div>
          <h1>👥 User Management</h1>
          <p>Manage user subscriptions and access</p>
        </div>
        <button className="add-user-btn" onClick={() => setShowAddUser(true)}>
          + Add User
        </button>
      </div>

      {showAddUser && (
        <div className="modal-overlay" onClick={() => setShowAddUser(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add New User</h2>
            <form onSubmit={handleAddUser}>
              <div className="form-row">
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={newUser.name}
                    onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    placeholder="email@example.com"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    required
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Mobile *</label>
                  <input
                    type="text"
                    placeholder="9876543210"
                    value={newUser.mobile}
                    onChange={(e) => setNewUser({...newUser, mobile: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Password *</label>
                  <input
                    type="password"
                    placeholder="Password"
                    value={newUser.password}
                    onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Subscription Type *</label>
                <select
                  value={newUser.subscription_type}
                  onChange={(e) => setNewUser({...newUser, subscription_type: e.target.value})}
                >
                  <option value="monthly">Monthly (30 days)</option>
                  <option value="quarterly">Quarterly (90 days)</option>
                </select>
              </div>

              <div className="modal-buttons">
                <button type="submit" className="btn-primary">Add User</button>
                <button type="button" className="btn-secondary" onClick={() => setShowAddUser(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>Subscription</th>
                <th>Status</th>
                <th>Days Left</th>
                <th>End Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{textAlign: 'center', padding: '40px'}}>
                    No users found. Add your first user!
                  </td>
                </tr>
              ) : (
                users.map(user => (
                  <tr key={user.id}>
                    <td>{user.name}</td>
                    <td>{user.email}</td>
                    <td>{user.mobile}</td>
                    <td>
                      <span className="subscription-badge">
                        {user.subscription_type}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${user.subscription_status}`}>
                        {user.subscription_status}
                      </span>
                    </td>
                    <td>
                      <span className={user.days_remaining <= 7 ? 'days-warning' : ''}>
                        {user.days_remaining} days
                      </span>
                    </td>
                    <td>
                      {user.subscription_end 
                        ? new Date(user.subscription_end).toLocaleDateString()
                        : 'N/A'
                      }
                    </td>
                    <td>
                      <div className="action-buttons">
                        <select 
                          className="renew-select"
                          onChange={(e) => {
                            if (e.target.value) {
                              handleRenew(user.id, e.target.value);
                              e.target.value = '';
                            }
                          }}
                        >
                          <option value="">Renew...</option>
                          <option value="monthly">Monthly</option>
                          <option value="quarterly">Quarterly</option>
                        </select>
                        <button 
                          className="btn-small"
                          onClick={() => handleChangePassword(user.id, user.email)}
                          title="Change Password"
                        >
                          🔑
                        </button>
                        <button 
                          className="btn-small btn-danger"
                          onClick={() => handleDeleteUser(user.id, user.email)}
                          title="Delete User"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminUsers;
