"""Service for processing ferret affirmations and interactions"""
import httpx
import asyncio
import random
from datetime import datetime

from ..db.models import AffirmationResult, Experiment, ChampionPhrase
from ..db.session import SessionLocal


def create_affirmation_record(affirmation_id: str, words_of_affirmation: str) -> None:
    """Create initial database record for new affirmation"""
    db = SessionLocal()
    try:
        # Create a temporary record with joy_sparked=False (will be updated later)
        db_affirmation = AffirmationResult(
            affirmation_id=affirmation_id,
            words_of_affirmation=words_of_affirmation,
            joy_sparked=False,  # Placeholder, will be updated
            created_at=datetime.now()
        )
        db.add(db_affirmation)
        db.commit()
        print(f"[DATABASE] 💾 Created affirmation record: {affirmation_id}")
    except Exception as e:
        print(f"[DATABASE] ❌ Error creating affirmation record: {e}")
        db.rollback()
    finally:
        db.close()


def update_affirmation_result(affirmation_id: str, joy_sparked: bool) -> None:
    """Update affirmation record with ferret reaction result"""
    db = SessionLocal()
    try:
        db_affirmation = db.query(AffirmationResult).filter(
            AffirmationResult.affirmation_id == affirmation_id
        ).first()
        
        if db_affirmation:
            db_affirmation.joy_sparked = joy_sparked
            db_affirmation.callback_received_at = datetime.now()
            db.commit()
            print(f"[DATABASE] 💾 Updated affirmation result: {affirmation_id} (joy={joy_sparked})")
        else:
            print(f"[DATABASE] ⚠️  Affirmation not found: {affirmation_id}")
    except Exception as e:
        print(f"[DATABASE] ❌ Error updating affirmation result: {e}")
        db.rollback()
    finally:
        db.close()


# create endpoint to create experiment run (which will both check if one is active and return the id of the run created if no run is active)
def create_experiment(variant_a: str, variant_b: str, target_runs: int) -> int:
    """Create a new experiment run in the database"""
    db = SessionLocal()
    try:
        # add new ExperimentRun to the database
        db_experiment = Experiment(
            variant_a=variant_a,
            variant_b=variant_b,
            status="Pending",
            target_runs=target_runs,
            created_at=datetime.now()
        )
        db.add(db_experiment)
        db.commit()
        print(f"[DATABASE] 💾 Created new experiment: {db_experiment.id}")
        return db_experiment.id
    except Exception as e:
        print(f"[DATABASE] ❌ Error creating experiment: {e}")
        db.rollback()
    finally:
        db.close()


# update experiment with data
def update_experiment(experiment_id: int, variant_a_success: bool, variant_b_success: bool, variant_tested: str | None, status: str | None = None) -> None:
    """Update experiment run in the database"""
    db = SessionLocal()
    try:
        # get experiment run by id
        experiment = db.query(Experiment).filter(
            Experiment.id == experiment_id
        ).first()
        
        # figure out which variant was tested and update accordingly
        if experiment: # check that experiment was found
            if(variant_tested == "A"): # if variant A was tested
                experiment.variant_a_runs += 1 # increment number of total variant A runs
                if(variant_a_success): # if variant A was successful
                    experiment.variant_a_successes += 1 # increment number of successful variant A runs
            elif(variant_tested == "B"): # else, variant_tested == "B"
                experiment.variant_b_runs += 1 # increment number of total variant B runs
                if(variant_b_success): # if variant B was successful
                    experiment.variant_b_successes += 1 # increment number of successful variant B runs
            elif(variant_tested is None):
                print(f"[LOG] No variant provided, ferret response call may have failed")
            else:
                print(f"[WARNING] ⚠️  Invalid variant tested: {variant_tested}")
                return

            # if status is "Failed", increment failed runs
            if(status == "Failed"):
               # failed runs +1 
                experiment.failed_runs += 1 

            # check if number of target runs has been reached
            if(experiment.variant_a_runs + experiment.variant_b_runs + experiment.failed_runs == experiment.target_runs):
                # mark experiment as completed
                experiment.status = "Completed"

                # do approval rate calculations
                if(experiment.variant_a_runs > 0):
                    experiment.variant_a_approval_rate = (experiment.variant_a_successes / experiment.variant_a_runs) if experiment.variant_a_runs > 0 else 0
                if(experiment.variant_b_runs > 0):
                    experiment.variant_b_approval_rate = (experiment.variant_b_successes / experiment.variant_b_runs) if experiment.variant_b_runs > 0 else 0

                # update champion phrase if variant B did better than variant A
                if(experiment.variant_b_approval_rate is not None and experiment.variant_a_approval_rate is not None):
                    if(experiment.variant_b_approval_rate > experiment.variant_a_approval_rate):
                        # update champion phrase in database
                        champion = db.query(ChampionPhrase).filter(ChampionPhrase.id == 1).first()
                        if champion:
                            champion.phrase = experiment.variant_b
                            champion.updated_at = datetime.now()
                            db.add(champion)
                            print(f"[DATABASE] 💾 Updated champion phrase to: '{experiment.variant_b}' based on experiment {experiment_id} results.")
            db.commit()
            print(f"[INFO] 💾 Updated experiment run {experiment_id} status to {status}")
    except Exception as e:
        print(f"[ERROR] ❌ Error updating experiment run: {e}")
        db.rollback()
    finally:
        db.close()


async def process_affirmation_and_callback(affirmation_id: str, words_of_affirmation: str, webhook_url: str, experiment_id: int, testing_champion: bool, current_run: int | None, target_runs: int | None) -> None:
    """Background task that shares words with ferrets, waits for their reaction, then posts to webhook"""
    try:
        # Share words with the fickle ferrets
        async with httpx.AsyncClient() as client:
            print(f"[FERRETS] 🦦 Sharing affirmation {affirmation_id} with our fickle ferrets...")
            response = await client.post(
                "https://spark-joy.local-services.workers.dev/spark",
                json={"input": words_of_affirmation},
                headers={"Content-Type": "application/json"}
            )
            ferret_joy = response.json()["result"]
            
            # Ferrets are thinking... (they're very fickle and take their time)
            delay = random.uniform(0.0, 1.0)
            print(f"[FERRETS] 🤔 Ferrets are contemplating... ({delay:.2f} seconds)")
            await asyncio.sleep(delay)
            
            # Post ferret reaction to our webhook endpoint
            callback_payload = {
                "affirmation_id": affirmation_id,
                "joy_sparked": ferret_joy,
                "timestamp": datetime.now().isoformat()
            }
            print(f"[FERRETS] 📢 Posting ferret reaction to webhook...")
            await client.post(webhook_url, json=callback_payload)
            print(f"[FERRETS] {'✨ Ferrets sparked with joy!' if ferret_joy else '😔 Ferrets remain unimpressed.'} (ID: {affirmation_id})")

            # update experiment with ferret results for this run if experiment_id was provided
            if(experiment_id is not None):
                # update db with experiment results
                variant_a_success = ferret_joy if testing_champion else False
                variant_b_success = ferret_joy if not testing_champion else False

                # check if this is the last run of the experiment
                status = "Pending"
                if((current_run is not None) and (target_runs is not None) and (current_run == target_runs)):
                    status = "Completed"

                # update expieriment record in db
                update_experiment(experiment_id, variant_a_success, variant_b_success,  "A" if testing_champion else "B")

                # in here we might want to do the math to figure out actual approal rates 
                if(status == "Completed"):
                    print(f"[INFO] 📊 All {target_runs} runs completed for affirmation ID: {affirmation_id}")
    except Exception as e:
        # update db with status = "Failed" for the experiment run if error occurs
        print(f"[FERRETS] ❌ Error processing affirmation {affirmation_id}: {e}")
        update_experiment(experiment_id, False , False, None, "Failed")

