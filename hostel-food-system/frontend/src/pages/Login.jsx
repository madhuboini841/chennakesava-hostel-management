import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Let App.jsx handle redirect via state change, but we can force it here:
      const authUser = JSON.parse(localStorage.getItem('user'));
      if (authUser?.role === 'admin') navigate('/admin');
      else navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Hostel Food Login</h2>
        {error && <div className="bg-red-100 text-red-700 p-2 mb-4 rounded text-sm">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input 
              type="email" 
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
              value={email} onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input 
              type="password" 
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring focus:border-blue-300"
              value={password} onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none">
            Sign In
          </button>
        </form>
        
        <div className="mt-4 text-center">
          <Link to="/forgot-password" className="text-sm text-blue-600 hover:text-blue-800">Forgot Password?</Link>
        </div>

      </div>
    </div>
  );
};

export default Login;
