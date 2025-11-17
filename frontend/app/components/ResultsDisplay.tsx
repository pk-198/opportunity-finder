/**
 * Container component for displaying analysis results.
 * Aggregates opportunities by section across all batches.
 * Conditionally renders BookfaceResults for bookface_digest sender.
 */

import { BatchResult } from '@/lib/api';
import OpportunityCard from './OpportunityCard';
import BookfaceResults from './BookfaceResults';

interface ResultsDisplayProps {
  results: BatchResult[];
  senderId?: string; // Sender identifier for conditional rendering
}

// Parse JSON analysis or return null if invalid
function parseAnalysis(analysisString?: string): any {
  if (!analysisString) return null;

  try {
    return JSON.parse(analysisString);
  } catch (e) {
    console.error('Failed to parse analysis JSON:', e);
    return null;
  }
}

// Aggregate opportunities by section across all batches
function aggregateBySection(results: BatchResult[]): Map<string, any[]> {
  const sectionMap = new Map<string, any[]>();

  results.forEach((result) => {
    if (result.error) return; // Skip failed batches

    const analysis = parseAnalysis(result.analysis);
    if (!analysis?.sections) return;

    analysis.sections.forEach((section: any) => {
      const sectionTitle = section.title || 'Untitled Section';

      // Get existing opportunities for this section or create new array
      const existingOpportunities = sectionMap.get(sectionTitle) || [];

      // Add opportunities from this section
      if (section.opportunities && Array.isArray(section.opportunities)) {
        section.opportunities.forEach((opp: any) => {
          existingOpportunities.push({
            ...opp,
            // Add metadata about which batch this came from
            _batchNumber: result.batch_number,
            _batchTotal: result.total_batches,
            _processedAt: result.processed_at,
          });
        });
      }

      // Add nested sections (e.g., blog topics)
      if (section.sections && Array.isArray(section.sections)) {
        section.sections.forEach((subsection: any) => {
          existingOpportunities.push({
            ...subsection,
            _batchNumber: result.batch_number,
            _batchTotal: result.total_batches,
            _processedAt: result.processed_at,
          });
        });
      }

      sectionMap.set(sectionTitle, existingOpportunities);
    });
  });

  return sectionMap;
}

export default function ResultsDisplay({ results, senderId }: ResultsDisplayProps) {
  // Conditional rendering: Use BookfaceResults for bookface_digest sender
  if (senderId === 'bookface_digest') {
    return <BookfaceResults results={results} />;
  }

  // Default rendering for F5bot and HARO senders
  // Show empty state if no results
  if (results.length === 0) {
    return (
      <div className="text-center py-12 px-4 bg-gray-800 rounded-lg border border-gray-700">
        <svg
          className="mx-auto h-12 w-12 text-gray-500"
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
        <p className="mt-4 text-sm text-gray-300">No results yet. Analysis in progress...</p>
      </div>
    );
  }

  // Aggregate opportunities by section
  const sectionMap = aggregateBySection(results);

  // Show error message if no valid sections found
  if (sectionMap.size === 0) {
    // Check if there are any failed batches to show
    const failedBatches = results.filter(r => r.error);

    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-100 mb-4">
          Analysis Results ({results.length} batches)
        </h2>

        {failedBatches.length > 0 && (
          <div className="space-y-3">
            {failedBatches.map((result, index) => (
              <div key={index} className="bg-red-900 border border-red-700 rounded-lg p-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-red-200">
                      Batch {result.batch_number} Failed
                    </h3>
                    <p className="mt-2 text-sm text-red-300">{result.error}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {failedBatches.length === 0 && (
          <div className="text-center py-8 text-gray-300">
            No valid sections found in the analysis results.
          </div>
        )}
      </div>
    );
  }

  // Display results organized by section
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-100 mb-4">
        Analysis Results ({results.length} batches processed)
      </h2>

      {/* Render each section with all its opportunities from all batches */}
      {Array.from(sectionMap.entries()).map(([sectionTitle, opportunities]) => (
        <div key={sectionTitle} className="bg-gray-800 border-2 border-gray-700 rounded-lg p-6 shadow-md">
          {/* Section Header */}
          <div className="mb-6 pb-4 border-b-2 border-gray-600">
            <h3 className="text-2xl font-bold text-gray-100">{sectionTitle}</h3>
            <p className="text-sm text-gray-400 mt-1">
              {opportunities.length} {opportunities.length === 1 ? 'opportunity' : 'opportunities'}
            </p>
          </div>

          {/* Opportunities in this section */}
          <div className="space-y-4">
            {opportunities.map((opportunity, oppIdx) => (
              <OpportunityCard
                key={oppIdx}
                opportunity={opportunity}
                showBatchInfo={true}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
