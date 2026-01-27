/**
 * Negotiation Dialog Component
 * Displays 3-round negotiation results in a modal dialog
 */
'use client';

import { NegotiationResult } from '@/types/pdf';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, MessageSquare, Shield, AlertCircle, TrendingDown, X } from 'lucide-react';

interface NegotiationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    result: NegotiationResult | null;
    isLoading?: boolean;
    error?: string | null;
}

export function NegotiationDialog({
    open,
    onOpenChange,
    result,
    isLoading = false,
    error = null,
}: NegotiationDialogProps) {

    // Helper to get stance variant
    const getStanceVariant = (stance: string): "destructive" | "default" | "secondary" => {
        switch (stance) {
            case 'Defensive':
                return 'destructive';
            case 'Balanced':
                return 'default';
            case 'Soft':
                return 'secondary';
            default:
                return 'default';
        }
    };

    const getRoundTypeLabel = (roundNumber: number): string => {
        switch (roundNumber) {
            case 0:
                return 'Ideal Proposal';
            case 1:
                return 'Alternative Approach';
            case 2:
                return 'Final Compromise';
            default:
                return `Round ${roundNumber}`;
        }
    };

    const getRoundIcon = (roundNumber: number) => {
        switch (roundNumber) {
            case 0:
                return '🎯';
            case 1:
                return '🔄';
            case 2:
                return '🤝';
            default:
                return '💬';
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-[80vw] w-[80vw] max-h-[90vh] flex flex-col p-0">
                <div className="px-6 pt-6 pb-4 border-b">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <MessageSquare className="w-5 h-5" />
                            Lease Clause Negotiation
                        </DialogTitle>
                        <DialogDescription>
                            AI-powered 3-round negotiation strategy for risky clauses
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {/* Loading State */}
                    {isLoading && (
                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                            <Loader2 className="w-12 h-12 animate-spin text-primary" />
                            <div className="text-center space-y-2">
                                <p className="font-medium">Negotiating with AI...</p>
                                <p className="text-sm text-muted-foreground">
                                    Generating 3 negotiation rounds with strategic fallbacks
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Error State */}
                    {error && !isLoading && (
                        <Alert variant="destructive" className="my-4">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription>
                                <strong>Negotiation Failed:</strong> {error}
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Results */}
                    {result && !isLoading && !error && (
                        <div className="space-y-6 pb-4">
                            {/* Original Clause & Stance */}
                            <Card className="border-2">
                                <CardHeader>
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1 space-y-2">
                                            <CardTitle className="text-lg">Original Clause</CardTitle>
                                            <p className="text-sm italic text-muted-foreground border-l-2 pl-3">
                                                "{result.clause_text}"
                                            </p>
                                        </div>
                                        <div className="space-y-2 text-right flex-shrink-0">
                                            <Badge variant={getStanceVariant(result.stance)} className="gap-1">
                                                <Shield className="w-3 h-3" />
                                                {result.stance} Stance
                                            </Badge>
                                            <div className="text-xs text-muted-foreground">
                                                Risk Score: <span className="font-bold text-red-600">{result.risk_score.toFixed(0)}</span>/100
                                            </div>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-1">
                                        <div className="text-sm">
                                            <span className="font-semibold">Category:</span> {result.clause_label}
                                        </div>
                                        <div className="text-sm">
                                            <span className="font-semibold">Risk:</span> {result.risk_explanation}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Negotiation Rounds Timeline */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <h3 className="font-bold text-lg">Negotiation Timeline</h3>
                                    <Badge variant="secondary" className="gap-1">
                                        <TrendingDown className="w-3 h-3" />
                                        3 Strategic Rounds
                                    </Badge>
                                </div>

                                {result.rounds.map((round, index) => (
                                    <Card
                                        key={round.round_number}
                                        className={`border-l-4 ${round.round_number === 0 ? 'border-l-blue-500' :
                                                round.round_number === 1 ? 'border-l-orange-500' :
                                                    'border-l-green-500'
                                            }`}
                                    >
                                        <CardHeader>
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-2xl">{getRoundIcon(round.round_number)}</span>
                                                    <div>
                                                        <CardTitle className="text-base">
                                                            Round {round.round_number}: {getRoundTypeLabel(round.round_number)}
                                                        </CardTitle>
                                                        <CardDescription>
                                                            {round.round_number === 0 && 'Best possible outcome for tenant protection'}
                                                            {round.round_number === 1 && 'Compromise approach after initial rejection'}
                                                            {round.round_number === 2 && 'Minimal but meaningful changes'}
                                                        </CardDescription>
                                                    </div>
                                                </div>
                                                <div className="text-right flex-shrink-0">
                                                    <div className="text-xs text-muted-foreground">Risk Reduction</div>
                                                    <div className="text-2xl font-bold text-green-600">
                                                        {round.risk_reduction.toFixed(0)}%
                                                    </div>
                                                </div>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="space-y-4">
                                            {/* Counter Clause */}
                                            <div className="space-y-2">
                                                <div className="text-sm font-semibold text-primary">
                                                    📝 Proposed Counter-Clause:
                                                </div>
                                                <p className="text-sm bg-muted p-3 rounded-lg border">
                                                    {round.counter_clause}
                                                </p>
                                            </div>

                                            {/* Justification */}
                                            <div className="space-y-2">
                                                <div className="text-sm font-semibold">💡 Justification:</div>
                                                <p className="text-sm text-muted-foreground">
                                                    {round.justification}
                                                </p>
                                            </div>

                                            {/* Risk Reduction Progress */}
                                            <div className="space-y-2">
                                                <div className="flex justify-between text-sm">
                                                    <span className="font-semibold">Protection Level:</span>
                                                    <span className="text-muted-foreground">
                                                        {round.risk_reduction.toFixed(0)}% improved
                                                    </span>
                                                </div>
                                                <Progress value={round.risk_reduction} className="h-2" />
                                            </div>

                                            {/* Rejection Feedback (for rounds 1-2) */}
                                            {round.rejection_text && index < result.rounds.length - 1 && (
                                                <Alert variant="destructive" className="mt-4">
                                                    <X className="h-4 w-4" />
                                                    <AlertDescription>
                                                        <strong>Counterparty Response:</strong> {round.rejection_text}
                                                    </AlertDescription>
                                                </Alert>
                                            )}
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>

                            {/* Summary Note */}
                            <Card className="bg-muted/50">
                                <CardContent className="pt-6">
                                    <div className="text-sm space-y-2">
                                        <p className="font-semibold">📋 Negotiation Strategy Summary:</p>
                                        <p className="text-muted-foreground">
                                            This {result.stance.toLowerCase()} negotiation approach started with an{' '}
                                            <strong>ideal proposal</strong> targeting {result.rounds[0]?.risk_reduction.toFixed(0)}% risk reduction.
                                            After simulated rejections, the strategy adapted through an{' '}
                                            <strong>alternative approach</strong> ({result.rounds[1]?.risk_reduction.toFixed(0)}% reduction)
                                            and finally a <strong>minimal compromise</strong> ({result.rounds[2]?.risk_reduction.toFixed(0)}% reduction).
                                            Use these proposals as talking points in real negotiations.
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
