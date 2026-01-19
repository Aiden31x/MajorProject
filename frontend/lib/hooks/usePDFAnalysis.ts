/**
 * Custom hook for PDF analysis with localStorage persistence
 */
import { useState, useEffect } from 'react';
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

const STORAGE_KEY = 'clausecraft_pdf_analysis';

export function usePDFAnalysis(): UsePDFAnalysisReturn {
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<PDFAnalysisResult | null>(null);

    // Load saved result from localStorage on mount
    useEffect(() => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                setResult(parsed);
            }
        } catch (err) {
            console.error('Failed to load saved analysis:', err);
        }
    }, []);

    // Save result to localStorage whenever it changes
    useEffect(() => {
        if (result) {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
            } catch (err) {
                console.error('Failed to save analysis:', err);
            }
        }
    }, [result]);

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
        // Clear saved result from localStorage
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch (err) {
            console.error('Failed to clear saved analysis:', err);
        }
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
