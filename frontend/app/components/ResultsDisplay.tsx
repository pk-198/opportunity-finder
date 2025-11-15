/**
 * Container component for displaying analysis results.
 * Maps batch results to OpportunityCard components.
 */

import { BatchResult } from '@/lib/api';
import OpportunityCard from './OpportunityCard';

interface ResultsDisplayProps {
  results: BatchResult[];
}

export default function ResultsDisplay({ results }: ResultsDisplayProps) {
  // Show empty state if no results
  if (results.length === 0) {
    return (
      <div className="text-center py-12 px-4 bg-gray-50 rounded-lg border border-gray-200">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <p className="mt-4 text-sm text-gray-600">No results yet. Analysis in progress...</p>
      </div>
    );
  }

  // Display results as cards
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Analysis Results ({results.length} batches)
      </h2>
      {results.map((result, index) => (
        <OpportunityCard key={index} result={result} />
      ))}
    </div>
  );
}
