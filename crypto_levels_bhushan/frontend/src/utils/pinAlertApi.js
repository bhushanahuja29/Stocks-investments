const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function authHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

export async function stopPinAlert(symbol) {
  const res = await fetch(`${API_URL}/api/pins/${encodeURIComponent(symbol)}/stop-alert`, {
    method: 'POST',
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to stop alert');
  }
  return data;
}

export async function fetchPins() {
  const res = await fetch(`${API_URL}/api/pins`, {
    headers: authHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to load pins');
  }
  return data.pins || [];
}
