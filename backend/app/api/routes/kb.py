"""
Knowledge Base Statistics Endpoint
"""
from fastapi import APIRouter, Depends

from app.models.responses import KBStatistics
from app.services.rag import ClauseStore
from app.api.deps import get_clause_store

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])


@router.get("/stats", response_model=KBStatistics)
async def get_kb_statistics(
    clause_store: ClauseStore = Depends(get_clause_store)
):
    """
    Get knowledge base statistics.
    
    Returns total clauses, red flags count, and status.
    """
    try:
        stats = clause_store.get_statistics()
        
        # Count red flags
        redflag_count = 0
        try:
            redflags = clause_store.get_clauses_by_label('redflag', limit=1000)
            redflag_count = len(redflags) if redflags else 0
        except:
            pass  # If method doesn't exist or fails, keep count at 0
        
        # Determine status
        total_clauses = stats['total_clauses']
        if total_clauses > 0:
            status = "Ready for queries"
        else:
            status = "Empty - process PDFs first"
        
        return KBStatistics(
            total_clauses=total_clauses,
            red_flags_count=redflag_count,
            collection_name=stats.get('collection_name', 'lease_clauses'),
            status=status
        )
        
    except Exception as e:
        # Return empty stats on error
        return KBStatistics(
            total_clauses=0,
            red_flags_count=0,
            collection_name="lease_clauses",
            status=f"Error: {str(e)}"
        )
