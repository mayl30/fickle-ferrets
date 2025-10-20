"""API route handlers"""
from fastapi import APIRouter, status, BackgroundTasks, Body, Depends
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import httpx
import random

from app.schemas.models import (
    Message,
    AffirmationResponse,
    WebhookCallback,
    ExperimentPayload,
    ExperimentSummary,
    AffirmationHistoryItem,
    ChampionPhraseResponse
)
from app.services.ferret_service import (
    process_affirmation_and_callback,
    create_affirmation_record,
    update_affirmation_result,
    create_experiment
)
from app.db.session import get_db
from app.db.models import AffirmationResult, ChampionPhrase, Experiment

router = APIRouter()


@router.get("/", response_model=Message)
async def root() -> Message:
    """Root endpoint returning a welcome message"""
    return Message(message="Welcome to Fickle Ferrets! 🦦 Share your words of affirmation and see if you can spark joy in our discerning ferrets. Visit /docs for interactive documentation.")


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.post("/webhook/ferret-reaction")
async def webhook_ferret_reaction(callback: WebhookCallback) -> dict[str, str]:
    """Webhook endpoint to receive ferret joy reactions"""
    print(f"[WEBHOOK] 📬 Received ferret reaction for affirmation {callback.affirmation_id}")
    print(f"[WEBHOOK] 🦦 Ferret Response: {'✨ JOY SPARKED!' if callback.joy_sparked else '😑 Unimpressed.'}")
    print(f"[WEBHOOK] ⏰ Timestamp: {callback.timestamp}")
    
    # Update database with ferret reaction
    update_affirmation_result(callback.affirmation_id, callback.joy_sparked)
    
    return {"status": "received", "affirmation_id": callback.affirmation_id}


@router.post("/experiment")
async def run_experiment(payload: ExperimentPayload, db: Session = Depends(get_db)) -> dict[str, str | int]: #reconsider return type?
    """Endpoint to run ferret sentiment experiments"""

    # check if an active experiment is already running 
    existing_experiment = db.query(Experiment).filter(
        Experiment.status == "Pending"
    ).first()

    # initialize experiment in database with champion phrase and new phrase if no active experiment exists and payload runs > 0
    experiment_id: int | None = None
    if(payload.runs > 0 and existing_experiment is None):
        champion = db.query(ChampionPhrase).filter(ChampionPhrase.id == 1).first()
        champion_phrase = champion.phrase
        experiment_id = create_experiment(champion_phrase, payload.new_affirmation, payload.runs)

        # check to see if experiment was created successfully
        if(experiment_id is not None):
            try:
                # for each item in array, randomly call affirmation endpoint with either new phrase or None if current run will test champion
                for current_run in range(1, payload.runs + 1):
                    test_phrase = payload.new_affirmation if random.choice([True, False]) else None
                    async with httpx.AsyncClient() as client: 
                        await client.post("http://localhost:8000/affirmation", json={"experiment_id": experiment_id, "suggested_affirmation": test_phrase, "current_run": current_run, "target_runs": payload.runs})

                print(f"[EXPERIMENT] 🧪 Experiment {experiment_id} initiated with {payload.runs} runs testing new affirmation: '{payload.new_affirmation}' against champion: '{champion_phrase}'")
                return {"number of runs": payload.runs, "new phrase to test: ": payload.new_affirmation, "experiment id": experiment_id or "invalid input"}
            except Exception as e:
                # if something goes wrong, mark experiment as failed
                print(f"[EXPERIMENT] ❌ Error initiating experiment: {e}")
                failure = db.query(Experiment).filter(Experiment.id == experiment_id).first()
                failure.status = "Failed"
                db.add(failure)
                db.commit()
        else:
            print(f"[EXPERIMENT] ❌ Error creating experiment in database.")
            return {"message": "Error creating experiment in database."}
    
    # return message if an active experiment is exists or number of runs was 0 or less
    return {"message": "An active experiment is already running or invalid number of runs was provided."}

@router.get("/experiment/history", response_model=list[ExperimentSummary])
async def get_experiment_history(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> list[ExperimentSummary]:
    """Get history of experiments with raw data, win rates, and statuses"""
    
    # retrieve all experiments within limit
    results = db.query(Experiment).order_by(
        Experiment.created_at.desc()
    ).limit(limit).all()
    
    return [
        ExperimentSummary(
            id=result.id,
            variant_a=result.variant_a,
            variant_a_successes=result.variant_a_successes,
            variant_a_runs=result.variant_a_runs,
            variant_b=result.variant_b,
            variant_b_successes=result.variant_b_successes,
            variant_b_runs=result.variant_b_runs,
            variant_a_approval_rate=result.variant_a_approval_rate,
            variant_b_approval_rate=result.variant_b_approval_rate,
            status=result.status,
            failed_runs=result.failed_runs,
            target_runs=result.target_runs,
            created_at=result.created_at
        )
        for result in results
    ]


# if a suggested affirmation is provided, use that, else get current champion from db as originally implemented
@router.post("/affirmation", response_model=AffirmationResponse, status_code=status.HTTP_202_ACCEPTED)
async def share_affirmation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    experiment_id: int | None = Body(default=None, embed=True), # experiment id if this call is part of an experiment
    suggested_affirmation: str | None = Body(default=None, embed=True), # new affirmation to test, will use current champion if this value is not provided
    current_run: int | None = Body(default=None, embed=True), # tells which run we are currently analyzing
    target_runs: int | None = Body(default=None, embed=True) # total number of runs for experiment
) -> AffirmationResponse:
    """Share the champion affirmation with our fickle ferrets - returns immediately and processes asynchronously"""
    
    # Use suggested affirmation if provided, else get current champion from DB
    if(suggested_affirmation):
        words_of_affirmation = suggested_affirmation
        testing_champion = False
    else:
        # Get current champion phrase from database
        champion = db.query(ChampionPhrase).filter(ChampionPhrase.id == 1).first()
        words_of_affirmation = champion.phrase
        testing_champion = True
    
    # Generate unique affirmation ID
    affirmation_id = str(uuid.uuid4())
    
    # Create database record for this affirmation
    create_affirmation_record(affirmation_id, words_of_affirmation)
    
    # Construct webhook URL (assuming localhost for development)
    webhook_url = "http://localhost:8000/webhook/ferret-reaction"
    
    # Add background task to share affirmation with ferrets and get their reaction
    background_tasks.add_task(
        process_affirmation_and_callback,
        affirmation_id,
        words_of_affirmation,
        webhook_url,
        experiment_id,
        testing_champion,
        current_run,
        target_runs
    )
    
    print(f"[AFFIRMATION] 🦦 New affirmation received! ID: {affirmation_id}")
    print(f"[AFFIRMATION] 📝 Using champion phrase: '{words_of_affirmation}'")
    
    # Return immediately with affirmation ID
    return AffirmationResponse(
        affirmation_id=affirmation_id,
        message="Your words have been shared with the ferrets! They're contemplating... 🦦"
    )


@router.get("/champion", response_model=ChampionPhraseResponse)
async def get_champion_phrase(db: Session = Depends(get_db)) -> ChampionPhraseResponse:
    """Get the current champion phrase"""
    champion = db.query(ChampionPhrase).filter(ChampionPhrase.id == 1).first()
    return ChampionPhraseResponse(
        phrase=champion.phrase,
        updated_at=champion.updated_at
    )


@router.get("/affirmations/history", response_model=list[AffirmationHistoryItem])
async def get_affirmation_history(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> list[AffirmationHistoryItem]:
    """Get history of affirmations and ferret reactions"""
    # Query database for recent affirmations
    results = db.query(AffirmationResult).order_by(
        AffirmationResult.created_at.desc()
    ).limit(limit).all()
    
    # Convert to response models
    return [
        AffirmationHistoryItem(
            affirmation_id=result.affirmation_id,
            words_of_affirmation=result.words_of_affirmation,
            joy_sparked=result.joy_sparked,
            created_at=result.created_at,
            callback_received_at=result.callback_received_at
        )
        for result in results
    ]

