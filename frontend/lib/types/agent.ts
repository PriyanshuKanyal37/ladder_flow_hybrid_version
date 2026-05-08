export interface AgentConfigRequest {
  topic: string;
  userName?: string;
  topic_title?: string;
  global_context?: string;
  why_this_matters?: string;
  key_questions?: string[];
  tts_provider?: string;
}

export interface LiveKitSession {
  provider?: 'livekit';
  token: string;
  livekitUrl: string;
  roomName: string;
  topicTitle: string;
  userName: string;
  greeting: string;
  interviewId: string;
  resumed?: boolean;
  priorTranscript?: string;
  researchContext?: Record<string, unknown>;
}

export type AgentConfigResponse = LiveKitSession;

export interface AgentDispatchRequest {
  interview_id: string;
}

export interface AgentDispatchResponse {
  status: 'dispatched' | 'already_dispatched' | 'not_required';
  roomName: string;
}
