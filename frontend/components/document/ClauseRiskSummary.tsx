"use client";

import { useState } from 'react';
import { ClausePosition } from '@/types/document';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ClauseRiskSummaryProps {
    selectedClauses: ClausePosition[] | null;
    pageNumber?: number;
    acceptedClauses?: Set<string>;
}

const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
        financial: 'bg-blue-100 text-blue-800 border-blue-300',
        legal_compliance: 'bg-purple-100 text-purple-800 border-purple-300',
        operational: 'bg-orange-100 text-orange-800 border-orange-300',
        timeline: 'bg-green-100 text-green-800 border-green-300',
        strategic_reputational: 'bg-pink-100 text-pink-800 border-pink-300',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 border-gray-300';
};

const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
        financial: 'Financial',
        legal_compliance: 'Legal/Compliance',
        operational: 'Operational',
        timeline: 'Timeline',
        strategic_reputational: 'Strategic/Reputational',
    };
    return labels[category] || category;
};

export function ClauseRiskSummary({ selectedClauses, pageNumber, acceptedClauses = new Set() }: ClauseRiskSummaryProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    if (!selectedClauses || selectedClauses.length === 0) {
        return (
            <Card className="m-4">
                <CardContent className="pt-6 text-center text-muted-foreground">
                    <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Click on a highlighted page to see clause details</p>
                </CardContent>
            </Card>
        );
    }

    // Sort clauses by risk score (highest first)
    const sortedClauses = [...selectedClauses].sort((a, b) => b.risk_score - a.risk_score);
    const highestRisk = sortedClauses[0];

    return (
        <Card className="m-4 border-2">
            <CardHeader
                className="cursor-pointer hover:bg-slate-50 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center justify-between">
                    <div className="flex-1">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <AlertCircle className="h-5 w-5" />
                            {pageNumber ? `Page ${pageNumber} Risks` : 'Clause Risks'}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                            {selectedClauses.length} risk{selectedClauses.length !== 1 ? 's' : ''} found
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Badge
                            variant={
                                highestRisk.risk_severity === 'High'
                                    ? 'destructive'
                                    : highestRisk.risk_severity === 'Medium'
                                        ? 'default'
                                        : 'secondary'
                            }
                        >
                            {highestRisk.risk_severity}
                        </Badge>
                        {isExpanded ? (
                            <ChevronUp className="h-5 w-5 text-muted-foreground" />
                        ) : (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                        )}
                    </div>
                </div>
            </CardHeader>

            {isExpanded && (
                <CardContent className="pt-0">
                    <div className="space-y-4">
                            {sortedClauses.map((clause, idx) => (
                                <div key={idx}>
                                    {idx > 0 && <Separator className="my-4" />}

                                    <div className="space-y-3">
                                        {/* Header with category and severity */}
                                        <div className="flex items-center justify-between">
                                            <Badge
                                                variant="outline"
                                                className={getCategoryColor(clause.risk_category)}
                                            >
                                                {getCategoryLabel(clause.risk_category)}
                                            </Badge>
                                            <div className="flex items-center gap-2">
                                                {acceptedClauses.has(clause.clause_text) && (
                                                    <Badge className="bg-green-100 text-green-800 border-green-300">
                                                        <CheckCircle2 className="h-3 w-3 mr-1" />
                                                        Accepted
                                                    </Badge>
                                                )}
                                                <Badge
                                                    variant={
                                                        clause.risk_severity === 'High'
                                                            ? 'destructive'
                                                            : clause.risk_severity === 'Medium'
                                                                ? 'default'
                                                                : 'secondary'
                                                    }
                                                >
                                                    {clause.risk_severity}
                                                </Badge>
                                                <span className="text-sm font-semibold">
                                                    {clause.risk_score.toFixed(1)}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Clause text */}
                                        <div className={`p-3 rounded border ${acceptedClauses.has(clause.clause_text) ? 'bg-green-50 border-green-200' : 'bg-slate-50'}`}>
                                            <p className="text-sm italic text-slate-700">
                                                "{clause.clause_text}"
                                            </p>
                                        </div>

                                        {/* Risk explanation */}
                                        <div>
                                            <p className="text-xs font-semibold text-slate-600 mb-1">
                                                Risk Explanation:
                                            </p>
                                            <p className="text-sm text-slate-700">
                                                {clause.risk_explanation}
                                            </p>
                                        </div>

                                        {/* Recommended action */}
                                        <div className="bg-blue-50 p-3 rounded border border-blue-200">
                                            <p className="text-xs font-semibold text-blue-800 mb-1">
                                                Recommended Action:
                                            </p>
                                            <p className="text-sm text-blue-900">
                                                {clause.recommended_action}
                                            </p>
                                        </div>

                                        {/* Confidence */}
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <span>Confidence:</span>
                                            <div className="flex-1 bg-slate-200 h-2 rounded-full overflow-hidden">
                                                <div
                                                    className="bg-blue-500 h-full transition-all"
                                                    style={{ width: `${clause.confidence * 100}%` }}
                                                />
                                            </div>
                                            <span>{(clause.confidence * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                </CardContent>
            )}
        </Card>
    );
}
