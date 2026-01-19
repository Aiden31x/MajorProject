/**
 * PDF Analysis Page - Main landing page
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { PDFUploader } from '@/components/pdf/PDFUploader';
import { AnalysisResults } from '@/components/pdf/AnalysisResults';
import { usePDFAnalysis } from '@/lib/hooks/usePDFAnalysis';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { FileText, MessageSquare, Sparkles, AlertCircle } from 'lucide-react';

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [apiKey, setApiKey] = useState('');
  const { isAnalyzing, progress, error, result, analyze, reset } = usePDFAnalysis();

  const handleAnalyze = async () => {
    if (file) {
      await analyze(file, apiKey || ''); // Use empty string if no API key provided (backend will use its own)
    }
  };

  const handleReset = () => {
    setFile(null);
    reset();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">ClauseCraft</h1>
                <p className="text-sm text-muted-foreground">AI-Powered Lease Agreement Analyzer</p>
              </div>
            </div>
            <Link href="/chat">
              <Button variant="outline" className="gap-2">
                <MessageSquare className="w-4 h-4" />
                Query Knowledge Base
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {!result ? (
          <div className="space-y-6">
            {/* Hero Section */}
            <div className="text-center space-y-4 py-8">
              <Badge variant="secondary" className="gap-1">
                <Sparkles className="w-3 h-3" />
                Powered by Google Gemini & RAG
              </Badge>
              <h2 className="text-4xl font-bold tracking-tight">
                Analyze Your Lease Agreement
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Upload your PDF lease agreement and get instant AI-powered analysis with
                clause classification and risk assessment.
              </p>
            </div>

            {/* Upload Section */}
            <div className="max-w-2xl mx-auto space-y-4">
              <PDFUploader
                file={file}
                onFileSelect={setFile}
                disabled={isAnalyzing}
              />

              <Card>
                <CardHeader>
                  <CardTitle>Configuration</CardTitle>
                  <CardDescription>Gemini API key is optional (server uses configured key by default)</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label htmlFor="api-key" className="text-sm font-medium block mb-2">
                      🔑 Gemini API Key <span className="text-muted-foreground font-normal">(Optional)</span>
                    </label>
                    <Input
                      id="api-key"
                      type="password"
                      placeholder="Leave empty to use server's API key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      disabled={isAnalyzing}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Use your own API key from{' '}
                      <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        Google AI Studio
                      </a>
                      {' '}or leave empty to use server's configured key
                    </p>
                  </div>

                  <Button
                    onClick={handleAnalyze}
                    disabled={!file || isAnalyzing}
                    className="w-full"
                    size="lg"
                  >
                    {isAnalyzing ? 'Analyzing...' : '🔍 Analyze Lease Agreement'}
                  </Button>

                  {isAnalyzing && (
                    <div className="space-y-2">
                      <Progress value={progress} />
                      <p className="text-sm text-center text-muted-foreground">
                        Processing... {progress}%
                      </p>
                    </div>
                  )}

                  {error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Instructions */}
              <Card>
                <CardHeader>
                  <CardTitle>📌 How to use</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Upload your lease agreement PDF</li>
                    <li>Enter your Gemini API key</li>
                    <li>Click "Analyze Lease Agreement"</li>
                    <li>Review the AI-extracted clauses and analysis</li>
                  </ol>
                  <div className="pt-4 border-t mt-4">
                    <p className="font-medium mb-2">🆕 Enhanced with RAG & Gemini:</p>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>PDFs stored page-by-page in knowledge base</li>
                      <li>Gemini extracts and classifies clauses with full context</li>
                      <li>Historical agreements provide context for better analysis</li>
                      <li>More accurate than regex-based splitting</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Header */}
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-bold">Analysis Results</h2>
                  <Badge variant="secondary" className="gap-1">
                    💾 Saved - persists across navigation
                  </Badge>
                </div>
                <p className="text-muted-foreground">
                  {result.source_document} • {result.pages_processed} pages •{' '}
                  {result.total_characters.toLocaleString()} characters
                </p>
              </div>
              <Button onClick={handleReset} variant="outline">
                Analyze Another PDF
              </Button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{result.pages_processed}</div>
                  <p className="text-sm text-muted-foreground">Pages Processed</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {result.stored_in_kb ? '✅' : '❌'}
                  </div>
                  <p className="text-sm text-muted-foreground">Stored in KB</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">{result.total_kb_count}</div>
                  <p className="text-sm text-muted-foreground">Total KB Documents</p>
                </CardContent>
              </Card>
            </div>

            {/* Results */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AnalysisResults
                title="📄 Classification Results"
                content={result.classification_results}
              />
              <AnalysisResults
                title="📑 AI Analysis"
                content={result.analysis_results}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-6 bg-muted/50">
        <div className="container max-w-7xl px-4 text-center text-sm text-muted-foreground">
          <p>
            ClauseCraft v2.0 • Powered by Next.js, FastAPI, Google Gemini & ChromaDB
          </p>
        </div>
      </footer>
    </div>
  );
}
