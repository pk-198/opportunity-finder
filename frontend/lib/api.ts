/**
 * API client for backend communication.
 * Provides typed functions for all FastAPI endpoints.
 * Sends X-API-Key header on every request for backend authentication.
 */

// Backend API URL - configurable via env var, defaults to localhost for dev
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

// Shared headers sent with every request (API key for backend auth)
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
const commonHeaders: Record<string, string> = {
  ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
};

// Type definitions for API responses
export interface Sender {
  id: string;
  name: string;
  email: string;
  description: string;
  expected_volume: string;
  prompt_key: string;
}

export interface AnalysisResponse {
  task_id: string;
  status: string;
}

export interface BatchResult {
  batch_number: number;
  total_batches: number;
  messages_in_batch: number; // Number of individual messages in this batch (CHANGED from threads_in_batch)
  thread_count_in_batch: number; // Number of unique threads in this batch (NEW field)
  analysis?: string; // JSON string with parsed analysis
  raw_markdown?: string; // Raw markdown output from LLM
  original_emails?: Array<{ // Original message content for cross-checking (UPDATED with thread metadata)
    subject: string;
    from: string; // Sender email address (NEW field)
    thread_id: string; // Parent thread ID (NEW field)
    message_number: number; // Position in thread (NEW field)
    total_in_thread: number; // Total messages in thread (NEW field)
    body: string;
    date: string;
  }>;
  error?: string; // Error message if batch failed
  processed_at: string; // ISO timestamp
}

export interface TaskStatus {
  task_id: string;
  sender_id: string; // Sender identifier (for conditional rendering)
  status: 'processing' | 'completed' | 'failed';
  progress: string;
  results: BatchResult[];
  error?: string;
}

export interface SendersResponse {
  senders: Sender[];
}

/**
 * Start email analysis workflow.
 *
 * @param senderId - Sender identifier (e.g., "f5bot")
 * @param emailLimit - Number of emails to analyze (default: 50)
 * @param batchSize - Emails per batch (default: 5)
 * @returns Task ID and status
 */
export async function startAnalysis(
  senderId: string,
  emailLimit: number = 50,
  batchSize: number = 5
): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...commonHeaders,
    },
    body: JSON.stringify({
      sender_id: senderId,
      email_limit: emailLimit,
      batch_size: batchSize,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start analysis');
  }

  return response.json();
}

/**
 * Get task status and results.
 * Used for polling to track progress and retrieve results.
 *
 * @param taskId - Unique task identifier
 * @returns Task status, progress, and results
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await fetch(`${API_BASE_URL}/api/status/${taskId}`, {
    headers: commonHeaders,
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Task not found');
    }
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get task status');
  }

  return response.json();
}

/**
 * Get list of available email senders.
 * Used to populate sender selection dropdown.
 *
 * @returns List of configured senders
 */
export async function getSenders(): Promise<SendersResponse> {
  const response = await fetch(`${API_BASE_URL}/api/senders`, {
    headers: commonHeaders,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get senders');
  }

  return response.json();
}

/**
 * Task metadata for task list display
 */
export interface TaskMetadata {
  task_id: string;
  sender_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: string;
  created_at: string;
  updated_at: string;
  email_limit: number;
  batch_size: number;
  result_count: number;
}

/**
 * Get list of all tasks in memory (24-hour retention).
 * Used for task history drawer.
 *
 * @returns List of task metadata
 */
export async function getAllTasks(): Promise<{ tasks: TaskMetadata[] }> {
  const response = await fetch(`${API_BASE_URL}/api/tasks`, {
    headers: commonHeaders,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get tasks');
  }

  return response.json();
}
