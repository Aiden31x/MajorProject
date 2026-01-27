/**
 * Negotiation API Functions
 */
import { apiClient } from './client';

// Types for negotiation
export interface NegotiationRequest {
    clause_text: string;
    clause_label: string;
    risk_score: number;
    risk_explanation: string;
}

export interface NegotiationRound {
    round_number: number;
    counter_clause: string;
    justification: string;
    risk_reduction: number;
    rejection_text: string | null;
}

export interface NegotiationResult {
    clause_text: string;
    clause_label: string;
    risk_score: number;
    risk_explanation: string;
    stance: 'Defensive' | 'Balanced' | 'Soft';
    rounds: NegotiationRound[];
    timestamp: string;
}

/**
 * Request 3-round negotiation for a risky lease clause
 */
export async function negotiateClause(request: NegotiationRequest): Promise<NegotiationResult> {
    const response = await apiClient.post<NegotiationResult>('/api/negotiation/negotiate', request, {
        timeout: 60000, // 1 minute for 3 LLM calls
    });

    return response.data;
}

/**
 * Health check for negotiation service
 */
export async function checkNegotiationHealth(): Promise<{ status: string; service: string; description: string }> {
    const response = await apiClient.get('/api/negotiation/health');
    return response.data;
}
