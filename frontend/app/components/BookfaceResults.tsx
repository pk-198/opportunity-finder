/**
 * Component for displaying Bookface Forum Digest analysis results.
 * Parses markdown output into 5 sections and displays with collapsible panels.
 */

'use client';

import { useState } from 'react';
import { BatchResult } from '@/lib/api';

interface BookfaceResultsProps {
  results: BatchResult[];
}

// Section emojis for matching
const SECTION_EMOJIS = {
  GROWTH_HACKS: '📈',
  REPLICABLE_CONTENT: '📝',
  COMMENTING: '💬',
  AUTORM: '🏗️',
  TOP_THREADS: '🎯',
};

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

// Item card component for displaying individual opportunities/insights
interface ItemCardProps {
  item: Record<string, string>;
  showBatchInfo?: boolean;
  batchNumber?: number;
  batchTotal?: number;
  processedAt?: string;
}

function ItemCard({ item, showBatchInfo, batchNumber, batchTotal, processedAt }: ItemCardProps) {
  return (
    <div className="bg-gray-700 border border-gray-600 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Priority Badge */}
      {item.Priority && (
        <div className="mb-3">
          <PriorityBadge priority={item.Priority} />
        </div>
      )}

      {/* Item Content */}
      <div className="space-y-2">
        {Object.entries(item).map(([key, value]) => {
          // Skip priority (shown as badge) and empty values
          if (key === 'Priority' || !value) return null;

          // Special handling for links
          if (key === 'Link' && value.startsWith('http')) {
            return (
              <p key={key}>
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
          }

          // Regular text fields
          return (
            <p key={key} className="text-gray-300 leading-relaxed">
              <strong className="text-gray-100">{key}:</strong> {value}
            </p>
          );
        })}
      </div>

      {/* Optional Batch Info */}
      {showBatchInfo && batchNumber && (
        <div className="mt-4 pt-3 border-t border-gray-600">
          <p className="text-xs text-gray-400">
            From Batch {batchNumber} of {batchTotal}
            {processedAt && <> • {new Date(processedAt).toLocaleString()}</>}
          </p>
        </div>
      )}
    </div>
  );
}

// Parse markdown section into structured items
function parseSection(sectionText: string): Record<string, string>[] {
  const items: Record<string, string>[] = [];
  const itemBlocks = sectionText.split(/^## Item \d+$/gm).filter(Boolean);

  itemBlocks.forEach((block) => {
    const item: Record<string, string> = {};
    const lines = block.trim().split('\n');

    lines.forEach((line) => {
      // Match lines like "- Key: Value" or "- Key: [value]"
      const match = line.match(/^-\s*([^:]+):\s*(.+)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim();
        item[key] = value;
      }
    });

    // Only add if item has content
    if (Object.keys(item).length > 0) {
      items.push(item);
    }
  });

  return items;
}

// Parse TOP 2 THREADS section (numbered list format)
function parseTopThreads(sectionText: string): Array<{ number: string; title: string; link: string }> {
  const threads: Array<{ number: string; title: string; link: string }> = [];
  const lines = sectionText.trim().split('\n');

  lines.forEach((line) => {
    // Match lines like "1. [Thread Title] - [link]"
    const match = line.match(/^(\d+)\.\s*(.+?)\s*-\s*(https?:\/\/.+)$/);
    if (match) {
      threads.push({
        number: match[1],
        title: match[2].trim(),
        link: match[3].trim(),
      });
    }
  });

  return threads;
}

// Collapsible section component
interface SectionPanelProps {
  title: string;
  emoji: string;
  items: Record<string, string>[] | Array<{ number: string; title: string; link: string }>;
  defaultOpen?: boolean;
  isTopThreads?: boolean;
  batchNumber?: number;
  batchTotal?: number;
  processedAt?: string;
}

function SectionPanel({
  title,
  emoji,
  items,
  defaultOpen = true,
  isTopThreads = false,
  batchNumber,
  batchTotal,
  processedAt,
}: SectionPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="bg-gray-800 border-2 border-gray-700 rounded-lg shadow-md">
      {/* Section Header - Clickable to toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{emoji}</span>
          <h3 className="text-xl font-bold text-gray-100">{title}</h3>
          <span className="text-sm text-gray-400">
            ({items.length} {items.length === 1 ? 'item' : 'items'})
          </span>
        </div>
        <svg
          className={`w-6 h-6 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Section Content - Collapsible */}
      {isOpen && (
        <div className="px-6 pb-6">
          <div className="space-y-4">
            {isTopThreads ? (
              // Special rendering for TOP 2 THREADS (numbered list)
              (items as Array<{ number: string; title: string; link: string }>).map((thread, idx) => (
                <div key={idx} className="bg-gray-700 border border-gray-600 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-lg font-bold text-gray-100">{thread.number}.</span>
                    <div>
                      <p className="text-gray-200 font-medium mb-1">{thread.title}</p>
                      <a
                        href={thread.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline text-sm break-all"
                      >
                        {thread.link}
                      </a>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              // Regular item cards for other sections
              (items as Record<string, string>[]).map((item, idx) => (
                <ItemCard
                  key={idx}
                  item={item}
                  showBatchInfo={true}
                  batchNumber={batchNumber}
                  batchTotal={batchTotal}
                  processedAt={processedAt}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function BookfaceResults({ results }: BookfaceResultsProps) {
  // Aggregate all markdown from batches
  const allMarkdown = results
    .filter((r) => !r.error && r.raw_markdown)
    .map((r) => r.raw_markdown)
    .join('\n\n');

  if (!allMarkdown) {
    return (
      <div className="text-center py-12 px-4 bg-gray-800 rounded-lg border border-gray-700">
        <p className="text-sm text-gray-300">No results yet. Analysis in progress...</p>
      </div>
    );
  }

  // Parse sections from markdown
  const sections: Array<{
    title: string;
    emoji: string;
    items: Record<string, string>[] | Array<{ number: string; title: string; link: string }>;
    isTopThreads?: boolean;
  }> = [];

  // Extract each section by emoji header
  const sectionRegex = /^#\s*(📈|📝|💬|🏗️|🎯)\s*(.+?)$/gm;
  let match;
  const sectionStarts: Array<{ emoji: string; title: string; index: number }> = [];

  while ((match = sectionRegex.exec(allMarkdown)) !== null) {
    sectionStarts.push({
      emoji: match[1],
      title: match[2].trim(),
      index: match.index,
    });
  }

  // Parse each section's content
  sectionStarts.forEach((section, idx) => {
    const startIndex = section.index;
    const endIndex = idx < sectionStarts.length - 1 ? sectionStarts[idx + 1].index : allMarkdown.length;
    const sectionContent = allMarkdown.substring(startIndex, endIndex);

    const isTopThreads = section.emoji === SECTION_EMOJIS.TOP_THREADS;
    const items = isTopThreads ? parseTopThreads(sectionContent) : parseSection(sectionContent);

    if (items.length > 0) {
      sections.push({
        title: section.title,
        emoji: section.emoji,
        items,
        isTopThreads,
      });
    }
  });

  // Show error if no sections found
  if (sections.length === 0) {
    return (
      <div className="text-center py-8 text-gray-300">
        No valid sections found in the analysis results.
      </div>
    );
  }

  // Get batch metadata from first result
  const firstResult = results.find((r) => !r.error);

  // Display results organized by section
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-100 mb-4">
        Bookface Analysis Results ({results.length} batches processed)
      </h2>

      {/* Render each section as collapsible panel */}
      {sections.map((section, idx) => (
        <SectionPanel
          key={idx}
          title={section.title}
          emoji={section.emoji}
          items={section.items}
          isTopThreads={section.isTopThreads}
          batchNumber={firstResult?.batch_number}
          batchTotal={firstResult?.total_batches}
          processedAt={firstResult?.processed_at}
        />
      ))}
    </div>
  );
}
