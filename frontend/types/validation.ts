/**
 * Validation and Feedback Types for ClauseCraft
 */

export interface ValidationIssue {
    issue_type: string;
    severity: 'critical' | 'major' | 'minor';
    description: string;
    location_hint: string;
}

export interface ValidationResult {
    id: string;
    clause_text: string;
    status: 'PASS' | 'WARN' | 'FAIL';
    confidence: number;
    issues: ValidationIssue[];
    timestamp: string;
    validation_time_ms: number;
}

export type FeedbackReason = 'too_strict' | 'too_risky' | 'not_clear' | 'wrong_intent' | 'other';

export interface FeedbackSubmission {
    validation_result_id: string;
    thumbs_up: boolean;
    follow_up_reason?: FeedbackReason;
    additional_comments?: string;
    user_accepted_clause?: boolean;
}

export interface FeedbackSubmitResponse {
    feedback_id: string;
    message: string;
}

export interface FeedbackAnalytics {
    total_feedback: number;
    thumbs_up_count: number;
    thumbs_down_count: number;
    top_issues: Record<string, number>;
    accuracy_by_decision: Record<string, number>;
}
