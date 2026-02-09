"""
Clause Extractor Service for ClauseCraft
Maps risky clauses from risk assessment to their positions in PDF pages
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ClausePosition:
    """Represents a clause's position in the document"""
    clause_text: str
    page_number: int
    start_char: int  # Character position on page (for future exact positioning)
    end_char: int
    risk_score: float
    risk_severity: str  # Low, Medium, High
    risk_category: str  # financial, legal, operational, timeline, strategic
    risk_explanation: str
    recommended_action: str
    confidence: float
    bounding_box: Optional[Dict[str, float]] = None  # x, y, width, height (future feature)


class ClauseExtractor:
    """Extract clause positions from PDF for highlighting"""
    
    def __init__(self, fuzzy_threshold: float = 0.75):
        """
        Initialize the clause extractor

        Args:
            fuzzy_threshold: Minimum similarity ratio for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self._normalized_pages_cache = {}  # Cache normalized page text for performance

    def _get_normalized_page(self, page_number: int, page_text: str) -> str:
        """Get cached normalized page text for performance"""
        if page_number not in self._normalized_pages_cache:
            self._normalized_pages_cache[page_number] = self._normalize_text(page_text)
        return self._normalized_pages_cache[page_number]

    def fuzzy_match_clause(
        self,
        clause_text: str,
        page_text: str,
        page_number: int = -1,  # NEW: For caching
        threshold: Optional[float] = None
    ) -> Optional[Tuple[int, int]]:
        """
        Find clause position using tiered strategy:
        1. Exact substring match (O(n), <1ms)
        2. Article/section reference extraction (for "Article X.XX:" patterns)
        3. Normalized exact match (O(n), handles whitespace)
        4. Fuzzy matching fallback (O(n²), for complex cases)

        Args:
            clause_text: The clause text to find
            page_text: The full page text to search in
            page_number: Optional page number for caching normalized text
            threshold: Minimum similarity threshold (uses instance default if None)

        Returns:
            Tuple of (start_char, end_char) or None if not found
        """
        if threshold is None:
            threshold = self.fuzzy_threshold

        clause_norm = self._normalize_text(clause_text)

        # Use cached normalized page if available
        if page_number != -1:
            page_norm = self._get_normalized_page(page_number, page_text)
        else:
            page_norm = self._normalize_text(page_text)

        # TIER 1: Exact normalized substring match (fastest)
        start = page_norm.find(clause_norm)
        if start != -1:
            return (start, start + len(clause_norm))

        # TIER 2: Extract article/section reference and search for that
        # Patterns like "Article 4.01:", "Section 5.04:", "Article 17.03"
        import re

        # Try to extract article/section numbers - be very flexible
        # Match patterns like: "Article 14.01", "Section 5.04", "14.01", "4.01"
        article_match = re.search(r'(?:article|section)?\s*(\d+\.?\d*)', clause_text, re.IGNORECASE)

        if article_match:
            number = article_match.group(1)  # e.g., "14.01", "4.01", "17.03"

            # Try many different search patterns
            search_patterns = [
                f"article {number}",  # "article 14.01"
                f"section {number}",  # "section 14.01"
                f"{number}.",         # "14.01."
                f"{number}:",         # "14.01:"
                f"{number} ",         # "14.01 "
                number                # just "14.01"
            ]

            for pattern in search_patterns:
                pattern_norm = self._normalize_text(pattern)
                start = page_norm.find(pattern_norm)
                if start != -1:
                    # Found it! Return a span around this location
                    end = min(start + 250, len(page_norm))
                    return (start, end)

        # TIER 3: Short clauses - exact match or nothing
        if len(clause_norm) < 20:
            return None

        # TIER 4: Fuzzy matching fallback (only for longer clauses)
        best_match = None
        best_ratio = 0.0
        clause_len = len(clause_norm)

        # Simplified window search - use single optimal window size
        window_size = clause_len

        for i in range(len(page_norm) - window_size + 1):
            window = page_norm[i:i + window_size]
            ratio = SequenceMatcher(None, clause_norm, window).ratio()

            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = (i, i + window_size)

                # Early termination if very good match
                if ratio >= 0.95:
                    break

        return best_match
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching (lowercase, remove extra whitespace)"""
        # Convert to lowercase
        text = text.lower()
        # Replace multiple spaces/newlines with single space
        text = ' '.join(text.split())
        # Remove common punctuation variations
        text = text.replace('\n', ' ').replace('\r', '')
        return text
    
    def extract_clauses_with_positions(
        self,
        pdf_pages: List[Dict],
        risk_assessment: Dict
    ) -> List[ClausePosition]:
        """
        Map risky clauses to PDF positions (optimized with parallel search).

        Strategy:
        1. Pre-cache all normalized page texts
        2. Check if LLM provided positions
        3. Fallback to parallelized fuzzy matching

        Args:
            pdf_pages: List of page dicts with 'page_number' and 'text' keys
            risk_assessment: Risk assessment dict with dimensional scores

        Returns:
            List of ClausePosition objects with page mappings
        """
        clause_positions = []

        # Clear and pre-populate cache for all pages (optimization)
        self._normalized_pages_cache.clear()
        for page in pdf_pages:
            page_num = page.get('page_number', 0)
            page_text = page.get('text', '')
            self._normalized_pages_cache[page_num] = self._normalize_text(page_text)

        # Collect all clauses to process
        clauses_to_find = []
        dimensions = [
            ('financial', risk_assessment.get('financial', {})),
            ('legal_compliance', risk_assessment.get('legal_compliance', {})),
            ('operational', risk_assessment.get('operational', {})),
            ('timeline', risk_assessment.get('timeline', {})),
            ('strategic_reputational', risk_assessment.get('strategic_reputational', {}))
        ]

        for dim_name, dim_data in dimensions:
            for clause_dict in dim_data.get('problematic_clauses', []):
                clause_text = clause_dict.get('clause_text', '')
                if clause_text:
                    clauses_to_find.append((dim_name, clause_dict))

        print(f"🔍 Finding positions for {len(clauses_to_find)} clauses across {len(pdf_pages)} pages...")

        # Process clauses (page search is already parallelized in _find_clause_in_pages)
        found_count = 0
        for dim_name, clause_dict in clauses_to_find:
            clause_text = clause_dict.get('clause_text', '')
            llm_page = clause_dict.get('page_number', -1)
            llm_start = clause_dict.get('start_char', -1)
            llm_end = clause_dict.get('end_char', -1)

            position = None

            # If LLM provided exact positions, use them
            if llm_page > 0 and llm_start >= 0 and llm_end > llm_start:
                position = (llm_page, llm_start, llm_end)
            # If LLM provided page only, search that page
            elif llm_page > 0:
                target_page = next((p for p in pdf_pages if p.get('page_number') == llm_page), None)
                if target_page:
                    match = self.fuzzy_match_clause(clause_text, target_page['text'], llm_page)
                    if match:
                        position = (llm_page, match[0], match[1])

            # Fallback: parallel search across all pages
            if not position:
                position = self._find_clause_in_pages(clause_text, pdf_pages)

            if position:
                found_count += 1
                page_num, start_char, end_char = position
                clause_positions.append(ClausePosition(
                    clause_text=clause_text,
                    page_number=page_num,
                    start_char=start_char,
                    end_char=end_char,
                    risk_score=float(clause_dict.get('severity', 0)),
                    risk_severity=clause_dict.get('severity_level', 'Medium'),
                    risk_category=dim_name,
                    risk_explanation=clause_dict.get('risk_explanation', ''),
                    recommended_action=clause_dict.get('recommended_action', ''),
                    confidence=float(clause_dict.get('confidence', 0.5))
                ))

        print(f"✅ Found {found_count}/{len(clauses_to_find)} clause positions")
        return clause_positions
    
    def _search_single_page(
        self,
        clause_text: str,
        page: Dict,
        clause_norm: str
    ) -> Optional[Tuple[int, int, int, float]]:
        """
        Search a single page for the clause (used for parallel execution)

        Returns:
            Tuple of (page_number, start_char, end_char, ratio) or None
        """
        page_num = page.get('page_number', 0)
        page_text = page.get('text', '')

        match = self.fuzzy_match_clause(
            clause_text,
            page_text,
            page_number=page_num
        )

        if match:
            start_char, end_char = match
            matched_text = page_text[start_char:end_char]
            ratio = SequenceMatcher(
                None,
                clause_norm,
                self._normalize_text(matched_text)
            ).ratio()
            return (page_num, start_char, end_char, ratio)
        return None

    def _find_clause_in_pages(
        self,
        clause_text: str,
        pdf_pages: List[Dict]
    ) -> Optional[Tuple[int, int, int]]:
        """
        Find which page contains the clause and its position (parallelized)

        Args:
            clause_text: Text to search for
            pdf_pages: List of page dicts

        Returns:
            Tuple of (page_number, start_char, end_char) or None
        """
        clause_norm = self._normalize_text(clause_text)
        best_match = None
        best_ratio = 0.0

        # Use ThreadPoolExecutor for parallel page search
        with ThreadPoolExecutor(max_workers=min(8, len(pdf_pages))) as executor:
            futures = {
                executor.submit(self._search_single_page, clause_text, page, clause_norm): page
                for page in pdf_pages
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    page_num, start_char, end_char, ratio = result
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = (page_num, start_char, end_char)

                        # Early termination for excellent matches
                        if ratio >= 0.95:
                            # Cancel remaining futures
                            for f in futures:
                                f.cancel()
                            break

        return best_match
    
    def group_clauses_by_page(
        self,
        clause_positions: List[ClausePosition]
    ) -> Dict[int, List[ClausePosition]]:
        """
        Group clauses by page number for efficient rendering
        
        Args:
            clause_positions: List of clause positions
        
        Returns:
            Dict mapping page_number -> list of clauses on that page
        """
        grouped = {}
        for clause in clause_positions:
            page_num = clause.page_number
            if page_num not in grouped:
                grouped[page_num] = []
            grouped[page_num].append(clause)
        
        return grouped
    
    def get_page_risk_level(
        self,
        clauses_on_page: List[ClausePosition]
    ) -> Tuple[str, float]:
        """
        Determine overall risk level for a page based on its clauses
        
        Args:
            clauses_on_page: List of clauses found on the page
        
        Returns:
            Tuple of (severity_level, max_score) for the page
        """
        if not clauses_on_page:
            return ("Low", 0.0)
        
        # Find highest risk score on the page
        max_score = max(clause.risk_score for clause in clauses_on_page)
        
        # Determine severity based on highest risk
        if max_score >= 70:
            severity = "High"
        elif max_score >= 40:
            severity = "Medium"
        else:
            severity = "Low"
        
        return (severity, max_score)
