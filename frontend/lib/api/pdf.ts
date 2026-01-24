/**
 * PDF Analysis API Functions
 */
import { apiClient } from './client';
import { PDFAnalysisResult } from '@/types/pdf';

export async function analyzePDF(
    file: File,
    geminiApiKey: string,
    enableRiskScoring: boolean = true
): Promise<PDFAnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('gemini_api_key', geminiApiKey);
    formData.append('enable_risk_scoring', String(enableRiskScoring));

    const response = await apiClient.post<PDFAnalysisResult>('/api/pdf/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        timeout: 600000, // 5 minutes for PDF analysis (up to 3 LLM calls with risk scoring)
    });

    return response.data;
}

