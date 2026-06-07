import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ZoneFinder from './pages/ZoneFinder';
import Monitor from './pages/Monitor';
import MonitorPremium from './pages/Monitor_Premium';
import Login from './pages/Login';
import AdminUsers from './pages/AdminUsers';
import PinAlerts from './pages/PinAlerts';
import TradingViewAlerts from './pages/TradingViewAlerts';
import Navbar from './components/Navbar';
import PwaShell from './components/PwaShell';
import PinAlertSoundWatcher from './components/PinAlertSoundWatcher';
import { ensurePushSubscription } from './utils/pushNotifications';
import { registerAlertSoundListener, unlockAlertSound } from './utils/alertSound';
import './App.css';
import './App_Premium.css';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshNavbar, setRefreshNavbar] = useState(0);

  // Check if user is logged in on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  // Re-sync push subscription when PWA reopens (cold start drops server registration)
  useEffect(() => {
    if (!user) return undefined;
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') {
      return undefined;
    }
    ensurePushSubscription().catch(() => undefined);
    return undefined;
  }, [user]);

  // Play alert sound when a push notification arrives while the app is open
  useEffect(() => {
    if (!user) return undefined;
    return registerAlertSoundListener();
  }, [user]);

  // Unlock Web Audio after first tap (browser autoplay policy)
  useEffect(() => {
    if (!user) return undefined;
    const unlock = () => unlockAlertSound();
    window.addEventListener('click', unlock, { once: true });
    window.addEventListener('touchstart', unlock, { once: true });
    window.addEventListener('keydown', unlock, { once: true });
    return () => {
      window.removeEventListener('click', unlock);
      window.removeEventListener('touchstart', unlock);
      window.removeEventListener('keydown', unlock);
    };
  }, [user]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const triggerNavbarRefresh = () => {
    setRefreshNavbar(prev => prev + 1);
  };

  // Show loading state
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Loading...
      </div>
    );
  }

  // If not logged in, show login with PWA install shell
  if (!user) {
    return (
      <Router>
        <PwaShell />
        <Routes>
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    );
  }

  // If logged in, show app with navbar
  return (
    <Router>
      <div className="App">
        <Navbar user={user} onLogout={handleLogout} refreshTrigger={refreshNavbar} />
        <PwaShell />
        <PinAlertSoundWatcher />
        <Routes>
          {/* Admin routes */}
          {user.role === 'admin' && (
            <Route path="/admin/users" element={<AdminUsers />} />
          )}
          
          {/* User routes */}
          <Route path="/zone-finder" element={<ZoneFinder />} />
          <Route path="/monitor" element={<MonitorPremium onNavbarRefresh={triggerNavbarRefresh} />} />
          <Route path="/monitor-classic" element={<Monitor onNavbarRefresh={triggerNavbarRefresh} />} />
          <Route path="/pins" element={<PinAlerts user={user} />} />
          <Route path="/alerts" element={<TradingViewAlerts />} />
          
          {/* Default redirect based on role */}
          <Route 
            path="/" 
            element={
              user.role === 'admin' 
                ? <Navigate to="/admin/users" replace /> 
                : <Navigate to="/monitor" replace />
            } 
          />
          
          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

