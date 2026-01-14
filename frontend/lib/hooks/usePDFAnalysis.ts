/**
 * Custom hook for PDF analysis
 */
import { useState } from 'react';
import { analyzePDF } from '@/lib/api/pdf';
import { PDFAnalysisResult } from '@/types/pdf';

interface UsePDFAnalysisReturn {
    isAnalyzing: boolean;
    progress: number;
    error: string | null;
    result: PDFAnalysisResult | null;
    analyze: (file: File, apiKey: string) => Promise<void>;
    reset: () => void;
}

export function usePDFAnalysis(): UsePDFAnalysisReturn {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<PDFAnalysisResult | null>(null);

    const analyze = async (file: File, apiKey: string) => {
        setIsAnalyzing(true);
        setProgress(0);
        setError(null);
        setResult(null);

        try {
            // Simulate progress
            const progressInterval = setInterval(() => {
                setProgress((prev) => Math.min(prev + 10, 90));
            }, 500);

            const analysisResult = await analyzePDF(file, apiKey);

            clearInterval(progressInterval);
            setProgress(100);
            setResult(analysisResult);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred during analysis');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const reset = () => {
        setIsAnalyzing(false);
        setProgress(0);
        setError(null);
        setResult(null);
    };

    return {
        isAnalyzing,
        progress,
        error,
        result,
        analyze,
        reset,
    };
}
