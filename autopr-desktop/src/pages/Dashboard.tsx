import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { RefreshCw, AlertCircle } from 'lucide-react';

// Skeleton Loader Component
const SkeletonCard = () => (
  <Card className="animate-pulse">
    <CardHeader>
      <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>
    </CardHeader>
    <CardContent>
      <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded w-1/2"></div>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    }
    setError(null);

    try {
      const res = await invoke('get_status');
      setStatus(JSON.parse(res as string));
      setLastUpdated(new Date());
      setIsLoading(false);
    } catch (err) {
      console.error('Failed to fetch status:', err);
      setError('Failed to fetch status. Please try again.');
      setIsLoading(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => fetchStatus(), 5000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut for refresh
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        fetchStatus(true);
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className="dark:text-white">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Real-time status of the AutoPR engine
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
          <Button 
            onClick={() => fetchStatus(true)} 
            disabled={isRefreshing}
            aria-label="Refresh status"
            title="Refresh (Ctrl+R)"
          >
            <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 rounded-md flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      <div className="mt-6">
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" role="status" aria-label="Loading dashboard">
            {[...Array(5)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : status ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card className="dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="dark:text-white">Engine Status</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={status.engine === 'running' ? 'default' : 'secondary'}>
                  {status.engine}
                </Badge>
              </CardContent>
            </Card>
            <Card className="dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="dark:text-white">Workflow Engine</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={status.workflow_engine?.status === 'active' ? 'default' : 'secondary'}>
                  {status.workflow_engine?.status || 'N/A'}
                </Badge>
              </CardContent>
            </Card>
            <Card className="dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="dark:text-white">Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold dark:text-white">{status.actions || 0}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">registered</p>
              </CardContent>
            </Card>
            <Card className="dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="dark:text-white">Integrations</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold dark:text-white">{status.integrations || 0}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">active</p>
              </CardContent>
            </Card>
            <Card className="dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="dark:text-white">LLM Providers</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold dark:text-white">{status.llm_providers || 0}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">configured</p>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12">
            No status data available
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
