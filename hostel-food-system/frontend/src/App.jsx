import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import FeeReceiptsStudent from './pages/FeeReceiptsStudent';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

const ProtectedRoute = ({ children, allowedRole }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (allowedRole && user.role !== allowedRole) return <Navigate to={user.role === 'admin' ? '/admin' : '/'} />;
  return children;
};

import StudentLayout from './components/StudentLayout';
import StudentProfile from './pages/StudentProfile';
import ComplaintsStudent from './pages/ComplaintsStudent';
import NoticesStudent from './pages/NoticesStudent';
import FeeStatusStudent from './pages/FeeStatusStudent';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password/:token" element={<ResetPassword />} />
      <Route path="/admin" element={<ProtectedRoute allowedRole="admin"><AdminDashboard /></ProtectedRoute>} />
      
      {/* Student Portal Routes with Sidebar Layout */}
      <Route path="/" element={<ProtectedRoute allowedRole="student"><StudentLayout /></ProtectedRoute>}>
        <Route index element={<StudentProfile />} />
        <Route path="fees" element={<FeeStatusStudent />} />
        <Route path="receipts" element={<FeeReceiptsStudent />} />
        <Route path="complaints" element={<ComplaintsStudent />} />
        <Route path="notices" element={<NoticesStudent />} />
        <Route path="food" element={<StudentDashboard />} />
      </Route>
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
