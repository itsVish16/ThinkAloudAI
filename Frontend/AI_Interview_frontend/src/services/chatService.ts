import { apiClient } from './apiClient';
export interface APIMessage {
  id: number;
  session_id: string;
  role: 'assistant' | 'user';
  content: string;
  created_at: string;
}

export interface APISession {
  id: string;
  title?: string;
  created_at: string;
}

const API_URL = import.meta.env.VITE_API_URL || '';

export async function getSessions(): Promise<APISession[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/sessions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  }
  return response.json();
}

export async function getSessionMessages(sessionId: string): Promise<APIMessage[]> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/sessions/${sessionId}/messages`);
  if (!response.ok) {
    throw new Error(`Failed to fetch messages for session ${sessionId}: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await apiClient.fetchWithAuth(`${API_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete session ${sessionId}: ${response.statusText}`);
  }
}

export async function startChatStream(
  sessionId: string,
  message: string,
  onChunk: (token: string) => void,
  onToolStart: (toolName: string, input: any) => void,
  onToolEnd: (toolName: string, output: string) => void,
  onError: (msg: string) => void,
  images?: string[]
) {
  try {
    const response = await apiClient.fetchWithAuth(`${API_URL}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
        ...(images && images.length > 0 && { images })
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("No readable stream available.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      // Decode the buffer chunk
      buffer += decoder.decode(value, { stream: true });

      // Process lines split by single newlines (handling \r\n as well)
      const lines = buffer.split(/\r?\n/);
      
      // Save the last incomplete line back to the buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          const rawData = trimmed.slice(6).trim();
          if (!rawData) continue;

          try {
            const event = JSON.parse(rawData);

            switch (event.type) {
              case "token":
                onChunk(event.content);
                break;
              case "tool_start":
                onToolStart(event.tool, event.input);
                break;
              case "tool_end":
                onToolEnd(event.tool, event.output);
                break;
              case "error":
                onError(event.message);
                break;
            }
          } catch (err) {
            console.error("Error parsing SSE line json:", err, line);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message);
  }
}
