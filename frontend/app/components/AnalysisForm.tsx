/**
 * Form component for email analysis configuration.
 * Allows user to set email limit and batch size.
 */

interface AnalysisFormProps {
  emailLimit: number;
  batchSize: number;
  onEmailLimitChange: (limit: number) => void;
  onBatchSizeChange: (size: number) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export default function AnalysisForm({
  emailLimit,
  batchSize,
  onEmailLimitChange,
  onBatchSizeChange,
  onSubmit,
  disabled = false,
}: AnalysisFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-4">
      {/* Email Limit Input */}
      <div>
        <label htmlFor="emailLimit" className="block text-sm font-medium text-gray-300 mb-2">
          Number of Emails
        </label>
        <input
          type="number"
          id="emailLimit"
          value={emailLimit}
          onChange={(e) => {
            const value = e.target.value;
            // Allow empty string or valid numbers
            if (value === '') {
              onEmailLimitChange(0);
            } else {
              const parsed = parseInt(value);
              onEmailLimitChange(isNaN(parsed) ? 0 : parsed);
            }
          }}
          min="1"
          max="500"
          disabled={disabled}
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-800 disabled:cursor-not-allowed"
        />
        <p className="mt-1 text-sm text-gray-400">Maximum number of emails to analyze (1-500)</p>
      </div>

      {/* Batch Size Input */}
      <div>
        <label htmlFor="batchSize" className="block text-sm font-medium text-gray-300 mb-2">
          Batch Size
        </label>
        <input
          type="number"
          id="batchSize"
          value={batchSize}
          onChange={(e) => {
            const value = e.target.value;
            // Allow empty string or valid numbers
            if (value === '') {
              onBatchSizeChange(0);
            } else {
              const parsed = parseInt(value);
              onBatchSizeChange(isNaN(parsed) ? 0 : parsed);
            }
          }}
          min="1"
          max="50"
          disabled={disabled}
          className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-800 disabled:cursor-not-allowed"
        />
        <p className="mt-1 text-sm text-gray-400">Number of emails to process per batch (1-50)</p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={disabled}
        className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {disabled ? 'Processing...' : 'Analyze Emails'}
      </button>
    </form>
  );
}
