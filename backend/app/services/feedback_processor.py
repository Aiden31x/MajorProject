"""
Feedback Processor for ClauseCraft

Converts user feedback into structured tags and stores in PostgreSQL.

IMPORTANT: Feedback is non-blocking:
- 👍 feedback: Fire-and-forget (submit immediately, no confirmation)
- 👎 follow-up: Optional and dismissible (user can close without answering)
This avoids feedback fatigue and annoying users.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class FeedbackData:
    """User feedback data structure"""
    validation_result_id: str
    thumbs_up: bool
    follow_up_reason: Optional[str] = None
    additional_comments: Optional[str] = None
    user_accepted_clause: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeedbackProcessor:
    """
    Processes user feedback and converts to structured tags.
    
    Tag mapping converts user-friendly reasons into structured categories
    for future analysis and model improvement.
    """
    
    # Mapping of follow-up reasons to structured tags
    TAG_MAPPING = {
        "too_strict": ["overly_cautious", "false_positive"],
        "too_risky": ["missed_risk", "false_negative"],
        "not_clear": ["explanation_quality", "clarity_issue"],
        "wrong_intent": ["misunderstanding", "context_missing"],
        "other": ["needs_review"]
    }
    
    def convert_to_tags(self, follow_up_reason: Optional[str]) -> List[str]:
        """
        Convert follow-up reason to structured tags.
        
        Args:
            follow_up_reason: User-selected reason (too_strict, too_risky, not_clear, wrong_intent, other)
            
        Returns:
            List of structured tags for categorization
        """
        if not follow_up_reason:
            return []
        
        return self.TAG_MAPPING.get(follow_up_reason, ["uncategorized"])
    
    async def store_feedback(
        self, 
        feedback_data: FeedbackData,
        agent_decision: str,
        prisma_client
    ) -> str:
        """
        Store feedback in PostgreSQL with tag conversion.
        
        Args:
            feedback_data: FeedbackData object with user input
            agent_decision: The validation status that was given (PASS/WARN/FAIL)
            prisma_client: Prisma client instance
            
        Returns:
            ID of the created feedback record
        """
        # Convert follow-up reason to tags
        tags = self.convert_to_tags(feedback_data.follow_up_reason)
        
        # Create feedback record
        feedback_record = await prisma_client.feedback.create(
            data={
                "validationResultId": feedback_data.validation_result_id,
                "thumbsUp": feedback_data.thumbs_up,
                "followUpReason": feedback_data.follow_up_reason,
                "additionalComments": feedback_data.additional_comments,
                "tags": tags,
                "agentDecision": agent_decision,
                "userAcceptedClause": feedback_data.user_accepted_clause
            }
        )
        
        return feedback_record.id
    
    async def get_feedback_analytics(
        self,
        prisma_client,
        time_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get feedback analytics for a time range.
        
        Args:
            prisma_client: Prisma client instance
            time_range_days: Number of days to look back
            
        Returns:
            Analytics dictionary with counts and metrics
        """
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
        
        # Get all feedback in range
        feedback_records = await prisma_client.feedback.find_many(
            where={
                "createdAt": {
                    "gte": cutoff_date
                }
            },
            include={
                "validationResult": True
            }
        )
        
        # Calculate metrics
        total_feedback = len(feedback_records)
        thumbs_up_count = sum(1 for f in feedback_records if f.thumbsUp)
        thumbs_down_count = total_feedback - thumbs_up_count
        
        # Top issues by tag
        top_issues = {}
        for feedback in feedback_records:
            if not feedback.thumbsUp and feedback.tags:
                for tag in feedback.tags:
                    top_issues[tag] = top_issues.get(tag, 0) + 1
        
        # Accuracy by agent decision
        accuracy_by_decision = {}
        for decision in ["PASS", "WARN", "FAIL"]:
            decision_feedback = [f for f in feedback_records if f.agentDecision == decision]
            if decision_feedback:
                thumbs_up = sum(1 for f in decision_feedback if f.thumbsUp)
                accuracy_by_decision[decision] = thumbs_up / len(decision_feedback)
        
        return {
            "total_feedback": total_feedback,
            "thumbs_up_count": thumbs_up_count,
            "thumbs_down_count": thumbs_down_count,
            "top_issues": top_issues,
            "accuracy_by_decision": accuracy_by_decision
        }


from datetime import timedelta
