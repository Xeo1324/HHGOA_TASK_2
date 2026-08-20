import { QueryResponse, VoiceQueryResponse } from '../types';

export const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export async function checkHealth(apiBaseUrl: string = DEFAULT_API_BASE_URL): Promise<boolean> {
  try {
    const res = await fetch(`${apiBaseUrl}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) return false;
    const data = await res.json();
    // Accept both "ok" (fully ready) and "starting" (warming up after port binds)
    return data.status === 'ok' || data.status === 'starting';
  } catch (err) {
    return false;
  }
}

export async function queryText({
  query,
  top_k = 5,
  chunking_strategy = 'sentence',
  retrieval_mode = 'hybrid_rerank',
  previous_query,
  apiBaseUrl = DEFAULT_API_BASE_URL,
}: {
  query: string;
  top_k?: number;
  chunking_strategy?: string;
  retrieval_mode?: string;
  previous_query?: string;
  apiBaseUrl?: string;
}): Promise<QueryResponse> {
  const res = await fetch(`${apiBaseUrl}/v1/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      query,
      top_k,
      chunking_strategy,
      retrieval_mode,
      previous_query,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export async function queryVoice({
  audioBlob,
  language,
  top_k = 5,
  chunking_strategy = 'sentence',
  retrieval_mode = 'hybrid_rerank',
  synthesize_audio = true,
  previous_query,
  apiBaseUrl = DEFAULT_API_BASE_URL,
}: {
  audioBlob: Blob;
  language?: string;
  top_k?: number;
  chunking_strategy?: string;
  retrieval_mode?: string;
  synthesize_audio?: boolean;
  previous_query?: string;
  apiBaseUrl?: string;
}): Promise<VoiceQueryResponse> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.wav');
  if (language && language !== 'auto') {
    formData.append('language', language);
  }
  formData.append('top_k', top_k.toString());
  formData.append('chunking_strategy', chunking_strategy);
  formData.append('retrieval_mode', retrieval_mode);
  formData.append('synthesize_audio', synthesize_audio ? 'true' : 'false');
  if (previous_query) {
    formData.append('previous_query', previous_query);
  }

  const res = await fetch(`${apiBaseUrl}/v1/voice/query`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Voice query failed with status ${res.status}`);
  }

  return res.json();
}

export async function synthesizeSpeech({
  text,
  language = 'en',
  apiBaseUrl = DEFAULT_API_BASE_URL,
}: {
  text: string;
  language?: string;
  apiBaseUrl?: string;
}): Promise<Blob> {
  const res = await fetch(`${apiBaseUrl}/v1/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      language: language === 'auto' ? 'en' : language,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `TTS synthesis failed with status ${res.status}`);
  }

  return res.blob();
}
