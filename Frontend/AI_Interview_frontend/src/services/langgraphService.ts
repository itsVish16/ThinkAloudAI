// src/services/langgraphService.ts
import { apiClient } from './apiClient';

const API_URL = import.meta.env.VITE_API_URL || '';

export async function generateLanggraphToken(sessionId: string): Promise<string> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error('Failed to generate LangGraph token');
  }

  const data = await response.json();
  return data.access_token;
}

export async function getUserProfile(token: string): Promise<any> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/users/profile`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }

  return response.json();
}
