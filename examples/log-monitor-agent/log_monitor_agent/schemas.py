"""Pydantic schemas for structured LLM outputs.

These schemas ensure consistent, typed responses from the LLM for
classification and severity assessment tasks.
"""

from typing import Literal

from pydantic import BaseModel, Field


class LogClassificationSchema(BaseModel):
    """Schema for log message classification.

    The LLM uses this schema to provide structured classification output,
    making it easy to route the workflow based on the result.
    """

    classification: Literal["error", "warning", "normal"] = Field(
        description="The classification of the log message based on its content"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the classification (0.0 to 1.0)",
    )
    indicators: list[str] = Field(
        default_factory=list,
        description="Keywords or patterns that led to this classification",
    )


class SeverityAssessmentSchema(BaseModel):
    """Schema for problem severity assessment.

    After diagnosing a problem, the LLM uses this schema to assess
    whether immediate action (high severity) or ticketing (low severity)
    is appropriate.
    """

    severity: Literal["high", "low"] = Field(
        description="The severity level of the diagnosed problem"
    )
    reasoning: str = Field(
        description="Brief explanation of why this severity was assigned"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the assessment (0.0 to 1.0)",
    )
