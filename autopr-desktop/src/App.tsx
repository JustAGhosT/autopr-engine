import { HashRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Home, Settings, FileText, Moon, Sun, BarChart3 } from 'lucide-react';
import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Configuration from './pages/Configuration';
import Logs from './pages/Logs';
import PlatformAnalytics from './pages/PlatformAnalytics';
import './App.css';

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
          <div className="text-center p-8">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function NavigationLink({ to, icon: Icon, label }: { to: string; icon: any; label: string }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center px-6 py-3 mt-2 transition-colors duration-200 ${
        isActive
          ? 'bg-blue-600 text-white'
          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
      }`}
      aria-current={isActive ? 'page' : undefined}
    >
      <Icon className="w-5 h-5" />
      <span className="mx-4">{label}</span>
    </Link>
  );
}

function AppContent() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Load dark mode preference from localStorage
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode === 'true') {
      setDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    localStorage.setItem('darkMode', String(newMode));
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
      <aside className="w-64 bg-white dark:bg-gray-800 shadow-md">
        <div className="p-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AutoPR</h1>
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? (
              <Sun className="w-5 h-5 text-yellow-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </div>
        <nav className="mt-6" role="navigation" aria-label="Main navigation">
          <NavigationLink to="/" icon={Home} label="Dashboard" />
          <NavigationLink to="/analytics" icon={BarChart3} label="Platform Analytics" />
          <NavigationLink to="/configuration" icon={Settings} label="Configuration" />
          <NavigationLink to="/logs" icon={FileText} label="Logs" />
        </nav>
        <div className="absolute bottom-4 left-4 right-4 text-sm text-gray-500 dark:text-gray-400 text-center">
          <p>v1.0.0</p>
          <p className="text-xs mt-1">© 2024 AutoPR Engine</p>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto" role="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analytics" element={<PlatformAnalytics />} />
          <Route path="/configuration" element={<Configuration />} />
          <Route path="/logs" element={<Logs />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AppContent />
      </Router>
    </ErrorBoundary>
  );
}

export default App;
