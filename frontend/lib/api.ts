/**
 * API client for backend communication.
 * Provides typed functions for all FastAPI endpoints.
 */

// Backend API URL - hardcoded as per requirements (no .env)
const API_BASE_URL = 'http://localhost:8000';

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
  emails_in_batch: number;
  analysis?: string;
  error?: string;
  processed_at: string;
}

export interface TaskStatus {
  task_id: string;
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
  const response = await fetch(`${API_BASE_URL}/api/status/${taskId}`);

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
  const response = await fetch(`${API_BASE_URL}/api/senders`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get senders');
  }

  return response.json();
}
