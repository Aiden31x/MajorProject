/**
 * PDF Analysis Types
 */

export interface ClauseRiskScore {
    clause_text: string;
    category: string;
    severity: number;
    severity_level: string;
    confidence: number;
    risk_explanation: string;
    recommended_action: string;
}

export interface DimensionScore {
    score: number;
    severity: string;
    weight?: number | null;
    key_findings: string[];
    problematic_clauses: ClauseRiskScore[];
}

export interface RiskAssessment {
    overall_score: number;
    overall_severity: string;
    financial: DimensionScore;
    legal_compliance: DimensionScore;
    operational: DimensionScore;
    timeline: DimensionScore;
    strategic_reputational: DimensionScore;
    top_risks: string[];
    immediate_actions: string[];
    negotiation_priorities: string[];
    total_clauses_analyzed: number;
    high_risk_clauses_count: number;
    timestamp?: string;
}

export interface PDFAnalysisResult {
    classification_results: string;
    analysis_results: string;
    pages_processed: number;
    total_characters: number;
    source_document: string;
    stored_in_kb: boolean;
    total_kb_count: number;
    risk_assessment?: RiskAssessment;
}

export interface AnalysisState {
    isAnalyzing: boolean;
    progress: number;
    error: string | null;
    result: PDFAnalysisResult | null;
}

// Negotiation Types
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

export interface NegotiationRequest {
    clause_text: string;
    clause_label: string;
    risk_score: number;
    risk_explanation: string;
}

