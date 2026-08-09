import { apiClient } from './apiClient';

export interface APIDSAQuestion {
  id: number | string;
  title: string;
  description: string;
  difficulty: 'Easy' | 'Medium' | 'Hard' | string;
  test_cases: string; // stringified JSON
  python_starter_code?: string;
  cpp_starter_code?: string;
  cpp_test_harness?: string;
  function_name?: string;
  hints?: string;
  optimal_time_complexity?: string;
  optimal_space_complexity?: string;
  category?: string;
  created_at: string;
}

export interface CodeSubmitResponse {
  status: string;
  passed_tests: number;
  total_tests: number;
  error_message: string | null;
  execution_time_ms: number;
}

const API_URL = import.meta.env.VITE_API_URL || '';

export async function getDSAQuestions(): Promise<APIDSAQuestion[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/questions`);
  if (!response.ok) {
    throw new Error('Failed to fetch DSA questions');
  }
  return response.json();
}

export async function getDSAQuestionById(id: string | number): Promise<APIDSAQuestion> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/questions/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch DSA question ${id}`);
  }
  return response.json();
}

export async function submitDSACode(id: string | number, code: string, language: string, sessionId: string): Promise<CodeSubmitResponse> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/questions/${id}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, language, code }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to submit code for question ${id}`);
  }
  return response.json();
}
export async function getLatestSubmission(id: string | number, language?: string): Promise<{ code: string; status: string } | null> {
  const url = new URL(`${API_URL}/dsa/questions/${id}/submission`);
  if (language) {
    url.searchParams.append('language', language);
  }
  const response = await apiClient.fetchWithAuth(url.toString());
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new Error(`Failed to fetch latest submission for question ${id}`);
  }
  return response.json();
}

export async function getQuestionSubmissions(id: string | number, sessionId: string): Promise<any[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/questions/${id}/submissions/${sessionId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch submissions for question ${id}`);
  }
  return response.json();
}

export async function getUserSubmissions(sessionId: string): Promise<any[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/submissions/${sessionId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch submissions for user`);
  }
  return response.json();
}

export async function runDSACode(id: string | number, code: string, language: string, sessionId: string): Promise<CodeSubmitResponse> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/questions/${id}/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, language, code }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to run code for question ${id}`);
  }
  return response.json();
}

export async function getDSAProfileStats(token: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/users/profile`);
  if (!response.ok) {
    throw new Error('Failed to fetch DSA profile stats');
  }
  return response.json();
}

export async function getUserProblemStatus(token: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/status`);
  if (!response.ok) throw new Error('Failed to fetch problem status');
  return response.json();
}

export async function getRecommendations(token: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/dsa/recommendations`);
  if (!response.ok) throw new Error('Failed to fetch recommendations');
  return response.json();
}

export async function submitSystemDesign(id: string | number, answer: string, token: string, base64Image?: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/system-design/questions/${id}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ answer_text: answer, image_data: base64Image })
  });
  if (!response.ok) throw new Error('Failed to submit system design');
  return response.json();
}
