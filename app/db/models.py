"""SQLAlchemy database models"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric
from datetime import datetime
from .base import Base


class ChampionPhrase(Base):
    """Store the current champion affirmation phrase"""
    __tablename__ = "champion_phrase"
    
    id = Column(Integer, primary_key=True, default=1)  # Always ID=1 (singleton)
    phrase = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ChampionPhrase(phrase={self.phrase})>"


class AffirmationResult(Base):
    """Store ferret affirmation results"""
    __tablename__ = "affirmation_results"
    
    affirmation_id = Column(String, primary_key=True, index=True)
    words_of_affirmation = Column(String, nullable=False)
    joy_sparked = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    callback_received_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AffirmationResult(id={self.affirmation_id}, joy={self.joy_sparked})>"


class Experiment(Base):
    """Store experiment run results"""
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True) # Experiment ID
    variant_a = Column(String, nullable=False) # champion phrase for this run
    variant_a_successes = Column(Integer, default=0, nullable=False) # champion phrase approval rate
    variant_a_runs = Column(Integer, default=0, nullable=False) # number of times variant_a was tested
    variant_b = Column(String, nullable=False) # new_affirmation
    variant_b_successes = Column(Integer, default=0, nullable=True) # new_affirmation approval rate
    variant_b_runs = Column(Integer, default=0, nullable=False) # number of times variant_b was tested
    variant_a_approval_rate = Column(Numeric, default=None, nullable=True) # calculated approval rate for variant_a
    variant_b_approval_rate = Column(Numeric, default=None, nullable=True) # calculated approval rate for variant_b
    failed_runs = Column(Integer, default=0, nullable=False) # number of failed runs
    target_runs = Column(Integer, nullable=False) # Total runs to complete
    status = Column(String, default="Pending", nullable=False)  # "Pending", "Completed", "Failed" (ideally this would be an enum, but I think I've already spent long enough on this ^_^;)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self) -> str:
        return f"<Experiment(id={self.id}, a_approval={self.variant_a_approval_rate}, b_approval={self.variant_b_approval_rate}, status={self.status})>"