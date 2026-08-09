import { apiClient } from './apiClient';

export interface APIInterviewType {
  id: string;
  name: string;
  description: string;
}

export interface APIInterviewTypesResponse {
  types: APIInterviewType[];
}

const API_URL = import.meta.env.VITE_API_URL || '';

export async function getInterviewTypes(): Promise<APIInterviewType[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/interview-types`);
  if (!response.ok) {
    throw new Error('Failed to fetch interview types');
  }
  const data: APIInterviewTypesResponse = await response.json();
  return data.types;
}

export async function getMyInterviews(token: string): Promise<any[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/interviews/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!response.ok) {
    throw new Error('Failed to fetch past interviews');
  }
  return response.json();
}

export async function getInterviewDetails(token: string, sessionId: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/interview/${sessionId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!response.ok) {
    throw new Error('Failed to fetch interview details');
  }
  return response.json();
}

export async function endInterview(token: string, sessionId: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/interview/${sessionId}/end`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  if (!response.ok) {
    throw new Error('Failed to force end interview');
  }
  return response.json();
}

export async function getInterviewAnalytics(token: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/interviews/me/analytics`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!response.ok) {
    throw new Error('Failed to fetch interview analytics');
  }
  return response.json();
}
