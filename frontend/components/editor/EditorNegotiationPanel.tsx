"use client";

import { useState } from 'react';
import { EditorClausePosition, NegotiationRound } from '@/types/editor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import axios from 'axios';
import { ValidationStatusBadge } from '@/components/feedback/ValidationStatusBadge';
import { ValidationIssuesList } from '@/components/feedback/ValidationIssuesList';
import { ValidationFeedback } from '@/components/feedback/ValidationFeedback';

interface EditorNegotiationPanelProps {
    selectedClause: EditorClausePosition | null;
    apiKey: string;
    onAcceptSuggestion: (newText: string) => void;
}

interface NegotiationResponse {
    clause_text: string;
    clause_label: string;
    risk_score: number;
    risk_explanation: string;
    stance: string;
    rounds: NegotiationRound[];
    timestamp: string;
}

export function EditorNegotiationPanel({
    selectedClause,
    apiKey,
    onAcceptSuggestion,
}: EditorNegotiationPanelProps) {
    const [suggestions, setSuggestions] = useState<NegotiationRound[] | null>(null);
    const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleGetSuggestions = async () => {
        if (!selectedClause || !apiKey) return;

        setIsLoadingSuggestions(true);
        setError(null);
        setSuggestions(null);

        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            const formData = new FormData();
            formData.append('clause_text', selectedClause.clause_text);
            formData.append('clause_label', selectedClause.risk_category);
            formData.append('risk_score', selectedClause.risk_score.toString());
            formData.append('risk_explanation', selectedClause.risk_explanation);
            formData.append('gemini_api_key', apiKey);

            const response = await axios.post<NegotiationResponse>(
                `${API_BASE_URL}/api/negotiation/negotiate`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    timeout: 60000, // 1 minute
                }
            );

            setSuggestions(response.data.rounds);
        } catch (err: any) {
            console.error('Error fetching suggestions:', err);
            setError(err.response?.data?.detail || 'Failed to get negotiation suggestions');
        } finally {
            setIsLoadingSuggestions(false);
        }
    };

    const handleAccept = (round: NegotiationRound) => {
        onAcceptSuggestion(round.counter_clause);
        // Clear suggestions after accepting
        setSuggestions(null);
    };

    if (!selectedClause) {
        return (
            <div className="p-6 text-center text-muted-foreground">
                <p>Click on a highlighted clause to view details and get suggestions</p>
            </div>
        );
    }

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'High':
                return 'text-red-600 bg-red-50 border-red-200';
            case 'Medium':
                return 'text-yellow-600 bg-yellow-50 border-yellow-200';
            case 'Low':
                return 'text-green-600 bg-green-50 border-green-200';
            default:
                return 'text-gray-600 bg-gray-50 border-gray-200';
        }
    };

    return (
        <ScrollArea className="h-full">
            <div className="p-4 space-y-4">
                {/* Selected Clause Details */}
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Selected Clause</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {/* Risk Badge */}
                        <div className={`inline-flex items-center px-3 py-1 rounded-full border ${getSeverityColor(selectedClause.risk_severity)}`}>
                            <AlertTriangle className="h-4 w-4 mr-2" />
                            <span className="font-semibold">{selectedClause.risk_severity} Risk</span>
                            <span className="ml-2 text-sm">({selectedClause.risk_score.toFixed(0)}%)</span>
                        </div>

                        {/* Category */}
                        <div>
                            <p className="text-sm font-semibold text-muted-foreground">Category</p>
                            <p className="text-sm capitalize">{selectedClause.risk_category.replace('_', ' ')}</p>
                        </div>

                        {/* Clause Text */}
                        <div>
                            <p className="text-sm font-semibold text-muted-foreground">Clause Text</p>
                            <p className="text-sm bg-slate-50 p-2 rounded border">
                                {selectedClause.clause_text}
                            </p>
                        </div>

                        {/* Explanation */}
                        <div>
                            <p className="text-sm font-semibold text-muted-foreground">Why This Is Risky</p>
                            <p className="text-sm">{selectedClause.risk_explanation}</p>
                        </div>

                        {/* Recommended Action */}
                        <div>
                            <p className="text-sm font-semibold text-muted-foreground">Recommended Action</p>
                            <p className="text-sm">{selectedClause.recommended_action}</p>
                        </div>

                        {/* Get Suggestions Button */}
                        {!suggestions && (
                            <Button
                                onClick={handleGetSuggestions}
                                disabled={isLoadingSuggestions}
                                className="w-full"
                            >
                                {isLoadingSuggestions ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Generating Suggestions...
                                    </>
                                ) : (
                                    'Get Negotiation Suggestions'
                                )}
                            </Button>
                        )}

                        {error && (
                            <div className="bg-destructive/10 text-destructive p-3 rounded text-sm">
                                {error}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Negotiation Suggestions */}
                {suggestions && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">Negotiation Suggestions</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                3 rounds from ideal to fallback position
                            </p>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {suggestions.map((round) => (
                                <div key={round.round_number} className="border rounded-lg p-4 space-y-3">
                                    {/* Round Header */}
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h4 className="font-semibold">
                                                Round {round.round_number + 1}
                                                {round.round_number === 0 && ' (Ideal)'}
                                                {round.round_number === 1 && ' (Alternative)'}
                                                {round.round_number === 2 && ' (Fallback)'}
                                            </h4>
                                            <p className="text-sm text-muted-foreground">
                                                Est. Risk Reduction: {round.risk_reduction.toFixed(0)}%
                                            </p>
                                        </div>
                                        <Button
                                            size="sm"
                                            onClick={() => handleAccept(round)}
                                            variant={round.round_number === 0 ? 'default' : 'outline'}
                                        >
                                            <CheckCircle2 className="h-4 w-4 mr-1" />
                                            Accept
                                        </Button>
                                    </div>

                                    {/* Counter Clause */}
                                    <div>
                                        <p className="text-sm font-semibold text-muted-foreground mb-1">
                                            Proposed Clause
                                        </p>
                                        <p className="text-sm bg-green-50 p-2 rounded border border-green-200">
                                            {round.counter_clause}
                                        </p>
                                    </div>

                                    {/* Justification */}
                                    <div>
                                        <p className="text-sm font-semibold text-muted-foreground mb-1">
                                            Justification
                                        </p>
                                        <p className="text-sm">{round.justification}</p>
                                    </div>

                                    {/* Validation Section */}
                                    {round.validation_result && (
                                        <div className="space-y-2 pt-2 border-t">
                                            <p className="text-xs font-semibold text-slate-600">
                                                Validation Analysis:
                                            </p>

                                            <ValidationStatusBadge
                                                status={round.validation_result.status}
                                                confidence={round.validation_result.confidence}
                                            />

                                            {round.validation_result.issues && round.validation_result.issues.length > 0 && (
                                                <ValidationIssuesList issues={round.validation_result.issues} />
                                            )}

                                            <ValidationFeedback
                                                validationResultId={round.validation_result.id}
                                                validationStatus={round.validation_result.status}
                                                clauseText={round.counter_clause}
                                                onFeedbackSubmitted={() => {
                                                    console.log('Feedback submitted for negotiation round validation');
                                                }}
                                            />
                                        </div>
                                    )}

                                    {/* Rejection Text (if exists) */}
                                    {round.rejection_text && (
                                        <div className="bg-slate-50 p-2 rounded">
                                            <p className="text-xs font-semibold text-muted-foreground mb-1">
                                                If rejected by landlord:
                                            </p>
                                            <p className="text-xs italic">{round.rejection_text}</p>
                                        </div>
                                    )}
                                </div>
                            ))}

                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setSuggestions(null)}
                                className="w-full"
                            >
                                <XCircle className="h-4 w-4 mr-2" />
                                Close Suggestions
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </div>
        </ScrollArea>
    );
}
