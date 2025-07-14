# agents/master_agent.py

from agents.coach_agent import suggest_goal, adjust_feedback
from agents.tracker_agent import log_habit, get_streak

class MasterAgent:
    def __init__(self):
        self.current_goal = None

    def handle_input(self, user_input: str):
        # Step 1: Get or suggest a micro-goal
        self.current_goal = suggest_goal(user_input)
        return self.current_goal

    def handle_response(self, completed: bool, habit: str):
        # Step 2: Log it and get streak
        log_habit(completed)
        streak = get_streak()
        return adjust_feedback(completed, streak, habit), streak
