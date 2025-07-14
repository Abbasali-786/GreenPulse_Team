import asyncio
import json
from typing import Annotated, Optional
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from datetime import date # To get today's date for the command

# Conceptual Firestore imports (these would require Firebase setup)
# from firebase_admin import credentials, firestore
# import firebase_admin

# IMPORTANT: Replace with your actual agent JWT.
# This JWT is from your provided file. Ensure it is valid and unexpired.
AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MDgzYTM5Mi02ZGUyLTRjNmItYjgwZi0wNzQ0M2RkZWM3ZDAiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjkzYjJlZDU2LWUxZjgtNDVmZS04OTljLTdjNTY0MDk4NjlmMCJ9.PFVrW1_aVgOt5TkfAWSQ7uKrKFMKxlhfTysCZYrZEwk" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

# --- Conceptual Firestore Initialization ---
# This part is conceptual. In a real app, you would initialize Firebase
# and get a Firestore client.
# if not firebase_admin._apps:
#     cred = credentials.ApplicationDefault() # Or path to your service account key
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# --- Define potential micro-goals based on your provided list ---
# Expanded with more details for smarter selection and gamification
MICRO_GOALS = {
    "walk_or_bike_short_errand": {
        "description": "Try walking or biking instead of driving for one short errand this week.",
        "why": "Every short drive adds to carbon emissions. Choosing active transport reduces your carbon footprint and is great for health! It's like turning off a small, constant exhaust pipe.",
        "category": "commute",
        "xp": 10,
        "badge": "Green Commuter"
    },
    "shorter_shower": {
        "description": "Take one minute off your shower time today.",
        "why": "Shorter showers save precious water and the energy needed to heat it. Imagine a leaky faucet running all day – that's what long showers can be like for our planet's resources!",
        "category": "water_conservation",
        "xp": 5,
        "badge": "Water Saver"
    },
    "unplug_phantom_load": {
        "description": "Unplug one unused electronic device overnight (e.g., phone charger, laptop charger).",
        "why": "Devices still draw 'phantom' energy when plugged in, even if off. Unplugging them is like turning off a dripping tap of electricity, saving energy and money!",
        "category": "energy_saving",
        "xp": 5,
        "badge": "Energy Detective"
    },
    "plan_one_meal": {
        "description": "Plan one meal this week to use up ingredients you already have.",
        "why": "Reducing food waste saves resources, energy, and prevents methane emissions from landfills. Every bit of food you save from the bin is a win for the planet!",
        "category": "food_waste",
        "xp": 10,
        "badge": "Waste Warrior"
    },
    "reusable_shopping_bag": {
        "description": "Remember to bring a reusable shopping bag on your next trip to the store.",
        "why": "Single-use plastic bags pollute our oceans and landfills. Bringing your own bag prevents waste and shows you're a mindful consumer!",
        "category": "reduce_reuse_recycle",
        "xp": 5,
        "badge": "Reusable Champion"
    },
    "air_dry_laundry": {
        "description": "Air-dry one load of laundry instead of using the dryer.",
        "why": "Dryers are energy hogs! Air-drying saves electricity, reduces your carbon footprint, and is gentle on your clothes. It's like giving your clothes a refreshing outdoor spa day!",
        "category": "energy_saving",
        "xp": 10,
        "badge": "Sun Power Saver"
    },
    "plant_forward_meal": {
        "description": "Try one plant-forward meal this week (e.g., a vegetarian dinner).",
        "why": "Producing meat and dairy has a significant environmental impact. Eating more plants reduces your carbon footprint, saves water, and is great for your health! It's a delicious way to support the planet.",
        "category": "food_choices",
        "xp": 15,
        "badge": "Green Plate Pioneer"
    }
}

# --- Gamification Levels ---
ECO_LEVELS = {
    0: {"name": "Sprout", "message": "You're just beginning your eco-journey! Every step counts!"},
    50: {"name": "Sapling", "message": "You're growing strong! Keep nurturing those green habits!"},
    150: {"name": "Canopy Hero", "message": "You're making a real impact! Your actions are spreading like a forest canopy!"},
    300: {"name": "Forest Guardian", "message": "An inspiring protector of the planet! Your dedication is truly remarkable!"}
}

def get_eco_level_message(xp):
    level_name = "Sprout"
    level_message = ECO_LEVELS[0]["message"]
    for threshold, level_info in sorted(ECO_LEVELS.items(), reverse=True):
        if xp >= threshold:
            level_name = level_info["name"]
            level_message = level_info["message"]
            break
    return f"You are now a **{level_name}**! {level_message}"

@session.bind(
    name="coach_agent",
    description="You are Eco-Guide, a smart, adaptive AI Sustainability Mentor-Coach. You blend behavioral psychology, environmental science, and gamified habit design to help users build eco-friendly habits. You tailor your tone and advice to match the user's background, motivation level, and current lifestyle stage. You are friendly but honest, warm yet unafraid to challenge passive attitudes or rationalizations. You turn everyday living into a low-impact adventure. You empower users to take consistent, meaningful action toward a more sustainable lifestyle by guiding them through one micro-habit at a time—making change fun, personal, and sticky. You work as the Master Agent, collaborating with the Habit Tracker Agent, which logs progress and reports back user behavior patterns. You respond to that feedback and adapt your coaching accordingly."
)
async def coach_agent(
    agent_context: GenAIContext,
    user_input: Annotated[
        str,
        "The user's message or response, including answers to onboarding questions, goal acceptance, or daily check-ins."
    ],
    # Feedback from Habit Tracker Agent
    tracker_feedback: Annotated[
        Optional[dict],
        "Optional: Data received from the Habit Tracker Agent, e.g., {'habit_id': '...', 'days_completed': N, 'days_missed': M, 'streak': S, 'engagement_level': '...'}"
    ] = None,
    # Internal state variables for the coach (these will be updated and returned)
    coaching_stage: Annotated[
        str,
        "The current stage of the coaching process (e.g., 'initial', 'onboarding_q1', 'onboarding_q2', 'onboarding_complete', 'goal_proposed', 'daily_checkin')."
    ] = "initial",
    user_profile: Annotated[
        Optional[dict],
        "A dictionary storing user profile information gathered during onboarding, e.g., {'age_group': 'youth', 'eco_awareness': 'beginner', 'lifestyle': 'commuter', 'xp': 0}."
    ] = None,
    current_micro_goal: Annotated[
        Optional[dict],
        "A dictionary storing the currently assigned micro-goal, e.g., {'habit_id': '...', 'description': '...'}"
    ] = None,
    habit_tracker_history: Annotated[
        Optional[dict],
        "A dictionary to store past tracker feedback for a habit, helpful for context. Keyed by habit_id."
    ] = None
) -> dict: # Changed return type to dict
    """
    AI Sustainability Mentor-Coach that helps users build eco-friendly habits through personalized guidance and motivational support.
    It manages onboarding, suggests micro-goals, and adapts feedback based on habit tracking.
    """
    response_message = ""

    # Initialize state variables if they are None (first call or new session)
    # --- Conceptual: Load user state from Firestore here ---
    # user_id = agent_context.user_id # Assuming user_id is available from context or passed
    # user_data_doc = db.collection("users").document(user_id).get()
    # if user_data_doc.exists:
    #     user_data = user_data_doc.to_dict()
    #     user_profile = user_data.get("user_profile", {})
    #     coaching_stage = user_data.get("coaching_stage", "initial")
    #     current_micro_goal = user_data.get("current_micro_goal", None)
    #     habit_tracker_history = user_data.get("habit_tracker_history", {})
    # else:
    #     # Initialize for new user
    if user_profile is None:
        user_profile = {"xp": 0, "completed_habits": []} # Added XP and completed_habits
    if habit_tracker_history is None:
        habit_tracker_history = {}


    # --- Instruction 2: Adapt to the User (Simplified adaptation) ---
    # More sophisticated tone adaptation would involve an LLM or more complex NLP.
    tone_adj = ""
    if user_profile.get("age_group") == "youth":
        tone_adj = "playful, modern"
    elif user_profile.get("age_group") == "elderly":
        tone_adj = "respectful, gentle"
    elif user_profile.get("motivation_level") == "skeptic":
        tone_adj = "fact-based, humorous"
    
    # Helper to get the current tone prefix
    def get_tone_prefix(stage_tone_adj):
        if "playful" in stage_tone_adj: return "Hey Eco-Adventurer!"
        if "respectful" in stage_tone_adj: return "Greetings, Eco-Champion."
        if "fact-based" in stage_tone_adj: return "Alright, Eco-Analyst!"
        return "Hello there!"


    # --- Instruction 12: Process Feedback from Tracker (High Priority) ---
    if tracker_feedback:
        habit_id = tracker_feedback.get("habit_id")
        days_completed = tracker_feedback.get("days_completed", 0)
        days_missed = tracker_feedback.get("days_missed", 0)
        streak = tracker_feedback.get("streak", 0)
        engagement_level = tracker_feedback.get("engagement_level", "medium")

        # Update habit history
        habit_tracker_history[habit_id] = tracker_feedback

        goal_description = current_micro_goal.get("description", "your sustainability goal") if current_micro_goal else "your sustainability goal"
        goal_xp = current_micro_goal.get("xp", 0)
        goal_badge = current_micro_goal.get("badge")

        if days_completed > 0 and engagement_level == "completed": # Check engagement_level for clear completion
            user_profile["xp"] += goal_xp # Award XP
            if habit_id not in user_profile["completed_habits"]:
                user_profile["completed_habits"].append(habit_id) # Track completed habits for badges
            
            response_message = f"**Fantastic work, Eco-Warrior!** You've successfully completed your goal of '{goal_description}' for {days_completed} day(s)! That's {streak} days in a row! 🎉\n\n" \
                               f"You earned **{goal_xp} XP**! Your total XP is now {user_profile['xp']}. {get_eco_level_message(user_profile['xp'])}\n\n"
            if goal_badge and goal_badge not in user_profile.get("badges", []):
                user_profile.setdefault("badges", []).append(goal_badge)
                response_message += f"You also earned the **'{goal_badge}' Badge!** Keep up the amazing work!\n\n"
            
            response_message += f"Every small action stacks up like building blocks for a greener future. What felt easy about it today? What helped you remember?" # Instruction 6: Encourage Reflection
        
        elif engagement_level == "missed": # Clear miss
            response_message = f"Hey there! It looks like '{goal_description}' was a bit tough recently. No worries at all, everyone hits bumps. What got in your way today? Remember, progress over perfection!" # Instruction 4 & Note 4: Empathy for Imperfection
            # Instruction 8: Offer Alternatives, Not Guilt
            response_message += "\n\nPerhaps we could try making the goal even smaller, or explore a different approach? Would a post-it reminder help?" # Instruction 12: Suggest reflection
        
        elif engagement_level == "struggling": # User reported struggling
            response_message = f"Hey {tone_adj.capitalize()} Eco-Friend! It seems like you've been putting in effort with '{goal_description}', but it's been tricky. What specifically got in your way? Sometimes, even a tiny tweak can make a big difference. How about we brainstorm some solutions together?" # Instruction 6: Encourage Reflection
            # Instruction 7: Handle Resistance with Kind Challenge (if user explicitly justifies)
            # This would need more NLP to detect justification, for now, just offer help.

        coaching_stage = "daily_checkin" # Return to daily coaching after processing feedback

        # --- Conceptual: Save updated user state to Firestore here ---
        # db.collection("users").document(user_id).set({
        #     "user_profile": user_profile,
        #     "coaching_stage": coaching_stage,
        #     "current_micro_goal": current_micro_goal,
        #     "habit_tracker_history": habit_tracker_history
        # })

        return {
            "response": response_message,
            "coaching_stage": coaching_stage,
            "user_profile": user_profile,
            "current_micro_goal": current_micro_goal,
            "habit_tracker_history": habit_tracker_history
        }

    # --- Main Coaching Flow based on coaching_stage ---
    if coaching_stage == "initial":
        # Instruction 1: Personalized Onboarding - Ask 3-5 non-intrusive questions
        response_message = f"{get_tone_prefix(tone_adj)} I'm Eco-Guide, your personalized AI Sustainability Mentor-Coach. I'm here to help you make green living fun and easy. To get started, could you tell me a little bit about your current lifestyle? For example, how do you usually get around on a daily basis (walk, bike, car, public transit)?"
        coaching_stage = "onboarding_q1"
    elif coaching_stage == "onboarding_q1":
        user_profile["commute"] = user_input # Store response
        response_message = f"Thanks for sharing, {tone_adj} friend! That gives me a good idea. Next, how would you describe your current awareness about environmental issues? Are you a beginner, somewhat aware, or an eco-expert?"
        coaching_stage = "onboarding_q2"
    elif coaching_stage == "onboarding_q2":
        user_profile["eco_awareness"] = user_input # Store response
        response_message = f"Got it! One last quick question for now: What's one thing you're hoping to achieve by being more sustainable, or what's a challenge you've faced trying to be more eco-friendly?"
        coaching_stage = "onboarding_q3"
    elif coaching_stage == "onboarding_q3":
        user_profile["goals_challenges"] = user_input # Store response
        
        # Heuristic for age_group and motivation_level based on input
        if "school" in user_input.lower() or "student" in user_input.lower() or "young" in user_input.lower():
            user_profile["age_group"] = "youth"
        elif "retire" in user_input.lower() or "grandparent" in user_input.lower():
            user_profile["age_group"] = "elderly"
        
        if "skeptic" in user_input.lower() or "doubt" in user_input.lower() or "hard" in user_input.lower():
            user_profile["motivation_level"] = "skeptic"
        elif "eager" in user_input.lower() or "excited" in user_input.lower() or "committed" in user_input.lower():
            user_profile["motivation_level"] = "committed"

        # Instruction 3: One Habit at a Time - Suggest a personalized micro-goal
        # Smarter heuristic for goal selection
        suggested_goal_key = None
        if "car" in user_profile.get("commute", "").lower() or "drive" in user_profile.get("commute", "").lower():
            suggested_goal_key = "walk_or_bike_short_errand"
        elif "water" in user_profile.get("goals_challenges", "").lower() or "shower" in user_input.lower():
            suggested_goal_key = "shorter_shower"
        elif "electricity" in user_profile.get("goals_challenges", "").lower() or "lights" in user_input.lower() or "energy" in user_input.lower():
            suggested_goal_key = "unplug_phantom_load"
        elif "food waste" in user_profile.get("goals_challenges", "").lower() or "compost" in user_input.lower():
            suggested_goal_key = "plan_one_meal"
        elif "plastic" in user_profile.get("goals_challenges", "").lower() or "bags" in user_input.lower():
            suggested_goal_key = "reusable_shopping_bag"
        elif "laundry" in user_input.lower() or "dryer" in user_input.lower():
            suggested_goal_key = "air_dry_laundry"
        elif "diet" in user_input.lower() or "meat" in user_input.lower() or "plant" in user_input.lower():
            suggested_goal_key = "plant_forward_meal"
        
        # Fallback if no specific goal found or if already completed
        if not suggested_goal_key or suggested_goal_key in user_profile["completed_habits"]:
            # Try to pick a new, uncompleted goal
            for key, details in MICRO_GOALS.items():
                if key not in user_profile["completed_habits"]:
                    suggested_goal_key = key
                    break
            if not suggested_goal_key: # If all goals completed, offer to repeat or explore more
                response_message = f"{get_tone_prefix(tone_adj)} Wow, it looks like you've tackled all the micro-goals I have for now! You're a true Eco-Champion! Would you like to revisit some, or perhaps explore a deeper topic like systemic impact?"
                coaching_stage = "all_goals_completed"
                # --- Conceptual: Save state here ---
                # db.collection("users").document(user_id).set({ ... })
                return {
                    "response": response_message,
                    "coaching_stage": coaching_stage,
                    "user_profile": user_profile,
                    "current_micro_goal": current_micro_goal,
                    "habit_tracker_history": habit_tracker_history
                }

        goal_details = MICRO_GOALS.get(suggested_goal_key)
        
        if goal_details:
            current_micro_goal = goal_details # Update current_micro_goal
            response_message = f"{get_tone_prefix(tone_adj)} Based on what you've shared, how about we start with a super simple micro-goal? " \
                               f"Your daily quest could be: **'{goal_details['description']}'**\n\n" \
                               f"**Why this matters:** {goal_details['why']}\n\n" \
                               f"Ready to give this a try? Just say 'Yes!' or 'Sounds good!' to confirm!"
            coaching_stage = "goal_proposed"
        else:
            # Fallback if somehow no goal could be selected
            response_message = f"{get_tone_prefix(tone_adj)} I'm having a little trouble finding the perfect goal right now, but how about we try: **'{MICRO_GOALS['unplug_phantom_load']['description']}'**? It's a great start!\n\n" \
                               f"**Why this matters:** {MICRO_GOALS['unplug_phantom_load']['why']}\n\nReady to start your eco-adventure?"
            current_micro_goal = MICRO_GOALS["unplug_phantom_load"]
            coaching_stage = "goal_proposed"

    elif coaching_stage == "goal_proposed":
        if "yes" in user_input.lower() or "sounds good" in user_input.lower() or "i'm in" in user_input.lower() or "ready" in user_input.lower():
            if current_micro_goal:
                # Instruction 11: Trigger the Habit Tracker Agent
                today = date.today().isoformat()
                tracker_command = {
                    "action": "create_or_update_habit",
                    "habit_id": current_micro_goal["habit_id"],
                    "description": current_micro_goal["description"],
                    "target_days": 1, # Daily goal
                    "tracking_window_days": 1, # Track for today
                    "start_date": today
                }
                response_message = f"**That's the spirit, Eco-Champion!** Let's get this habit rolling! Your daily quest begins now! Remember, small steps lead to big adventures. I'll check in with you tomorrow! " \
                                   f"@@COMMAND {json.dumps(tracker_command)} @@END"
                coaching_stage = "daily_checkin"
            else:
                response_message = f"{get_tone_prefix(tone_adj)} It seems I lost track of your goal! Can you remind me what we agreed on, or would you like to set a new one?"
                coaching_stage = "initial" # Restart or guide back
        else:
            # Instruction 7: Handle Resistance with Kind Challenge / Instruction 8: Offer Alternatives
            response_message = f"{get_tone_prefix(tone_adj)} No worries if that goal doesn't quite fit! What's holding you back? Is there something else you'd prefer to focus on, or would you like me to suggest an alternative? Remember, we're finding *your* path to sustainability!"
            coaching_stage = "goal_proposed_renegotiate" # New stage for re-negotiation

    elif coaching_stage == "goal_proposed_renegotiate":
        # Simple renegotiation, could be more complex
        if "alternative" in user_input.lower() or "different" in user_input.lower() or "another" in user_input.lower():
            # Offer another goal from the list that wasn't previously suggested
            # Try to find an uncompleted goal that's not the current one
            new_goal_key = None
            for key, details in MICRO_GOALS.items():
                if key != current_micro_goal.get("habit_id") and key not in user_profile["completed_habits"]:
                    new_goal_key = key
                    break
            
            if new_goal_key:
                new_goal_details = MICRO_GOALS.get(new_goal_key)
                current_micro_goal = new_goal_details # Update current_micro_goal
                response_message = f"{get_tone_prefix(tone_adj)} Okay, no problem! How about this instead: **'{new_goal_details['description']}'**?\n\n**Why this matters:** {new_goal_details['why']}\n\nDoes this feel like a better fit?"
                coaching_stage = "goal_proposed"
            else:
                response_message = f"{get_tone_prefix(tone_adj)} Hmm, I'm out of easy alternatives for now! Would you like to tell me what kind of eco-habit you're most interested in trying, or perhaps we can revisit your initial profile questions?"
                coaching_stage = "onboarding_q3" # Go back to understanding their interests more
        else:
            # Instruction 7: Handle Resistance (if user is just saying no without asking for alternative)
            response_message = f"{get_tone_prefix(tone_adj)} I understand. Sometimes finding the right starting point takes a moment. You mentioned caring about the planet earlier – how do you feel about this gap between your intention and action? What's one area of sustainability you feel most connected to, even if it's small?" # Instruction 7
            coaching_stage = "onboarding_q3" # Go back to understanding their interests more

    elif coaching_stage == "daily_checkin":
        # This stage primarily waits for tracker_feedback (handled at the top) or user direct inquiry
        # Instruction 6: Encourage Reflection (after user input without tracker_feedback)
        if "how" in user_input.lower() or "feel" in user_input.lower() or "easy" in user_input.lower() or "hard" in user_input.lower() or "struggle" in user_input.lower():
            response_message = f"That's a great question for reflection! What felt easy about working on '{current_micro_goal.get('description', 'your goal')}' today? What got in your way, if anything? How did it make you feel? Remember, every experience is a learning opportunity!"
        else:
            response_message = f"Hi again! Ready for another eco-adventure today? Remember your goal: **'{current_micro_goal.get('description', 'your goal')}'**! Did you manage to complete it? Or perhaps you have a question or an update for me?" # Instruction 9: Follow Up Consistently

    elif coaching_stage == "all_goals_completed":
        # User has completed all defined micro-goals
        response_message = f"{get_tone_prefix(tone_adj)} You've truly mastered the basics! Now, would you like to revisit some past goals to strengthen them, or are you ready to dive into a deeper understanding of systemic impact, like where our products truly come from?" # Instruction 10: Build toward Systems Thinking
    
    else:
        response_message = f"{get_tone_prefix(tone_adj)} I'm not quite sure how to proceed. Can we start with what you'd like to work on today? Or perhaps try saying 'Hello Eco-Guide' to restart our journey?"
        coaching_stage = "initial" # Reset or guide back to a known state

    # --- Conceptual: Save updated user state to Firestore here ---
    # db.collection("users").document(user_id).set({
    #     "user_profile": user_profile,
    #     "coaching_stage": coaching_stage,
    #     "current_micro_goal": current_micro_goal,
    #     "habit_tracker_history": habit_tracker_history
    # })

    # Return all updated state variables along with the response message
    return {
        "response": response_message,
        "coaching_stage": coaching_stage,
        "user_profile": user_profile,
        "current_micro_goal": current_micro_goal,
        "habit_tracker_history": habit_tracker_history
    }

async def main():
    print(f"Eco-Guide Coach Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())

