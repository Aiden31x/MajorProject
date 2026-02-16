/**
 * ValidationFeedback Component
 * 
 * Main feedback component with 👍/👎 buttons
 * 
 * IMPORTANT: Feedback is non-blocking:
 * - 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
 * - 👎 follow-up: Optional and dismissible (user can close without answering)
 * This avoids feedback fatigue and annoying users
 */

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react';
import { FeedbackFollowUpDialog } from './FeedbackFollowUpDialog';
import { submitFeedback } from '@/lib/api/validation';
import { FeedbackReason } from '@/types/validation';

interface ValidationFeedbackProps {
    validationResultId: string;
    validationStatus: 'PASS' | 'WARN' | 'FAIL';
    clauseText: string;
    onFeedbackSubmitted?: () => void;
}

export function ValidationFeedback({
    validationResultId,
    validationStatus,
    clauseText,
    onFeedbackSubmitted,
}: ValidationFeedbackProps) {
    const [hasVoted, setHasVoted] = useState(false);
    const [voteType, setVoteType] = useState<'up' | 'down' | null>(null);
    const [showFollowUp, setShowFollowUp] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Handle thumbs up - fire and forget
    const handleThumbsUp = async () => {
        if (hasVoted) return;

        setIsSubmitting(true);
        setError(null);

        try {
            await submitFeedback({
                validation_result_id: validationResultId,
                thumbs_up: true,
            });

            setHasVoted(true);
            setVoteType('up');
            onFeedbackSubmitted?.();
        } catch (err) {
            console.error('Error submitting feedback:', err);
            setError('Failed to submit feedback. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Handle thumbs down - show follow-up dialog
    const handleThumbsDown = () => {
        if (hasVoted) return;

        setHasVoted(true);
        setVoteType('down');
        setShowFollowUp(true);
    };

    // Handle follow-up submission (optional)
    const handleFollowUpSubmit = async (reason: FeedbackReason, comments?: string) => {
        setIsSubmitting(true);
        setError(null);

        try {
            await submitFeedback({
                validation_result_id: validationResultId,
                thumbs_up: false,
                follow_up_reason: reason,
                additional_comments: comments,
            });

            onFeedbackSubmitted?.();
        } catch (err) {
            console.error('Error submitting follow-up feedback:', err);
            setError('Failed to submit feedback details.');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Handle follow-up dialog close without submission
    const handleFollowUpClose = async () => {
        setShowFollowUp(false);

        // Submit basic thumbs down if they skipped the follow-up
        if (!isSubmitting) {
            setIsSubmitting(true);
            try {
                await submitFeedback({
                    validation_result_id: validationResultId,
                    thumbs_up: false,
                });

                onFeedbackSubmitted?.();
            } catch (err) {
                console.error('Error submitting feedback:', err);
            } finally {
                setIsSubmitting(false);
            }
        }
    };

    return (
        <div className="mt-3">
            <div className="flex items-center gap-3">
                <div className="text-xs text-gray-600">Was this validation helpful?</div>

                <div className="flex items-center gap-2">
                    {/* Thumbs Up Button */}
                    <button
                        onClick={handleThumbsUp}
                        disabled={hasVoted || isSubmitting}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition ${voteType === 'up'
                                ? 'bg-green-100 text-green-700 border border-green-300'
                                : hasVoted
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'bg-gray-50 text-gray-700 hover:bg-green-50 hover:text-green-600 border border-gray-200'
                            }`}
                        aria-label="Thumbs up"
                    >
                        {voteType === 'up' ? (
                            <>
                                <Check className="w-4 h-4" />
                                <span>Thanks!</span>
                            </>
                        ) : (
                            <>
                                <ThumbsUp className="w-4 h-4" />
                                <span>Yes</span>
                            </>
                        )}
                    </button>

                    {/* Thumbs Down Button */}
                    <button
                        onClick={handleThumbsDown}
                        disabled={hasVoted || isSubmitting}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition ${voteType === 'down'
                                ? 'bg-red-100 text-red-700 border border-red-300'
                                : hasVoted
                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    : 'bg-gray-50 text-gray-700 hover:bg-red-50 hover:text-red-600 border border-gray-200'
                            }`}
                        aria-label="Thumbs down"
                    >
                        <ThumbsDown className="w-4 h-4" />
                        <span>No</span>
                    </button>
                </div>
            </div>

            {error && (
                <div className="mt-2 text-xs text-red-600">{error}</div>
            )}

            {/* Follow-up Dialog */}
            <FeedbackFollowUpDialog
                open={showFollowUp}
                onClose={handleFollowUpClose}
                onSubmit={handleFollowUpSubmit}
            />
        </div>
    );
}
