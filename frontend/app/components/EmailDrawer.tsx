/**
 * Scrollable drawer component for displaying original emails.
 * Shows full email content for cross-checking purposes.
 */

import { BatchResult } from '@/lib/api';

interface EmailDrawerProps {
  results: BatchResult[];
  isOpen: boolean;
  onToggle: () => void;
}

export default function EmailDrawer({ results, isOpen, onToggle }: EmailDrawerProps) {
  return (
    <>
      {/* Toggle Button - Always visible */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-gray-800 text-gray-200 px-3 py-6 rounded-l-lg shadow-lg hover:bg-gray-700 transition-colors z-40 border-l-2 border-blue-500"
        style={{ right: isOpen ? '400px' : '0' }}
      >
        {isOpen ? '→' : '← Emails'}
      </button>

      {/* Drawer Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-[400px] bg-gray-800 border-l-2 border-gray-700 shadow-2xl transform transition-transform duration-300 ease-in-out z-30 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="bg-gray-900 px-4 py-4 border-b border-gray-700">
          <h2 className="text-lg font-bold text-gray-100">Original Emails</h2>
          <p className="text-xs text-gray-400 mt-1">
            {results.length} {results.length === 1 ? 'batch' : 'batches'} processed
          </p>
        </div>

        {/* Scrollable Content */}
        <div className="overflow-y-auto h-[calc(100vh-80px)] px-4 py-4">
          {results.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-gray-400">No emails processed yet...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result, idx) => (
                <div key={idx} className="bg-gray-700 rounded-lg p-3 border border-gray-600">
                  {/* Batch Header */}
                  <div className="mb-2 pb-2 border-b border-gray-600">
                    <p className="text-xs font-semibold text-blue-400">
                      Batch {result.batch_number} of {result.total_batches}
                    </p>
                    <p className="text-xs text-gray-400">
                      {result.thread_count_in_batch} {result.thread_count_in_batch === 1 ? 'thread' : 'threads'}
                    </p>
                  </div>

                  {/* Email Content */}
                  {result.original_emails ? (
                    <div className="space-y-2">
                      {result.original_emails.map((email: any, emailIdx: number) => (
                        <div key={emailIdx} className="bg-gray-800 rounded p-2 border border-gray-600">
                          {/* Email Metadata */}
                          <div className="mb-1">
                            <p className="text-xs font-semibold text-gray-200 truncate">
                              {email.subject || 'No Subject'}
                            </p>
                            <p className="text-xs text-gray-400">{email.date || 'Unknown Date'}</p>
                          </div>

                          {/* Email Body (scrollable, small font) */}
                          <div className="max-h-32 overflow-y-auto">
                            <pre className="text-[10px] leading-tight text-gray-300 whitespace-pre-wrap break-words font-mono">
                              {email.body || 'No content'}
                            </pre>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400 italic">No email content available</p>
                  )}

                  {/* Timestamp */}
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(result.processed_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
