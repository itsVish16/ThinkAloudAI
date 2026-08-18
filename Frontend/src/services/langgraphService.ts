// src/services/langgraphService.ts
import { apiClient } from './apiClient';

const API_URL = import.meta.env.VITE_API_URL || '';

export async function generateLanggraphToken(_sessionId?: string): Promise<string> {
  const token = localStorage.getItem('access_token');
  return token || '';
}

export async function getUserProfile(token?: string): Promise<any> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient.fetchWithAuth(`${API_URL}/users/profile`, {
    method: 'GET',
    headers: Object.keys(headers).length > 0 ? headers : undefined,
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }

  return response.json();
}
