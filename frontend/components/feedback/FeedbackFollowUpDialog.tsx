/**
 * FeedbackFollowUpDialog Component
 * 
 * Modal for collecting follow-up feedback when user clicks thumbs down
 * 
 * IMPORTANT: This dialog is DISMISSIBLE - user can close without answering
 * to avoid feedback fatigue
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import { FeedbackReason } from '@/types/validation';

interface FeedbackFollowUpDialogProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (reason: FeedbackReason, comments?: string) => void;
}

export function FeedbackFollowUpDialog({ open, onClose, onSubmit }: FeedbackFollowUpDialogProps) {
    const [selectedReason, setSelectedReason] = useState<FeedbackReason | null>(null);
    const [additionalComments, setAdditionalComments] = useState('');

    if (!open) return null;

    const handleSubmit = () => {
        if (selectedReason) {
            onSubmit(selectedReason, additionalComments || undefined);
            onClose();
            // Reset form
            setSelectedReason(null);
            setAdditionalComments('');
        }
    };

    const handleClose = () => {
        onClose();
        // Reset form
        setSelectedReason(null);
        setAdditionalComments('');
    };

    const reasons: { value: FeedbackReason; label: string; description: string }[] = [
        {
            value: 'too_strict',
            label: 'Too strict',
            description: 'The validation was overly cautious or flagged things that aren\'t really issues',
        },
        {
            value: 'too_risky',
            label: 'Too risky',
            description: 'The validation missed important risks or concerns',
        },
        {
            value: 'not_clear',
            label: 'Not clear',
            description: 'The explanation or issues weren\'t clear or helpful',
        },
        {
            value: 'wrong_intent',
            label: 'Didn\'t match my intent',
            description: 'The validation didn\'t understand the context or purpose of the clause',
        },
        {
            value: 'other',
            label: 'Other',
            description: 'Something else was wrong',
        },
    ];

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
                onClick={handleClose}
            >
                {/* Dialog */}
                <div
                    className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 relative"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Close button */}
                    <button
                        onClick={handleClose}
                        className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5" />
                    </button>

                    {/* Title */}
                    <h2 className="text-lg font-semibold text-gray-900 mb-2">
                        Help us improve
                    </h2>
                    <p className="text-sm text-gray-600 mb-4">
                        What went wrong with this validation? (Optional - you can skip this)
                    </p>

                    {/* Reason options */}
                    <div className="space-y-2 mb-4">
                        {reasons.map((reason) => (
                            <label
                                key={reason.value}
                                className={`flex items-start gap-3 p-3 rounded-lg border-2 cursor-pointer transition ${selectedReason === reason.value
                                        ? 'border-blue-500 bg-blue-50'
                                        : 'border-gray-200 hover:border-gray-300'
                                    }`}
                            >
                                <input
                                    type="radio"
                                    name="feedback-reason"
                                    value={reason.value}
                                    checked={selectedReason === reason.value}
                                    onChange={() => setSelectedReason(reason.value)}
                                    className="mt-1 text-blue-600 focus:ring-blue-500"
                                />
                                <div className="flex-1">
                                    <div className="text-sm font-medium text-gray-900">{reason.label}</div>
                                    <div className="text-xs text-gray-600">{reason.description}</div>
                                </div>
                            </label>
                        ))}
                    </div>

                    {/* Additional comments */}
                    <div className="mb-4">
                        <label htmlFor="additional-comments" className="block text-sm font-medium text-gray-700 mb-2">
                            Additional comments (optional)
                        </label>
                        <textarea
                            id="additional-comments"
                            rows={3}
                            value={additionalComments}
                            onChange={(e) => setAdditionalComments(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                            placeholder="Any other feedback you'd like to share..."
                        />
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 justify-end">
                        <button
                            onClick={handleClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
                        >
                            Skip
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={!selectedReason}
                            className={`px-4 py-2 text-sm font-medium text-white rounded-md transition ${selectedReason
                                    ? 'bg-blue-600 hover:bg-blue-700'
                                    : 'bg-gray-300 cursor-not-allowed'
                                }`}
                        >
                            Submit
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
}
