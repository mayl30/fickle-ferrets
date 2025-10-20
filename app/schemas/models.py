"""Pydantic models for request/response validation"""
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Generic message response"""
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChampionPhraseResponse(BaseModel):
    """Current champion phrase"""
    phrase: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AffirmationResponse(BaseModel):
    """Response when affirmation is shared with ferrets"""
    affirmation_id: str = Field(..., description="Unique affirmation identifier")
    message: str = Field(..., description="Status message")


class FerretJoyResult(BaseModel):
    """Response from Spark API indicating if ferrets felt joy"""
    joy_sparked: bool


class WebhookCallback(BaseModel):
    """Webhook callback payload with ferret joy result"""
    affirmation_id: str = Field(..., description="Affirmation identifier")
    joy_sparked: bool = Field(..., description="Whether the words sparked joy in our fickle ferrets")
    timestamp: datetime = Field(default_factory=datetime.now)


class ExperimentPayload(BaseModel):
    """Experiment payload with number of runs and new affirmation"""
    runs: int = Field(..., description="Number of experiment runs")
    new_affirmation: str = Field(..., description="New affirmation to test with ferrets")
    timestamp: datetime = Field(default_factory=datetime.now)


class ExperimentSummary(BaseModel):
    """Summary of an experiment run"""
    id: int = Field(..., description="Experiment run identifier")
    variant_a: str = Field(..., description="Champion affirmation phrase")
    variant_a_successes: int = Field(..., description="Number of successful variant A runs")
    variant_a_runs: int = Field(..., description="Total number of variant A runs")
    variant_b: str = Field(..., description="New affirmation phrase")
    variant_b_successes: int = Field(..., description="Number of successful variant B runs")
    variant_b_runs: int = Field(..., description="Total number of variant B runs")
    variant_a_approval_rate: float | None = Field(..., description="Approval rate for variant A")
    variant_b_approval_rate: float | None = Field(..., description="Approval rate for variant B")
    status: str = Field(..., description="Status of the experiment run")
    failed_runs: int = Field(..., description="Number of failed runs")
    target_runs: int = Field(..., description="Total target runs for the experiment")
    created_at: datetime = Field(..., description="When the experiment was created")
    
    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models


class AffirmationHistoryItem(BaseModel):
    """History item for affirmations stored in database"""
    affirmation_id: str = Field(..., description="Unique affirmation identifier")
    words_of_affirmation: str = Field(..., description="The words shared with the ferrets")
    joy_sparked: bool = Field(..., description="Whether joy was sparked")
    created_at: datetime = Field(..., description="When the affirmation was created")
    callback_received_at: datetime | None = Field(None, description="When the callback was received")
    
    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models

