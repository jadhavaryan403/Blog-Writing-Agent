/**
 * src/main.jsx
 * ────────────
 * React entry point. The design lives entirely in static/css/main.css,
 * imported here so Vite bundles it with the app.
 */

import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import App from './App.jsx';
import { ToastProvider } from './components/ToastProvider.jsx';
import '../static/css/main.css';

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <ToastProvider>
      <App />
    </ToastProvider>
  </BrowserRouter>
);
