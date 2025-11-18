import { HashRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Home, Settings, FileText } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Configuration from './pages/Configuration';
import Logs from './pages/Logs';
import './App.css';

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <aside className="w-64 bg-white shadow-md">
          <div className="p-6">
            <h1 className="text-2xl font-bold">AutoPR</h1>
          </div>
          <nav className="mt-6">
            <Link to="/" className="flex items-center px-6 py-2 text-gray-700 hover:bg-gray-200">
              <Home className="w-5 h-5" />
              <span className="mx-4">Dashboard</span>
            </Link>
            <Link to="/configuration" className="flex items-center px-6 py-2 mt-4 text-gray-700 hover:bg-gray-200">
              <Settings className="w-5 h-5" />
              <span className="mx-4">Configuration</span>
            </Link>
            <Link to="/logs" className="flex items-center px-6 py-2 mt-4 text-gray-700 hover:bg-gray-200">
              <FileText className="w-5 h-5" />
              <span className="mx-4">Logs</span>
            </Link>
          </nav>
        </aside>
        <main className="flex-1 p-6 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/configuration" element={<Configuration />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
