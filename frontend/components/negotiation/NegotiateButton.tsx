/**
 * Negotiate Button Component
 * Triggers negotiation for high-risk clauses
 */
'use client';

import { useState } from 'react';
import { ClauseRiskScore, NegotiationResult, NegotiationRequest } from '@/types/pdf';
import { negotiateClause } from '@/lib/api/negotiation';
import { Button } from '@/components/ui/button';
import { NegotiationDialog } from './NegotiationDialog';
import { MessageSquare, Loader2 } from 'lucide-react';

interface NegotiateButtonProps {
    clause: ClauseRiskScore;
    onNegotiationComplete?: (result: NegotiationResult) => void;
}

export function NegotiateButton({ clause, onNegotiationComplete }: NegotiateButtonProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<NegotiationResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Only show for high-risk clauses (severity >= 70)
    if (clause.severity < 70) {
        return null;
    }

    const handleNegotiate = async () => {
        setIsOpen(true);
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            // Prepare negotiation request
            const request: NegotiationRequest = {
                clause_text: clause.clause_text,
                clause_label: clause.category,
                risk_score: clause.severity,
                risk_explanation: clause.risk_explanation,
            };

            // Call negotiation API
            const negotiationResult = await negotiateClause(request);

            setResult(negotiationResult);
            setIsLoading(false);

            // Callback for parent component
            if (onNegotiationComplete) {
                onNegotiationComplete(negotiationResult);
            }
        } catch (err) {
            console.error('Negotiation failed:', err);
            setError(err instanceof Error ? err.message : 'Failed to negotiate clause. Please try again.');
            setIsLoading(false);
        }
    };

    const handleOpenChange = (open: boolean) => {
        setIsOpen(open);
        // Reset state when dialog closes
        if (!open && !isLoading) {
            setResult(null);
            setError(null);
        }
    };

    return (
        <>
            <Button
                onClick={handleNegotiate}
                variant="outline"
                size="sm"
                className="gap-2"
                disabled={isLoading}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Negotiating...
                    </>
                ) : (
                    <>
                        <MessageSquare className="w-4 h-4" />
                        Negotiate
                    </>
                )}
            </Button>

            <NegotiationDialog
                open={isOpen}
                onOpenChange={handleOpenChange}
                result={result}
                isLoading={isLoading}
                error={error}
            />
        </>
    );
}
