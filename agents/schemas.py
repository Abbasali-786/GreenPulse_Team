from uagents import Model

# Define the message model for when the user inputs a habit
class HabitInput(Model):
    user_id: str
    habit: str

# Define the message model for the coach's reply
class CoachReply(Model):
    text: str
    streak: int

# Define the message model for when the user reports completion/missed goal
class UserReport(Model):
    user_id: str
    completed: bool
    habit: str # The habit related to the goal being reported
    goal_id: str # The specific goal that was completed or missed (can be the text of the goal for simplicity)