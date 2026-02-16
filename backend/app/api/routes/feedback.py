"""
Feedback API Routes for ClauseCraft

Handles user feedback submission and analytics.

IMPORTANT: Feedback is non-blocking:
- 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
- 👎 follow-up: Optional and dismissible (user can close without answering)
"""

from fastapi import APIRouter, Form, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from app.services.feedback_processor import FeedbackProcessor, FeedbackData
from app.models.responses import FeedbackSubmitResponse, FeedbackAnalyticsResponse

router = APIRouter()


# Note: Prisma client will be injected via dependency injection in production
# For now, we'll use a placeholder that should be replaced with actual Prisma client
# This will be set up when integrating with main.py


@router.post("/submit", response_model=FeedbackSubmitResponse)
async def submit_feedback(
    validation_result_id: str = Form(...),
    thumbs_up: bool = Form(...),
    follow_up_reason: Optional[str] = Form(None),
    additional_comments: Optional[str] = Form(None),
    user_accepted_clause: Optional[bool] = Form(None)
):
    """
    Submit user feedback for a validation result.
    
    Flow:
    1. Lookup validation result from database
    2. Convert follow_up_reason to structured tags
    3. Store feedback with relationship to validation result
    4. Return feedback_id
    
    IMPORTANT: Feedback is non-blocking:
    - 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
    - 👎 follow-up: Optional and dismissible (user can close without answering)
    
    Args:
        validation_result_id: ID of the validation result being rated
        thumbs_up: True for 👍, False for 👎
        follow_up_reason: Optional reason (too_strict, too_risky, not_clear, wrong_intent, other)
        additional_comments: Optional free-text comments
        user_accepted_clause: Optional flag indicating if user accepted the clause
        
    Returns:
        FeedbackSubmitResponse with feedback_id and message
    """
    try:
        # TODO: Get Prisma client from dependency injection and store in database
        # For now, we'll just log the feedback and return success
        # This allows the frontend to work while database integration is completed

        print(f"📝 Feedback received for validation {validation_result_id}:")
        print(f"   👍/👎: {'👍' if thumbs_up else '👎'}")
        if follow_up_reason:
            print(f"   Reason: {follow_up_reason}")
        if additional_comments:
            print(f"   Comments: {additional_comments}")

        # Generate a temporary feedback ID
        import uuid
        feedback_id = str(uuid.uuid4())

        return FeedbackSubmitResponse(
            feedback_id=feedback_id,
            message="Feedback received successfully (database storage pending)"
        )
        
        # The actual implementation would be:
        # 
        # # Lookup validation result to get agent decision
        # validation_result = await prisma_client.validationresult.find_unique(
        #     where={"id": validation_result_id}
        # )
        # 
        # if not validation_result:
        #     raise HTTPException(
        #         status_code=404,
        #         detail=f"Validation result {validation_result_id} not found"
        #     )
        # 
        # # Create feedback data
        # feedback_data = FeedbackData(
        #     validation_result_id=validation_result_id,
        #     thumbs_up=thumbs_up,
        #     follow_up_reason=follow_up_reason,
        #     additional_comments=additional_comments,
        #     user_accepted_clause=user_accepted_clause
        # )
        # 
        # # Store feedback
        # processor = FeedbackProcessor()
        # feedback_id = await processor.store_ feedback(
        #     feedback_data,
        #     agent_decision=validation_result.status,
        #     prisma_client=prisma_client
        # )
        # 
        # return FeedbackSubmitResponse(
        #     feedback_id=feedback_id,
        #     message="Feedback submitted successfully"
        # )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/analytics", response_model=FeedbackAnalyticsResponse)
async def get_feedback_analytics(time_range: str = Query("7d", regex="^\\d+d$")):
    """
    Get feedback analytics for a time range.
    
    Args:
        time_range: Time range in format "Nd" where N is number of days (e.g., "7d", "30d")
        
    Returns:
        FeedbackAnalyticsResponse with aggregated metrics
    """
    try:
        # TODO: Get Prisma client from dependency injection
        raise HTTPException(
            status_code=501,
            detail="Feedback analytics requires Prisma client integration - to be implemented in Phase 10"
        )
        
        # The actual implementation would be:
        #
        # from app.database import get_prisma_client
        # prisma_client = await get_prisma_client()
        # 
        # # Parse time range
        # days = int(time_range[:-1])
        # 
        # # Get analytics
        # processor = FeedbackProcessor()
        # analytics = await processor.get_feedback_analytics(
        #     prisma_client,
        #     time_range_days=days
        # )
        # 
        # return FeedbackAnalyticsResponse(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching analytics: {str(e)}"
        )


@router.get("/health")
async def feedback_health():
    """
    Health check for feedback service.
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "FeedbackProcessor",
        "note": "Prisma integration pending in Phase 10"
    }
