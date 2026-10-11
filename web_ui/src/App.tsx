import React, { useEffect, useState, useCallback } from 'react';
import { Navbar, CleanNavTab } from './components/layout/Navbar';
import { LiveAnalysis } from './pages/LiveAnalysis';
import { Observations } from './pages/Observations';
import { ReviewQueue } from './pages/ReviewQueue';
import { api } from './services/api';
import { HealthData, TelemetryData } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<CleanNavTab>('studio');
  const [health, setHealth] = useState<HealthData | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [h, t] = await Promise.all([api.getHealth(), api.getTelemetry()]);
      setHealth(h);
      setTelemetry(t);
    } catch (err) {
      console.error('Failed to connect to backend:', err);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-gold-500 selection:text-dark-950">
      {/* Clean Navbar */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        health={health}
        pendingReviewsCount={telemetry?.pending_reviews ?? 0}
      />

      {/* Main Clean Workspace */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentTab === 'studio' && <LiveAnalysis />}
        {currentTab === 'explore' && <Observations />}
        {currentTab === 'review' && <ReviewQueue />}
      </main>
    </div>
  );
};

export default App;
