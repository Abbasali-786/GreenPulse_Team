import asyncio
from typing import Annotated, Optional
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from datetime import date # Added for potential last_completion_date update

# Conceptual Firestore imports (these would require Firebase setup)
# from firebase_admin import credentials, firestore
# import firebase_admin

# IMPORTANT: Replace with your actual agent JWT.
# This JWT is from your provided file. Ensure it is valid and unexpired.
AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNTdhYWE0ZS0yYmJiLTQyMzUtYTAyMi0yOWExZWUzYzA0ZDYiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjkzYjJlZDU2LWUxZjgtNDVmZS04OTljLTdjNTY0MDk4NjlmMCJ9.e9sSUghD6TLRh6hmhBDqjCLNLasCr4p-VYeT-NEz0mQ" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

# --- Conceptual Firestore Initialization ---
# if not firebase_admin._apps:
#     cred = credentials.ApplicationDefault() # Or path to your service account key
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

@session.bind(
    name="habit_tracker_agent",
    description="Tracks daily habit completion (Yes/No input) and sends consistency insights to the Coach Agent for tone/goal adjustment."
)
async def habit_tracker_agent(
    agent_context: GenAIContext,
    user_response: Annotated[
        str,
        "The user's response indicating habit completion (e.g., 'Yes', 'No', 'I did it', 'Couldn't today')."
    ],
    goal_to_track: Annotated[
        str,
        "The specific micro-goal that the user is currently tracking, as provided by the Coach Agent."
    ],
    # This would typically interact with a persistence layer (e.g., JSON/Firebase)
    # to store streak data. For MVP, we'll simulate.
    streak_data: Annotated[
        Optional[dict],
        "Optional: Dictionary containing streak information, e.g., {'current_streak': 3, 'last_completion_date': '2025-07-13'}."
    ] = None
) -> dict:
    """
    Accepts Yes/No input for daily habit completion, detects consistency or drop-off,
    and sends insights back to the Coach Agent for tone/goal adjustment.
    """
    response_lower = user_response.lower()
    habit_completed = False
    status_for_coach = "missed" # Default status if not completed

    # Simulate streak tracking (would be more robust with a proper data store)
    # --- Conceptual: Load streak data from Firestore here ---
    # user_id = agent_context.user_id # Assuming user_id is available from context or passed
    # habit_id = "some_derived_habit_id_from_goal_to_track" # You'd need a consistent ID
    # streak_doc = db.collection("user_streaks").document(f"{user_id}_{habit_id}").get()
    # if streak_doc.exists:
    #     streak_data = streak_doc.to_dict()
    # else:
    if streak_data is None:
        streak_data = {"current_streak": 0, "last_completion_date": None}

    # Simple logic to detect completion
    if "yes" in response_lower or "i did it" in response_lower or "yep" in response_lower or "completed" in response_lower:
        habit_completed = True
        status_for_coach = "completed"
    elif "no" in response_lower or "couldn't" in response_lower or "nope" in response_lower or "missed" in response_lower:
        status_for_coach = "missed"
    elif "struggle" in response_lower or "hard" in response_lower or "tricky" in response_lower:
        status_for_coach = "struggling"

    if habit_completed:
        streak_data["current_streak"] += 1
        streak_data["last_completion_date"] = date.today().isoformat() # Update date
    else:
        # If missed or struggling, reset streak unless it's a "struggling" state that needs different handling
        # For "struggling", we might not reset the streak immediately, but for "missed" we do.
        if status_for_coach == "missed":
            streak_data["current_streak"] = 0
        # If struggling, streak might or might not reset based on specific rules.
        # For simplicity, we'll let the coach decide how to interpret "struggling" for streak purposes.


    # This agent's primary output is the insight for the Coach Agent.
    # --- Conceptual: Save updated streak data to Firestore here ---
    # db.collection("user_streaks").document(f"{user_id}_{habit_id}").set(streak_data)

    return {
        "habit_status": status_for_coach,
        "message_for_coach": f"User reported '{user_response}' for goal '{goal_to_track}'. Current status: {status_for_coach}. Streak: {streak_data['current_streak']}.",
        "streak_info": streak_data
    }

async def main():
    print(f"Habit Tracker Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())

