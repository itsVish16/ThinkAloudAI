const API_URL = import.meta.env.VITE_API_URL || '';

export interface RoadmapItem {
  id: number;
  topic_id: number;
  title: string;
  content_type: string;
  content_id: string | null;
  timeline_days: number;
  is_completed: boolean;
}

import { apiClient } from './apiClient';

export interface RoadmapTopic {
  id: number;
  roadmap_id: number;
  title: string;
  description: string;
  order_index: number;
  items: RoadmapItem[];
}

export interface Roadmap {
  id: number;
  user_id: string;
  title: string;
  description: string;
  created_at: string;
  topics: RoadmapTopic[];
}

export interface ScheduledInterview extends RoadmapItem {
  roadmap_title: string;
  topic_title: string;
  roadmap_id: number;
}

export async function getRoadmaps(): Promise<Roadmap[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/roadmaps`);
  if (!response.ok) {
    throw new Error('Failed to fetch roadmaps');
  }
  return response.json();
}

export async function getScheduledInterviews(): Promise<ScheduledInterview[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/roadmaps/interviews/scheduled`);
  if (!response.ok) {
    throw new Error('Failed to fetch scheduled interviews');
  }
  return response.json();
}

export async function toggleRoadmapItem(roadmapId: number, topicId: number, itemId: number): Promise<RoadmapItem> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/roadmaps/${roadmapId}/topics/${topicId}/items/${itemId}/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error('Failed to toggle roadmap item');
  }
  return response.json();
}

export async function deleteRoadmap(roadmapId: number): Promise<void> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/roadmaps/${roadmapId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete roadmap');
  }
}
