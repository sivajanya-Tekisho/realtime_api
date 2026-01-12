
export type ViewState = 'overview' | 'realtime' | 'transcripts' | 'knowledge' | 'analytics' | 'settings' | 'outbound';

export interface TranscriptPart {
  speaker: 'user' | 'ai';
  text: string;
  timestamp: string;
}

export interface CallMetric {
  id: string;
  timestamp: string;
  duration: number;
  status: 'answered' | 'missed' | 'dropped' | 'active';
  intent: 'appointment' | 'support' | 'order' | 'inquiry' | 'unknown';
  confidence: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  caller: string;
  language: string;
  summary?: string;
  transcript?: TranscriptPart[];
}

export interface ChartData {
  name: string;
  value: number;
  secondary?: number;
}

export interface BusinessMetric {
  label: string;
  value: string | number;
  change: number;
  trend: 'up' | 'down';
  sparkline?: number[];
}

export interface BusinessDataMetrics {
  apiSuccessRate: number;
  avgFetchTime: number;
  actions: { name: string; value: number }[];
}

export interface CallerInsights {
  newCallers: number;
  returningCallers: number;
  frequencyData: { name: string; value: number }[];
}
