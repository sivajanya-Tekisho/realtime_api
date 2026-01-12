import { CallMetric, BusinessDataMetrics, ChartData } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1'; // Adjust if needed

export const api = {
    async getAnalytics(): Promise<{
        total_calls: number;
        completed_calls: number;
        missed_calls: number;
        avg_duration: number;
        intent_distribution: Record<string, number>;
        calls_by_hour: { name: string; value: number }[];
    }> {
        const response = await fetch(`${API_BASE_URL}/calls/analytics`);
        if (!response.ok) throw new Error('Failed to fetch analytics');
        return response.json();
    },

    async getCalls(skip = 0, limit = 100): Promise<CallMetric[]> {
        const response = await fetch(`${API_BASE_URL}/calls/?skip=${skip}&limit=${limit}`);
        if (!response.ok) throw new Error('Failed to fetch calls');
        return response.json();
    },

    async getActiveCalls(): Promise<CallMetric[]> {
        const response = await fetch(`${API_BASE_URL}/calls/active`);
        if (!response.ok) throw new Error('Failed to fetch active calls');
        return response.json();
    },

    async getCallDetails(callId: string): Promise<CallMetric> {
        const response = await fetch(`${API_BASE_URL}/calls/${callId}`);
        if (!response.ok) throw new Error('Failed to fetch call details');
        return response.json();
    }
};
