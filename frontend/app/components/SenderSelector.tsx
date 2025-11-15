/**
 * Dropdown component for selecting email sender.
 * Displays sender name and description.
 */

import { Sender } from '@/lib/api';

interface SenderSelectorProps {
  senders: Sender[];
  selectedId: string;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

export default function SenderSelector({
  senders,
  selectedId,
  onSelect,
  disabled = false,
}: SenderSelectorProps) {
  return (
    <div className="w-full">
      <label htmlFor="sender" className="block text-sm font-medium text-gray-700 mb-2">
        Email Sender
      </label>
      <select
        id="sender"
        value={selectedId}
        onChange={(e) => onSelect(e.target.value)}
        disabled={disabled}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">Select a sender...</option>
        {senders.map((sender) => (
          <option key={sender.id} value={sender.id}>
            {sender.name} - {sender.description}
          </option>
        ))}
      </select>
    </div>
  );
}
