import { apiClient } from './apiClient';

const API_URL = import.meta.env.VITE_API_URL || '';

export interface LeaderboardUser {
  rank: number;
  candidate_name: string;
  score: number;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardUser[];
  me: LeaderboardUser;
}

export async function getLiveLeaderboard(token: string): Promise<LeaderboardResponse> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/api/leaderboard`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch leaderboard');
  }
  
  return response.json();
}
