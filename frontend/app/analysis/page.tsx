/**
 * Results page for email analysis.
 * Polls for task status and displays incremental results.
 */

'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getTaskStatus, TaskStatus } from '@/lib/api';
import ProgressBar from '../components/ProgressBar';
import ResultsDisplay from '../components/ResultsDisplay';
import EmailDrawer from '../components/EmailDrawer';

export default function AnalysisPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get task_id from URL query params
  const taskId = searchParams.get('task_id');

  // State management
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [error, setError] = useState<string>('');
  const [polling, setPolling] = useState<boolean>(true);
  const [drawerOpen, setDrawerOpen] = useState<boolean>(true); // Open by default

  // Poll for task status every 15 seconds using useEffect
  useEffect(() => {
    // Validate task_id exists
    if (!taskId) {
      setError('No task ID provided');
      setPolling(false);
      return;
    }

    // Function to fetch task status
    const fetchStatus = async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatus(status);

        // Stop polling if task is completed or failed
        if (status.status === 'completed' || status.status === 'failed') {
          setPolling(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
        setPolling(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Set up polling interval (20 seconds)
    const intervalId = setInterval(() => {
      if (polling) {
        fetchStatus();
      }
    }, 20000);

    // Cleanup interval on unmount
    return () => clearInterval(intervalId);
  }, [taskId, polling]);

  // Handle back to home
  const handleBackToHome = () => {
    router.push('/');
  };

  return (
    <main className="min-h-screen bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-[80%] ml-auto mr-[420px]"> {/* 80% width, right-aligned, margin for drawer */}
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={handleBackToHome}
            className="inline-flex items-center text-sm text-blue-400 hover:text-blue-300 mb-4"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </button>

          <h1 className="text-3xl font-bold text-gray-100">Email Analysis Results</h1>
          {taskId && (
            <p className="mt-2 text-sm text-gray-300">Task ID: {taskId}</p>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg">
            <div className="flex items-start">
              <svg className="h-5 w-5 text-red-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="ml-3 text-sm text-red-200">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {!taskStatus && !error && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
            <p className="mt-4 text-gray-300">Loading analysis status...</p>
          </div>
        )}

        {/* Task Status Display */}
        {taskStatus && (
          <div className="space-y-6">
            {/* Progress Bar */}
            <div className="bg-gray-800 rounded-lg shadow-md p-6">
              <ProgressBar progress={taskStatus.progress} status={taskStatus.status} />

              {/* Polling Indicator */}
              {polling && taskStatus.status === 'processing' && (
                <p className="mt-4 text-sm text-gray-400 text-center">
                  Polling for updates every 20 seconds...
                </p>
              )}

              {/* Error Message */}
              {taskStatus.error && (
                <div className="mt-4 p-3 bg-red-900 border border-red-700 rounded">
                  <p className="text-sm text-red-200">{taskStatus.error}</p>
                </div>
              )}
            </div>

            {/* Results Display */}
            <ResultsDisplay results={taskStatus.results} senderId={taskStatus.sender_id} />

            {/* Completion Message */}
            {taskStatus.status === 'completed' && (
              <div className="bg-green-900 border border-green-700 rounded-lg p-4 text-center">
                <p className="text-sm text-green-200 font-medium">
                  Analysis complete! All batches have been processed.
                </p>
                <button
                  onClick={handleBackToHome}
                  className="mt-3 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-500 transition-colors"
                >
                  Start New Analysis
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Email Drawer - Fixed on right side */}
      <EmailDrawer
        results={taskStatus?.results || []}
        isOpen={drawerOpen}
        onToggle={() => setDrawerOpen(!drawerOpen)}
      />
    </main>
  );
}
