/**
 * API Utility Functions
 * Handles authenticated API calls with token management
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Get authorization headers with token
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * Handle API errors and logout if unauthorized
 */
export const handleApiError = (error) => {
  if (error.response?.status === 401 || error.response?.status === 403) {
    // Token expired or invalid - logout
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }
  throw error;
};

/**
 * Make authenticated GET request
 */
export const apiGet = async (endpoint, params = {}) => {
  try {
    const url = new URL(`${API_URL}${endpoint}`);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        handleApiError({ response });
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    handleApiError(error);
  }
};

/**
 * Make authenticated POST request
 */
export const apiPost = async (endpoint, data = {}) => {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        handleApiError({ response });
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    handleApiError(error);
  }
};

/**
 * Make authenticated PUT request
 */
export const apiPut = async (endpoint, data = {}) => {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        handleApiError({ response });
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    handleApiError(error);
  }
};

/**
 * Make authenticated DELETE request
 */
export const apiDelete = async (endpoint) => {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        handleApiError({ response });
      }
      throw new Error(`API error: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    handleApiError(error);
  }
};

export default {
  get: apiGet,
  post: apiPost,
  put: apiPut,
  delete: apiDelete,
  getAuthHeaders,
  handleApiError
};
