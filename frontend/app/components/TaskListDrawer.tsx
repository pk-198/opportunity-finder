/**
 * Scrollable drawer component for displaying task history.
 * Shows all tasks in memory with 24-hour retention.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAllTasks, TaskMetadata } from '@/lib/api';

interface TaskListDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
}

export default function TaskListDrawer({ isOpen, onToggle }: TaskListDrawerProps) {
  const router = useRouter();
  const [tasks, setTasks] = useState<TaskMetadata[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // Fetch tasks on mount and refresh every 30 seconds
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await getAllTasks();
        setTasks(response.tasks);
        setError('');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tasks');
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();

    // Refresh every 30 seconds
    const intervalId = setInterval(fetchTasks, 30000);
    return () => clearInterval(intervalId);
  }, []);

  // Navigate to task results
  const handleTaskClick = (taskId: string) => {
    router.push(`/analysis?task_id=${taskId}`);
  };

  // Status badge component
  const StatusBadge = ({ status }: { status: string }) => {
    const colors: Record<string, string> = {
      processing: 'bg-blue-900 text-blue-200 border border-blue-700',
      completed: 'bg-green-900 text-green-200 border border-green-700',
      failed: 'bg-red-900 text-red-200 border border-red-700',
    };

    const colorClass = colors[status] || 'bg-gray-800 text-gray-200 border border-gray-700';

    return (
      <span className={`inline-block px-2 py-0.5 text-xs font-semibold rounded ${colorClass}`}>
        {status}
      </span>
    );
  };

  return (
    <>
      {/* Toggle Button - Always visible */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-gray-800 text-gray-200 px-3 py-6 rounded-l-lg shadow-lg hover:bg-gray-700 transition-colors z-40 border-l-2 border-purple-500"
        style={{ right: isOpen ? '350px' : '0' }}
      >
        {isOpen ? '→' : '← Tasks'}
      </button>

      {/* Drawer Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[350px] bg-gray-800 border-l-2 border-gray-700 shadow-2xl transform transition-transform duration-300 ease-in-out z-30 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="bg-gray-900 px-4 py-4 border-b border-gray-700">
          <h2 className="text-lg font-bold text-gray-100">Task History</h2>
          <p className="text-xs text-gray-400 mt-1">
            {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'} in memory (24hr retention)
          </p>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto h-[calc(100vh-80px)] px-4 py-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
              <p className="mt-4 text-sm text-gray-300">Loading tasks...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-sm text-red-300">{error}</p>
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-400">No tasks in memory</p>
              <p className="text-xs text-gray-500 mt-2">Tasks auto-delete after 24 hours</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <button
                  key={task.task_id}
                  onClick={() => handleTaskClick(task.task_id)}
                  className="w-full bg-gray-700 rounded-lg p-3 border border-gray-600 hover:bg-gray-600 hover:border-purple-500 transition-all text-left"
                >
                  {/* Task ID (short) */}
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-mono text-purple-300 truncate">
                      {task.task_id.slice(0, 8)}...
                    </p>
                    <StatusBadge status={task.status} />
                  </div>

                  {/* Sender and Progress */}
                  <div className="mb-2">
                    <p className="text-sm font-semibold text-gray-200 capitalize">
                      {task.sender_id.replace('_', ' ')}
                    </p>
                    <p className="text-xs text-gray-400">
                      Progress: {task.progress} • {task.result_count} results
                    </p>
                  </div>

                  {/* Config Info */}
                  <div className="text-xs text-gray-500 space-y-0.5">
                    <p>Emails: {task.email_limit} • Batch: {task.batch_size}</p>
                    <p className="truncate">
                      Created: {new Date(task.created_at).toLocaleString()}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
