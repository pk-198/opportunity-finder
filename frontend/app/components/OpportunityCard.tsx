/**
 * Card component for displaying individual opportunity.
 * Shows a single opportunity with all its data as plain text.
 */

interface OpportunityCardProps {
  opportunity: any;
  showBatchInfo?: boolean;
}

// Source badge component (Reddit vs Hacker News)
function SourceBadge({ source }: { source?: any }) {
  if (!source) return null;

  // Normalize source to string (handles object, array, or string)
  let sourceStr = '';
  if (typeof source === 'string') {
    sourceStr = source;
  } else if (typeof source === 'object') {
    // If source is object like {text: "Reddit"}, extract the value
    sourceStr = JSON.stringify(source);
  } else {
    sourceStr = String(source);
  }

  const sourceStrLower = sourceStr.toLowerCase();
  const isHN = sourceStrLower.includes('hacker') || sourceStrLower.includes('hn');
  const colorClass = isHN
    ? 'bg-orange-900 text-orange-200 border border-orange-700'
    : 'bg-blue-900 text-blue-200 border border-blue-700';

  const displayText = isHN ? '🔥 Hacker News' : '🔴 Reddit';

  return (
    <span className={`inline-block px-3 py-1 text-xs font-semibold rounded ${colorClass}`}>
      {displayText}
    </span>
  );
}

// Priority badge component
function PriorityBadge({ priority }: { priority?: string }) {
  if (!priority) return null;

  const colors: Record<string, string> = {
    High: 'bg-red-900 text-red-200 border border-red-700',
    Medium: 'bg-yellow-900 text-yellow-200 border border-yellow-700',
    Low: 'bg-green-900 text-green-200 border border-green-700',
  };

  const colorClass = colors[priority] || 'bg-gray-800 text-gray-200 border border-gray-700';

  return (
    <span className={`inline-block px-3 py-1 text-sm font-semibold rounded ${colorClass}`}>
      {priority} Priority
    </span>
  );
}

// Helper to recursively render all object properties as simple text
function renderObjectAsText(obj: any, indent: number = 0): JSX.Element[] {
  const elements: JSX.Element[] = [];
  const indentClass = indent > 0 ? 'ml-4' : '';

  if (Array.isArray(obj)) {
    obj.forEach((item, idx) => {
      if (typeof item === 'object' && item !== null) {
        elements.push(...renderObjectAsText(item, indent));
      } else {
        elements.push(
          <p key={`arr-${idx}`} className={`text-gray-300 leading-relaxed ${indentClass}`}>
            • {String(item)}
          </p>
        );
      }
    });
  } else if (typeof obj === 'object' && obj !== null) {
    Object.entries(obj).forEach(([key, value]) => {
      // Skip rendering priority, source, name, and metadata fields (shown as badges)
      if (key === 'priority' || key === 'source' || key === 'name' || key.startsWith('_')) return;

      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        // Special handling for links
        if (key.toLowerCase().includes('link') && typeof value === 'string' && value.startsWith('http')) {
          elements.push(
            <p key={key} className={indentClass}>
              <strong className="text-gray-100">{key}:</strong>{' '}
              <a
                href={value}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline break-all"
              >
                {value}
              </a>
            </p>
          );
        } else {
          elements.push(
            <p key={key} className={`text-gray-300 leading-relaxed ${indentClass}`}>
              <strong className="text-gray-100">{key}:</strong> {String(value)}
            </p>
          );
        }
      } else if (typeof value === 'object' && value !== null) {
        elements.push(
          <div key={key} className={`mt-2 ${indentClass}`}>
            <p className="font-semibold text-gray-100">{key}:</p>
            {renderObjectAsText(value, indent + 1)}
          </div>
        );
      }
    });
  }

  return elements;
}

export default function OpportunityCard({ opportunity, showBatchInfo }: OpportunityCardProps) {
  // Render individual opportunity card
  return (
    <div className="bg-gray-700 border border-gray-600 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Badges at the top */}
      <div className="flex gap-2 mb-3 flex-wrap">
        <SourceBadge source={opportunity.source} />
        <PriorityBadge priority={opportunity.priority} />
      </div>

      {/* Dump all opportunity data as text */}
      <div className="space-y-2">
        {renderObjectAsText(opportunity)}
      </div>

      {/* Optional Batch Info */}
      {showBatchInfo && opportunity._batchNumber && (
        <div className="mt-4 pt-3 border-t border-gray-600">
          <p className="text-xs text-gray-400">
            From Batch {opportunity._batchNumber} of {opportunity._batchTotal}
            {opportunity._processedAt && (
              <> • {new Date(opportunity._processedAt).toLocaleString()}</>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
