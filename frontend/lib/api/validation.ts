/**
 * API Client for Validation and Feedback
 */

import { ValidationResult, FeedbackSubmission, FeedbackSubmitResponse, FeedbackAnalytics } from '@/types/validation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Validate a single clause on-demand
 * 
 * IMPORTANT: Does NOT require API key from frontend.
 * Validation uses server-side credentials for security and consistency.
 */
export async function validateClause(
    clauseText: string,
    clauseCategory: string,
    riskScore: number,
    riskExplanation: string,
    fullDocumentText?: string
): Promise<ValidationResult> {
    const formData = new FormData();
    formData.append('clause_text', clauseText);
    formData.append('clause_category', clauseCategory);
    formData.append('risk_score', riskScore.toString());
    formData.append('risk_explanation', riskExplanation);

    if (fullDocumentText) {
        formData.append('full_document_text', fullDocumentText);
    }

    const response = await fetch(`${API_BASE_URL}/api/validation/validate-clause`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Validation failed' }));
        throw new Error(error.detail || 'Validation failed');
    }

    return response.json();
}

/**
 * Submit user feedback for a validation result
 * 
 * IMPORTANT: Feedback is non-blocking:
 * - 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
 * - 👎 follow-up: Optional and dismissible (user can close without answering)
 */
export async function submitFeedback(
    feedback: FeedbackSubmission
): Promise<FeedbackSubmitResponse> {
    const formData = new FormData();
    formData.append('validation_result_id', feedback.validation_result_id);
    formData.append('thumbs_up', feedback.thumbs_up.toString());

    if (feedback.follow_up_reason) {
        formData.append('follow_up_reason', feedback.follow_up_reason);
    }

    if (feedback.additional_comments) {
        formData.append('additional_comments', feedback.additional_comments);
    }

    if (feedback.user_accepted_clause !== undefined) {
        formData.append('user_accepted_clause', feedback.user_accepted_clause.toString());
    }

    const response = await fetch(`${API_BASE_URL}/api/feedback/submit`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Feedback submission failed' }));
        throw new Error(error.detail || 'Feedback submission failed');
    }

    return response.json();
}

/**
 * Get feedback analytics
 */
export async function getFeedbackAnalytics(
    timeRange: string = '7d'
): Promise<FeedbackAnalytics> {
    const response = await fetch(
        `${API_BASE_URL}/api/feedback/analytics?time_range=${timeRange}`
    );

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to fetch analytics' }));
        throw new Error(error.detail || 'Failed to fetch analytics');
    }

    return response.json();
}
