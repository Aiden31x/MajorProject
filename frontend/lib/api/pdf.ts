/**
 * PDF Analysis API Functions
 */
import { apiClient } from './client';
import { PDFAnalysisResult } from '@/types/pdf';

export async function analyzePDF(
    file: File,
    geminiApiKey: string
): Promise<PDFAnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('gemini_api_key', geminiApiKey);

    const response = await apiClient.post<PDFAnalysisResult>('/api/pdf/analyze', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
}
