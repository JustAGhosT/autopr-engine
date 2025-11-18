import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Clipboard, Trash2 } from 'lucide-react';

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/logs');

    ws.onmessage = (event) => {
      setLogs((prevLogs) => [...prevLogs, event.data]);
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleClear = () => {
    setLogs([]);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(logs.join('\n'));
  };

  return (
    <div>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Logs</h1>
          <p className="mt-2 text-gray-600">
            This page shows the real-time logs from the AutoPR engine.
          </p>
        </div>
        <div>
          <Button variant="outline" onClick={handleCopy} className="mr-4">
            <Clipboard className="w-5 h-5" />
          </Button>
          <Button variant="destructive" onClick={handleClear}>
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      </div>
      <div className="mt-6 p-4 bg-gray-900 text-white rounded-md">
        {logs.map((log, index) => (
          <div key={index} className="font-mono">{log}</div>
        ))}
      </div>
    </div>
  );
};

export default Logs;
