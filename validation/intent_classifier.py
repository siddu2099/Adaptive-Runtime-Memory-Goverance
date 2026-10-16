"""
ARMG Phase 12: Natural-Language Intent Safety Classifier.

Deterministic, zero-token pre-generation safety classifier for Text-to-SQL workflows.
Evaluates user natural-language questions before model invocation to detect and block
explicitly destructive database requests (DROP, TRUNCATE, DELETE, destructive ALTER)
while permitting explanatory, educational, preventive, or analytical queries.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional


class IntentDecision(str, Enum):
    """Controlled intent classification outcomes."""
    BLOCK = "BLOCK"
    ALLOW = "ALLOW"
    ALLOW_EXPLANATION = "ALLOW_EXPLANATION"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class IntentClassificationResult:
    """Immutable result of natural-language intent classification."""
    decision: IntentDecision
    reason: str
    matched_pattern: Optional[str] = None
    operation_type: Optional[str] = None
    confidence: float = 1.0


class IntentClassifier:
    """
    Deterministic rule-based classifier for natural-language database query intent.
    
    Guarantees:
    - Zero remote or LLM service calls (purely deterministic static analysis).
    - Distinguishes destructive execution commands from educational/explanatory discussions.
    - Explicitly surfaces ambiguity rather than silently executing or over-blocking.
    """

    # Core keywords indicating potential database mutations
    MUTATION_KEYWORDS = {
        "drop", "delete", "deletion", "truncate", "wipe", "destroy",
        "erase", "purge", "alter", "kill", "remove"
    }

    # Prohibited destructive operation patterns (when expressed imperatively/as requests)
    DESTRUCTIVE_EXECUTION_PATTERNS = [
        # DROP operations
        (r"\b(?:permanently\s+|completely\s+)?drop\s+(?:the\s+)?(?:table\s+[a-zA-Z0-9_]+|[a-zA-Z0-9_]+\s+table|table|schema|database|view|index|partition)\b", "DROP", "Request to drop database object"),
        (r"\bdrop\s+(?:table\s+)?[a-zA-Z0-9_]+\s+(?:permanently|cascade)\b", "DROP", "Request to drop database object with cascade/permanence"),
        (r"\b(?:destroy|wipe|kill)\s+(?:the\s+)?(?:[a-zA-Z0-9_]+\s+)?(?:table|database|schema)\b", "DROP", "Request to destroy/wipe database object"),
        (r"\b(?:remove|delete)\s+(?:the\s+)?(?:[a-zA-Z0-9_]+\s+)?(?:table|schema|database)\b", "DROP", "Request to remove/delete database object"),
        (r"\bdrop\s+(?:table\s+)?[a-zA-Z0-9_]+\b", "DROP", "Request to drop database table"),

        # TRUNCATE operations
        (r"\btruncate\s+(?:the\s+)?(?:table\s+)?[a-zA-Z0-9_]+\b", "TRUNCATE", "Request to truncate database table"),
        (r"\b(?:empty|clear)\s+(?:all\s+data\s+(?:from|in)\s+)?(?:the\s+)?(?:[a-zA-Z0-9_]+\s+)?table\b", "TRUNCATE", "Request to clear/empty all data from table"),

        # DELETE operations (bulk or record mutations)
        (r"\bdelete\s+(?:all|every|the)\s+(?:rows?|records?|transactions?|data)\b", "DELETE", "Request to delete records from table"),
        (r"\bdelete\s+from\s+[a-zA-Z0-9_]+\b", "DELETE", "Request to execute DELETE FROM statement"),
        (r"\b(?:erase|purge|remove|wipe|clear)\s+(?:all|every|the)\s+(?:rows?|records?|transactions?|data)\b", "DELETE", "Request to erase/purge/wipe records"),

        # Destructive ALTER operations
        (r"\balter\s+table\s+[a-zA-Z0-9_]+\s+drop\b", "ALTER_DROP", "Request to alter table and drop column/constraint"),
        (r"\bdrop\s+column\s+[a-zA-Z0-9_]+\b", "ALTER_DROP", "Request to drop table column"),

        # Administrative privilege mutations
        (r"\b(?:grant|revoke)\s+(?:all|admin|superuser)\b", "ADMIN_MUTATION", "Request to alter administrative permissions"),
    ]

    # Explanatory, educational, auditing, or prevention patterns that discuss destructive
    # operations without requesting their execution
    EXPLANATION_PATTERNS = [
        # Explicit negation: user ordering NOT to perform the action
        r"\b(?:do\s+not|don't|never|cannot|should\s+not|must\s+not)\s+(?:drop|delete|truncate|wipe|destroy|alter)\b",

        # Safety / prevention questions
        r"\bhow\s+(?:can\s+i|to|do\s+i)\s+(?:prevent|avoid|guard\s+against|protect\s+against|stop)\b",
        r"\b(?:safeguard|protection|best\s+practice)\s+(?:against|for)\b",

        # Auditing / searching logs or queries
        r"\b(?:check|verify|find|search|look\s+for|show|list)\s+.*(?:in|from)\s+(?:the\s+)?(?:logs?|history|scripts?|code|files?)\b",
        r"\bqueries\s+(?:that\s+contain|with|having)\b",
        r"\bcheck\s+(?:whether|if)\s+(?:any|all)?\s*(?:drop|delete|truncate)\b",

        # Conceptual / educational questions
        r"^(?:explain|describe|define)\b",
        r"^what\s+(?:is|does|do)\s+.*(?:mean|do|represent)\b",
        r"^what\s+does\s+(?:drop|delete|truncate|alter)\b",
        r"^what\s+is\s+(?:drop\s+table|delete\s+from|truncate\s+table)\b",
        r"\bwhy\s+is\s+(?:truncate|delete|drop)\b",
        r"\bdifference\s+between\s+(?:truncate|delete|drop)\b",
        r"\b(?:meaning|definition|syntax|example|purpose)\s+of\s+(?:drop|delete|truncate)\b",
        r"\b(?:is\s+there\s+any|are\s+there\s+any)\b.*(?:keyword|statement|query|mention|occurrence|clause)\b",
        r"\bhow\s+does\s+.*\b(?:handle|implement|process|store|execute)\b",
    ]

    # Ambiguity patterns: conflicting clauses, uncertain hypotheticals, or contradictory instructions
    AMBIGUOUS_PATTERNS = [
        # Contradictory instructions: destructive verb + analytical redirection
        r"\b(?:drop|delete|truncate|wipe|destroy)\b.*\b(?:but\s+(?:actually|instead)|or\s+(?:just|instead))\b",
        r"\b(?:show|select|give|get|display)\b.*\b(?:or\s+(?:should\s+i|maybe))\s+(?:drop|delete|truncate)\b",

        # Speculative / uncertain questions / conditional hesitation
        r"\b(?:should\s+i|would\s+it\s+be\s+good\s+to|maybe\s+we\s+should)\s+(?:drop|delete|truncate)\b",
        r"\b(?:unless|maybe|perhaps|might|whether\s+to|if\s+you\s+think)\b",
        r"^(?:drop|delete|truncate)\s+(?:it|this)\s*\??$",
    ]

    def classify(self, text: Optional[str]) -> IntentClassificationResult:
        """
        Classify the natural-language request into BLOCK, ALLOW, ALLOW_EXPLANATION, or AMBIGUOUS.
        
        Args:
            text: Raw natural-language question string.
            
        Returns:
            IntentClassificationResult with deterministic decision, reason, and metadata.
        """
        if not text or not text.strip():
            return IntentClassificationResult(
                decision=IntentDecision.ALLOW,
                reason="Empty natural-language request",
                confidence=1.0,
            )

        cleaned = text.strip()
        lower_text = cleaned.lower()

        # Step 0: Fast-path: if text contains no mutation keywords, it is ordinary analytical query
        words = set(re.findall(r"\b[a-z]+\b", lower_text))
        if not words.intersection(self.MUTATION_KEYWORDS):
            return IntentClassificationResult(
                decision=IntentDecision.ALLOW,
                reason="Standard analytical or read-only analytical query",
                confidence=1.0,
            )

        # Step 1: Check for Ambiguous / Contradictory requests
        for pattern in self.AMBIGUOUS_PATTERNS:
            if re.search(pattern, lower_text):
                return IntentClassificationResult(
                    decision=IntentDecision.AMBIGUOUS,
                    reason="Contradictory or speculative clauses detected requiring explicit user clarification",
                    matched_pattern=pattern,
                    confidence=0.85,
                )

        # Step 2: Check for Explanation / Educational / Prevention / Negated requests
        for pattern in self.EXPLANATION_PATTERNS:
            if re.search(pattern, lower_text):
                return IntentClassificationResult(
                    decision=IntentDecision.ALLOW_EXPLANATION,
                    reason="Explanatory, preventive, or negated context identified; execution not requested",
                    matched_pattern=pattern,
                    confidence=0.95,
                )

        # Step 3: Check for Explicit Destructive Execution requests -> BLOCK
        for pattern, op_type, desc in self.DESTRUCTIVE_EXECUTION_PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                return IntentClassificationResult(
                    decision=IntentDecision.BLOCK,
                    reason=f"{desc}: '{match.group(0)}'",
                    matched_pattern=pattern,
                    operation_type=op_type,
                    confidence=1.0,
                )

        # Step 4: Standalone direct SQL command detection in question (e.g., "execute: DROP TABLE ...")
        sql_direct_pattern = r"(?:^|\b(?:please\s+)?(?:execute|run|perform|apply)\s*:?\s*)(drop\s+table|truncate\s+table|delete\s+from|alter\s+table\s+[a-z0-9_]+\s+drop)\b"
        sql_direct_match = re.search(sql_direct_pattern, lower_text)
        if sql_direct_match:
            return IntentClassificationResult(
                decision=IntentDecision.BLOCK,
                reason=f"Direct destructive SQL command request: '{sql_direct_match.group(1)}'",
                matched_pattern=sql_direct_pattern,
                operation_type="SQL_DIRECT_COMMAND",
                confidence=1.0,
            )

        # Step 5: Default for queries that contain mutation keywords in non-destructive ways
        # (e.g., "what is the price drop on products?", "remove discounts from calculation")
        return IntentClassificationResult(
            decision=IntentDecision.ALLOW,
            reason="Query mentions mutation vocabulary without requesting database mutation",
            confidence=0.90,
        )


def classify_natural_language_intent(query: str) -> IntentClassificationResult:
    """Convenience helper to classify a natural-language query using the default IntentClassifier."""
    return IntentClassifier().classify(query)

