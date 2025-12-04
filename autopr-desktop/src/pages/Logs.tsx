import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../components/ui/button';
import { Clipboard, Trash2, Download, Search, AlertCircle, CheckCircle } from 'lucide-react';

// Toast notification component
const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
  const Icon = type === 'success' ? CheckCircle : AlertCircle;

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 z-50 animate-slide-in`}>
      <Icon className="w-5 h-5" />
      <span>{message}</span>
    </div>
  );
};

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/logs');

    ws.onopen = () => {
      setIsConnected(true);
      showToast('Connected to log stream', 'success');
    };

    ws.onmessage = (event) => {
      setLogs((prevLogs) => [...prevLogs, event.data]);
    };

    ws.onerror = () => {
      setIsConnected(false);
      showToast('Failed to connect to log stream', 'error');
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Filter logs based on search
  useEffect(() => {
    if (searchQuery) {
      setFilteredLogs(logs.filter(log => log.toLowerCase().includes(searchQuery.toLowerCase())));
    } else {
      setFilteredLogs(logs);
    }
  }, [logs, searchQuery]);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
  };

  const handleClear = () => {
    setLogs([]);
    showToast('Logs cleared', 'success');
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(logs.join('\n'));
      showToast('Logs copied to clipboard', 'success');
    } catch {
      showToast('Failed to copy logs', 'error');
    }
  };

  const handleDownload = () => {
    try {
      const blob = new Blob([logs.join('\n')], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `autopr-logs-${new Date().toISOString()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      showToast('Logs downloaded', 'success');
    } catch {
      showToast('Failed to download logs', 'error');
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('log-search')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className="dark:text-white">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Logs</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400 flex items-center gap-2">
            Real-time logs from the AutoPR engine
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
              isConnected ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 
              'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            }`}>
              {isConnected ? '● Connected' : '● Disconnected'}
            </span>
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCopy} title="Copy logs (Ctrl+C)" aria-label="Copy logs">
            <Clipboard className="w-5 h-5" />
          </Button>
          <Button variant="outline" onClick={handleDownload} title="Download logs" aria-label="Download logs">
            <Download className="w-5 h-5" />
          </Button>
          <Button variant="destructive" onClick={handleClear} title="Clear logs" aria-label="Clear logs">
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      </div>

      <div className="mb-4 relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          id="log-search"
          type="text"
          placeholder="Search logs... (Ctrl+F)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Search logs"
        />
      </div>

      <div className="mt-6 p-4 bg-gray-900 dark:bg-gray-950 text-white rounded-md max-h-[600px] overflow-y-auto font-mono text-sm">
        {filteredLogs.length === 0 ? (
          <div className="text-gray-400 text-center py-8">
            {logs.length === 0 ? 'No logs yet...' : 'No matching logs found'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} className="py-1 hover:bg-gray-800 px-2 rounded">
              {log}
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default Logs;
