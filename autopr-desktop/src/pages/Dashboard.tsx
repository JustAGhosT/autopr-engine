import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { RefreshCw } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStatus = () => {
    invoke('get_status').then((res) => {
      setStatus(JSON.parse(res as string));
      setLastUpdated(new Date());
    });
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="mt-2 text-gray-600">
            This page shows the real-time status of the AutoPR engine.
          </p>
        </div>
        <div className="flex items-center">
          {lastUpdated && (
            <p className="text-sm text-gray-500 mr-4">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
          <Button onClick={fetchStatus}>
            <RefreshCw className="w-5 h-5" />
          </Button>
        </div>
      </div>
      <div className="mt-6">
        {status ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Engine Status</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge>{status.engine}</Badge>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Workflow Engine</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge>{status.workflow_engine.status}</Badge>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{status.actions}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Integrations</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{status.integrations}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>LLM Providers</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{status.llm_providers}</p>
              </CardContent>
            </Card>
          </div>
        ) : (
          'Loading...'
        )}
      </div>
    </div>
  );
};

export default Dashboard;
