/**
 * Knowledge Base Statistics Sidebar
 */
'use client';

import { useEffect, useState } from 'react';
import { getKBStatistics } from '@/lib/api/chat';
import { KBStatistics } from '@/types/chat';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Database, AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function KBStatsSidebar() {
    const [stats, setStats] = useState<KBStatistics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStats = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getKBStatistics();
            setStats(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load statistics');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        KB Statistics
                    </CardTitle>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={fetchStats}
                        disabled={isLoading}
                    >
                        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {isLoading ? (
                    <>
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-full" />
                    </>
                ) : error ? (
                    <p className="text-sm text-destructive">{error}</p>
                ) : stats ? (
                    <>
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium">Total Clauses:</span>
                                <Badge variant="secondary">{stats.total_clauses}</Badge>
                            </div>

                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium flex items-center gap-1">
                                    <AlertTriangle className="w-4 h-4 text-destructive" />
                                    Red Flags:
                                </span>
                                <Badge variant="destructive">{stats.red_flags_count}</Badge>
                            </div>

                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium">Collection:</span>
                                <Badge variant="outline" className="text-xs">{stats.collection_name}</Badge>
                            </div>
                        </div>

                        <div className="pt-2 border-t">
                            <p className="text-xs text-muted-foreground">{stats.status}</p>
                        </div>
                    </>
                ) : null}
            </CardContent>
        </Card>
    );
}
