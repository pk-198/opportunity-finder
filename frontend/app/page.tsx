/**
 * Main form page for email analysis.
 * Allows user to select sender and configure analysis parameters.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSenders, startAnalysis, Sender } from '@/lib/api';
import SenderSelector from './components/SenderSelector';
import AnalysisForm from './components/AnalysisForm';
import TaskListDrawer from './components/TaskListDrawer';

export default function HomePage() {
  const router = useRouter();

  // State management
  const [senders, setSenders] = useState<Sender[]>([]);
  const [selectedSenderId, setSelectedSenderId] = useState<string>('');
  const [emailLimit, setEmailLimit] = useState<number>(50);
  const [batchSize, setBatchSize] = useState<number>(5);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [loadingSenders, setLoadingSenders] = useState<boolean>(true);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(true); // Task drawer open by default

  // Fetch senders on component mount using useEffect
  useEffect(() => {
    const fetchSenders = async () => {
      try {
        const response = await getSenders();
        setSenders(response.senders);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load senders');
      } finally {
        setLoadingSenders(false);
      }
    };

    fetchSenders();
  }, []);

  // Handle form submission
  const handleSubmit = async () => {
    // Validate sender selection
    if (!selectedSenderId) {
      setError('Please select a sender');
      return;
    }

    // Validate email limit
    if (emailLimit < 1 || emailLimit > 500) {
      setError('Email limit must be between 1 and 500');
      return;
    }

    // Validate batch size
    if (batchSize < 1 || batchSize > 50) {
      setError('Batch size must be between 1 and 50');
      return;
    }

    setError('');
    setLoading(true);

    try {
      // Start analysis via API
      const response = await startAnalysis(selectedSenderId, emailLimit, batchSize);

      // Redirect to results page with task_id in URL
      router.push(`/analysis?task_id=${response.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-100 mb-2">
            Email Analysis Tool
          </h1>
          <p className="text-lg text-gray-300">
            Analyze emails with AI-powered insights
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-800 rounded-lg shadow-md p-8">
          {/* Loading Senders State */}
          {loadingSenders && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
              <p className="mt-4 text-gray-300">Loading senders...</p>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg">
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          {/* Form Content */}
          {!loadingSenders && (
            <div className="space-y-6">
              {/* Sender Selection */}
              <SenderSelector
                senders={senders}
                selectedId={selectedSenderId}
                onSelect={setSelectedSenderId}
                disabled={loading}
              />

              {/* Analysis Configuration */}
              <AnalysisForm
                emailLimit={emailLimit}
                batchSize={batchSize}
                onEmailLimitChange={setEmailLimit}
                onBatchSizeChange={setBatchSize}
                onSubmit={handleSubmit}
                disabled={loading}
              />
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-8 text-center text-sm text-gray-400">
          <p>This tool analyzes Gmail emails and provides actionable insights.</p>
          <p className="mt-2">Results are stored in memory for 24 hours.</p>
        </div>
      </div>

      {/* Task History Drawer - Fixed on right side */}
      <TaskListDrawer
        isOpen={drawerOpen}
        onToggle={() => setDrawerOpen(!drawerOpen)}
      />
    </main>
  );
}
