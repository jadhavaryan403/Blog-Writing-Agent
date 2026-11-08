/**
 * src/App.jsx
 * ───────────
 * Route table — one React page per old HTML page, same URLs.
 */

import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';

import { Auth } from './lib/api.js';
import Landing from './pages/Landing.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Create from './pages/Create.jsx';
import Approval from './pages/Approval.jsx';
import Viewer from './pages/Viewer.jsx';
import Settings from './pages/Settings.jsx';

// Old guardAuth(): send logged-out visitors to /login.
function RequireAuth({ children }) {
  if (!Auth.isLoggedIn()) return <Navigate to="/login" replace />;
  return children;
}

// Old multi-page loads always started at the top of the page.
function ScrollToTop() {
  const { pathname, search } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname, search]);
  return null;
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/create" element={<RequireAuth><Create /></RequireAuth>} />
        <Route path="/approval" element={<RequireAuth><Approval /></RequireAuth>} />
        <Route path="/viewer" element={<RequireAuth><Viewer /></RequireAuth>} />
        <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
