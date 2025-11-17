/**
 * Visual progress indicator component.
 * Shows batch processing progress (e.g., "Processing batch 3/10").
 */

interface ProgressBarProps {
  progress: string; // Format: "3/10"
  status: 'processing' | 'completed' | 'failed';
}

export default function ProgressBar({ progress, status }: ProgressBarProps) {
  // Parse progress string to calculate percentage
  const [current, total] = progress.split('/').map((n) => parseInt(n) || 0);
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

  // Determine status color
  const getStatusColor = () => {
    switch (status) {
      case 'processing':
        return 'bg-blue-600';
      case 'completed':
        return 'bg-green-600';
      case 'failed':
        return 'bg-red-600';
      default:
        return 'bg-gray-400';
    }
  };

  // Determine status text
  const getStatusText = () => {
    switch (status) {
      case 'processing':
        return `Processing batch ${progress}...`;
      case 'completed':
        return 'Analysis complete!';
      case 'failed':
        return 'Analysis failed';
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="w-full">
      {/* Status Text */}
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-200">{getStatusText()}</span>
        <span className="text-sm font-medium text-gray-200">{percentage}%</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className={`h-full ${getStatusColor()} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
