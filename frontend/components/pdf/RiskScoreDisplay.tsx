/**
 * Risk Score Display Component
 * Comprehensive visualization of multi-dimensional risk assessment
 */
'use client';

import { RiskAssessment, DimensionScore, ClauseRiskScore } from '@/types/pdf';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { DollarSign, Scale, Settings, Clock, Shield, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { NegotiateButton } from '@/components/negotiation/NegotiateButton';

interface RiskScoreDisplayProps {
    riskAssessment: RiskAssessment;
}

export function RiskScoreDisplay({ riskAssessment }: RiskScoreDisplayProps) {
    // Helper function to get color based on severity
    const getSeverityColor = (severity: string): string => {
        switch (severity.toLowerCase()) {
            case 'high':
                return 'text-red-600';
            case 'medium':
                return 'text-yellow-600';
            case 'low':
                return 'text-green-600';
            default:
                return 'text-gray-600';
        }
    };

    const getProgressColor = (severity: string): string => {
        switch (severity.toLowerCase()) {
            case 'high':
                return 'bg-red-600';
            case 'medium':
                return 'bg-yellow-600';
            case 'low':
                return 'bg-green-600';
            default:
                return 'bg-gray-600';
        }
    };

    const getBadgeVariant = (severity: string): "destructive" | "default" | "secondary" => {
        switch (severity.toLowerCase()) {
            case 'high':
                return 'destructive';
            case 'medium':
                return 'default';
            case 'low':
                return 'secondary';
            default:
                return 'default';
        }
    };

    // Dimension configuration
    const dimensions = [
        {
            name: 'Financial',
            key: 'financial' as const,
            icon: DollarSign,
            data: riskAssessment.financial,
        },
        {
            name: 'Legal/Compliance',
            key: 'legal_compliance' as const,
            icon: Scale,
            data: riskAssessment.legal_compliance,
        },
        {
            name: 'Operational',
            key: 'operational' as const,
            icon: Settings,
            data: riskAssessment.operational,
        },
        {
            name: 'Timeline',
            key: 'timeline' as const,
            icon: Clock,
            data: riskAssessment.timeline,
        },
        {
            name: 'Strategic/Reputational',
            key: 'strategic_reputational' as const,
            icon: Shield,
            data: riskAssessment.strategic_reputational,
            isQualitative: true,
        },
    ];

    return (
        <div className="space-y-6">
            {/* Overall Risk Card */}
            <Card className="border-2">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-2xl">Overall Risk Assessment</CardTitle>
                            <CardDescription>
                                Comprehensive multi-dimensional analysis of lease agreement
                            </CardDescription>
                        </div>
                        <Badge className="text-lg px-4 py-2" variant={getBadgeVariant(riskAssessment.overall_severity)}>
                            {riskAssessment.overall_severity}
                        </Badge>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Overall Score */}
                    <div className="flex items-center gap-4">
                        <div className="text-6xl font-bold">{riskAssessment.overall_score.toFixed(1)}</div>
                        <div className="flex-1 space-y-2">
                            <Progress
                                value={riskAssessment.overall_score}
                                className="h-4"
                            />
                            <div className={`text-sm font-medium ${getSeverityColor(riskAssessment.overall_severity)}`}>
                                {riskAssessment.overall_severity} Risk Level
                            </div>
                        </div>
                    </div>

                    {/* Summary Stats */}
                    <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                        <div className="text-center">
                            <div className="text-2xl font-bold">{riskAssessment.total_clauses_analyzed}</div>
                            <div className="text-sm text-muted-foreground">Clauses Analyzed</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-600">{riskAssessment.high_risk_clauses_count}</div>
                            <div className="text-sm text-muted-foreground">High-Risk Clauses</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-orange-600">{riskAssessment.top_risks.length}</div>
                            <div className="text-sm text-muted-foreground">Top Risks</div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Dimensional Breakdown */}
            <div className="space-y-4">
                <h3 className="text-xl font-bold">Risk Dimensions</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {dimensions.map((dimension) => {
                        const Icon = dimension.icon;
                        const data = dimension.data;

                        return (
                            <Card key={dimension.key}>
                                <CardHeader>
                                    <div className="flex items-center gap-2">
                                        <Icon className="w-5 h-5" />
                                        <CardTitle className="text-lg">{dimension.name}</CardTitle>
                                    </div>
                                    {dimension.data.weight !== null && dimension.data.weight !== undefined && (
                                        <CardDescription>
                                            Weight: {(dimension.data.weight * 100).toFixed(0)}%
                                        </CardDescription>
                                    )}
                                    {dimension.isQualitative && (
                                        <CardDescription>
                                            Qualitative Analysis Only
                                        </CardDescription>
                                    )}
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    {/* Score and Badge */}
                                    <div className="flex items-center justify-between">
                                        <div className="text-3xl font-bold">{data.score.toFixed(1)}</div>
                                        <Badge variant={getBadgeVariant(data.severity)}>
                                            {data.severity}
                                        </Badge>
                                    </div>

                                    {/* Progress Bar */}
                                    <Progress
                                        value={data.score}
                                        className="h-2"
                                    />

                                    {/* Key Findings */}
                                    <div className="space-y-1">
                                        <div className="text-sm font-medium">Key Findings:</div>
                                        <ul className="text-xs text-muted-foreground space-y-1">
                                            {data.key_findings.slice(0, 2).map((finding, idx) => (
                                                <li key={idx} className="line-clamp-2">• {finding}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            </div>

            {/* Detailed Analysis Tabs */}
            <Card>
                <CardHeader>
                    <CardTitle>Detailed Risk Analysis</CardTitle>
                    <CardDescription>
                        Explore identified risks, recommended actions, and problematic clauses
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Tabs defaultValue="risks" className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="risks">Top Risks</TabsTrigger>
                            <TabsTrigger value="actions">Actions</TabsTrigger>
                            <TabsTrigger value="clauses">Clauses</TabsTrigger>
                        </TabsList>

                        {/* Top Risks Tab */}
                        <TabsContent value="risks" className="space-y-3 mt-4">
                            {riskAssessment.top_risks.length > 0 ? (
                                riskAssessment.top_risks.map((risk, idx) => (
                                    <Alert key={idx} variant="destructive">
                                        <AlertTriangle className="h-4 w-4" />
                                        <AlertDescription>{risk}</AlertDescription>
                                    </Alert>
                                ))
                            ) : (
                                <p className="text-sm text-muted-foreground text-center py-8">
                                    No critical risks identified
                                </p>
                            )}
                        </TabsContent>

                        {/* Immediate Actions Tab */}
                        <TabsContent value="actions" className="space-y-2 mt-4">
                            {riskAssessment.immediate_actions.length > 0 ? (
                                riskAssessment.immediate_actions.map((action, idx) => (
                                    <div key={idx} className="flex items-start gap-2 p-3 bg-muted rounded-lg">
                                        <CheckCircle2 className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
                                        <span className="text-sm">{action}</span>
                                    </div>
                                ))
                            ) : (
                                <p className="text-sm text-muted-foreground text-center py-8">
                                    No immediate actions required
                                </p>
                            )}
                        </TabsContent>

                        {/* Problematic Clauses Tab */}
                        <TabsContent value="clauses" className="mt-4">
                            <ScrollArea className="h-96">
                                <div className="space-y-4 pr-4">
                                    {dimensions.map((dimension) => {
                                        const clauses = dimension.data.problematic_clauses;
                                        if (clauses.length === 0) return null;

                                        return (
                                            <div key={dimension.key} className="space-y-2">
                                                <h4 className="font-semibold text-sm flex items-center gap-2">
                                                    <dimension.icon className="w-4 h-4" />
                                                    {dimension.name} Issues
                                                </h4>
                                                {clauses.map((clause, idx) => (
                                                    <Card key={idx} className="border-l-4" style={{
                                                        borderLeftColor: clause.severity_level === 'High' ? '#dc2626' :
                                                            clause.severity_level === 'Medium' ? '#ca8a04' : '#16a34a'
                                                    }}>
                                                        <CardContent className="pt-4 space-y-2">
                                                            <div className="flex items-start justify-between gap-2">
                                                                <Badge variant={getBadgeVariant(clause.category)}>
                                                                    {clause.category}
                                                                </Badge>
                                                                <div className="flex items-center gap-2">
                                                                    <Badge variant={getBadgeVariant(clause.severity_level)}>
                                                                        {clause.severity_level} ({clause.severity.toFixed(0)})
                                                                    </Badge>
                                                                    <span className="text-xs text-muted-foreground">
                                                                        {(clause.confidence * 100).toFixed(0)}% confidence
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            <p className="text-sm italic text-muted-foreground border-l-2 pl-3">
                                                                "{clause.clause_text.substring(0, 200)}{clause.clause_text.length > 200 ? '...' : ''}"
                                                            </p>

                                                            <div className="space-y-1 text-sm">
                                                                <div>
                                                                    <span className="font-semibold">Risk: </span>
                                                                    {clause.risk_explanation}
                                                                </div>
                                                                <div>
                                                                    <span className="font-semibold">Action: </span>
                                                                    {clause.recommended_action}
                                                                </div>
                                                            </div>

                                                            {/* Negotiate Button for High-Risk Clauses */}
                                                            {clause.severity >= 70 && (
                                                                <div className="pt-3 border-t">
                                                                    <NegotiateButton clause={clause} />
                                                                </div>
                                                            )}
                                                        </CardContent>
                                                    </Card>
                                                ))}
                                            </div>
                                        );
                                    })}
                                </div>
                            </ScrollArea>
                        </TabsContent>
                    </Tabs>
                </CardContent>
            </Card>
        </div>
    );
}
