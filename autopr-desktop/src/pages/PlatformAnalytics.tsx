import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { RefreshCw, TrendingUp, Activity, Zap, Search } from 'lucide-react';

interface PlatformData {
  id: string;
  name: string;
  category: string;
  detectionCount: number;
  avgConfidence: number;
  lastDetected: string;
  trend: 'up' | 'down' | 'stable';
}

const SkeletonCard = () => (
  <Card className="animate-pulse">
    <CardHeader>
      <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded w-3/4"></div>
    </CardHeader>
    <CardContent>
      <div className="space-y-2">
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full"></div>
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-2/3"></div>
      </div>
    </CardContent>
  </Card>
);

const PlatformAnalytics: React.FC = () => {
  const [platforms, setPlatforms] = useState<PlatformData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'count' | 'confidence'>('count');

  // Mock data for demonstration
  const mockPlatforms: PlatformData[] = [
    { id: 'base44', name: 'Base44', category: 'ai_development', detectionCount: 45, avgConfidence: 0.92, lastDetected: '2024-11-18T12:20:00', trend: 'up' },
    { id: 'windsurf', name: 'Windsurf', category: 'ai_development', detectionCount: 38, avgConfidence: 0.88, lastDetected: '2024-11-18T11:45:00', trend: 'up' },
    { id: 'github_copilot', name: 'GitHub Copilot', category: 'ai_development', detectionCount: 156, avgConfidence: 0.95, lastDetected: '2024-11-18T12:15:00', trend: 'stable' },
    { id: 'cursor', name: 'Cursor', category: 'ai_development', detectionCount: 123, avgConfidence: 0.91, lastDetected: '2024-11-18T12:10:00', trend: 'up' },
    { id: 'continue', name: 'Continue', category: 'ai_development', detectionCount: 67, avgConfidence: 0.87, lastDetected: '2024-11-18T11:30:00', trend: 'stable' },
    { id: 'aider', name: 'Aider', category: 'ai_development', detectionCount: 34, avgConfidence: 0.84, lastDetected: '2024-11-18T10:50:00', trend: 'up' },
    { id: 'amazon_q', name: 'Amazon Q', category: 'ai_development', detectionCount: 52, avgConfidence: 0.89, lastDetected: '2024-11-18T12:05:00', trend: 'stable' },
    { id: 'replit', name: 'Replit', category: 'rapid_prototyping', detectionCount: 89, avgConfidence: 0.93, lastDetected: '2024-11-18T11:55:00', trend: 'down' },
    { id: 'vercel', name: 'Vercel', category: 'cloud_hosting', detectionCount: 201, avgConfidence: 0.96, lastDetected: '2024-11-18T12:18:00', trend: 'up' },
    { id: 'netlify', name: 'Netlify', category: 'cloud_hosting', detectionCount: 145, avgConfidence: 0.94, lastDetected: '2024-11-18T12:12:00', trend: 'stable' },
  ];

  useEffect(() => {
    // Simulate API call
    const loadData = async () => {
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      setPlatforms(mockPlatforms);
      setIsLoading(false);
    };
    loadData();
  }, []);

  const refreshData = async () => {
    setIsRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    // In production, fetch from actual API
    setPlatforms([...mockPlatforms]);
    setIsRefreshing(false);
  };

  const categories = ['all', ...Array.from(new Set(platforms.map(p => p.category)))];

  const filteredAndSortedPlatforms = platforms
    .filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || p.category === categoryFilter;
      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'count') return b.detectionCount - a.detectionCount;
      if (sortBy === 'confidence') return b.avgConfidence - a.avgConfidence;
      return 0;
    });

  const totalDetections = platforms.reduce((sum, p) => sum + p.detectionCount, 0);
  const avgConfidence = platforms.reduce((sum, p) => sum + p.avgConfidence, 0) / platforms.length || 0;
  const mostPopular = platforms.sort((a, b) => b.detectionCount - a.detectionCount)[0];
  const highestConfidence = platforms.sort((a, b) => b.avgConfidence - a.avgConfidence)[0];

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'down') return <TrendingUp className="w-4 h-4 text-red-500 rotate-180" />;
    return <Activity className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="dark:text-white">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Platform Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Real-time insights into platform detection and usage
          </p>
        </div>
        <Button 
          onClick={refreshData} 
          disabled={isRefreshing}
          aria-label="Refresh analytics"
        >
          <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Summary Cards */}
      {!isLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
          <Card className="dark:bg-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Total Detections
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{totalDetections}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Across all platforms</p>
            </CardContent>
          </Card>

          <Card className="dark:bg-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Avg Confidence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{(avgConfidence * 100).toFixed(1)}%</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Detection accuracy</p>
            </CardContent>
          </Card>

          <Card className="dark:bg-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Most Popular
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{mostPopular?.name || 'N/A'}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {mostPopular?.detectionCount || 0} detections
              </p>
            </CardContent>
          </Card>

          <Card className="dark:bg-gray-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Highest Confidence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{highestConfidence?.name || 'N/A'}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {((highestConfidence?.avgConfidence || 0) * 100).toFixed(1)}% accuracy
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6 flex-wrap">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search platforms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat === 'all' ? 'All Categories' : cat.replace('_', ' ')}
            </option>
          ))}
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'name' | 'count' | 'confidence')}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                   focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="count">Sort by Detections</option>
          <option value="confidence">Sort by Confidence</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>

      {/* Platform Cards */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredAndSortedPlatforms.map((platform) => (
            <Card key={platform.id} className="dark:bg-gray-800 hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="dark:text-white">{platform.name}</CardTitle>
                    <Badge variant="secondary" className="mt-2">
                      {platform.category.replace('_', ' ')}
                    </Badge>
                  </div>
                  {getTrendIcon(platform.trend)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Detections</span>
                    <span className="font-bold text-lg">{platform.detectionCount}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Confidence</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-600 rounded-full" 
                          style={{ width: `${platform.avgConfidence * 100}%` }}
                        />
                      </div>
                      <span className="font-medium text-sm">{(platform.avgConfidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Last: {new Date(platform.lastDetected).toLocaleString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isLoading && filteredAndSortedPlatforms.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          No platforms found matching your filters
        </div>
      )}
    </div>
  );
};

export default PlatformAnalytics;
