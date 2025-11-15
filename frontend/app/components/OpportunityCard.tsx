/**
 * Card component for displaying individual opportunity.
 * Shows LLM analysis result from a single batch.
 */

import { BatchResult } from '@/lib/api';

interface OpportunityCardProps {
  result: BatchResult;
}

export default function OpportunityCard({ result }: OpportunityCardProps) {
  // Check if batch has error
  if (result.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-red-800">
              Batch {result.batch_number} Failed
            </h3>
            <p className="mt-2 text-sm text-red-700">{result.error}</p>
            <p className="mt-1 text-xs text-red-600">
              {result.emails_in_batch} emails in batch
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Render successful batch analysis
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
      {/* Batch Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Batch {result.batch_number} of {result.total_batches}
        </h3>
        <span className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
          {result.emails_in_batch} emails
        </span>
      </div>

      {/* Analysis Content */}
      <div className="prose prose-sm max-w-none">
        <div className="text-gray-700 whitespace-pre-wrap">
          {result.analysis}
        </div>
      </div>

      {/* Processed Timestamp */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          Processed: {new Date(result.processed_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
