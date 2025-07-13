import asyncio
from typing import Annotated, List
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
import random
from datetime import datetime

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkODc0NWJmNS04Y2MyLTQ5MjUtOWIzMC1hNDhjNzU5MjQzMjEiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjkzYjJlZDU2LWUxZjgtNDVmZS04OTljLTdjNTY0MDk4NjlmMCJ9.5ozTk8Jg2F63PYld7C3itkwVEet5TlSjgqsRYoeuB50"  # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

# Gamification elements
LEVELS = {
    1: "🌱 Sprout",
    2: "🌿 Sapling",
    3: "🌳 Canopy Hero"
}

BADGES = {
    "commute": "🚲 Pedal Power",
    "diet": "🥦 Green Eater",
    "energy": "💡 Watt Watcher",
    "water": "💧 Aqua Guardian",
    "waste": "♻️ Zero Waste Hero"
}

class EcoGuide:
    def __init__(self):
        self.user_profile = {}
        self.current_habit = None
        self.xp = 0
        self.level = 1
        self.badges_earned = []
        self.streak = 0
    
    async def onboard_user(self, agent_context):
        """Personalized onboarding with 3-5 non-intrusive questions"""
        questions = [
            "1. First, how would you describe your current lifestyle? (e.g., busy parent, student, retired, etc.)",
            "2. What's your biggest sustainability concern? (e.g., climate change, plastic waste, energy use)",
            "3. On a scale of 1-5, how motivated are you to make eco-friendly changes?",
            "4. What's one green habit you already practice?",
            "5. What's your biggest obstacle to being more sustainable? (time, cost, convenience)"
        ]
        
        answers = []
        for question in questions:
            answer = await agent_context.prompt_user(question)
            answers.append(answer)
            agent_context.logger.info(f"Q: {question} → A: {answer}")
        
        # Analyze responses to determine user profile
        self.user_profile = {
            "lifestyle": answers[0],
            "concern": answers[1],
            "motivation": int(answers[2]) if answers[2].isdigit() else 3,
            "existing_habit": answers[3],
            "obstacle": answers[4]
        }
        
        # Determine tone based on profile
        if "student" in answers[0].lower() or "teen" in answers[0].lower():
            self.tone = "playful"
        elif "parent" in answers[0].lower():
            self.tone = "practical"
        elif "retired" in answers[0].lower() or "senior" in answers[0].lower():
            self.tone = "respectful"
        else:
            self.tone = "friendly"
    
    def adapt_language(self, message):
        """Adjust language based on user profile"""
        if self.tone == "playful":
            return f"✨ {message} Let's make this fun!"
        elif self.tone == "practical":
            return f"⏱️ {message} (Quick and easy version!)"
        elif self.tone == "respectful":
            return f"🙏 {message} Whenever you're ready."
        else:
            return f"🌿 {message}"
    
    def generate_micro_habit(self):
        """Create one simple, measurable habit based on user profile"""
        habit_options = []
        
        # Habits based on user concerns
        if "plastic" in self.user_profile["concern"].lower():
            habit_options.append("Use a reusable water bottle today")
            habit_options.append("Say no to one single-use plastic item")
        
        if "energy" in self.user_profile["concern"].lower():
            habit_options.append("Turn off lights when leaving a room today")
            habit_options.append("Unplug one charger when not in use")
        
        if "climate" in self.user_profile["concern"].lower():
            habit_options.append("Try a plant-based meal today")
            habit_options.append("Walk or bike for one short trip")
        
        # Fallback habits if no specific matches
        if not habit_options:
            habit_options = [
                "Sort your recyclables properly today",
                "Take a 5-minute shorter shower",
                "Bring your own bag when shopping",
                "Air dry one load of laundry"
            ]
        
        # Select one habit and explain why it matters
        selected_habit = random.choice(habit_options)
        why_matters = self.explain_why(selected_habit)
        
        return selected_habit, why_matters
    
    def explain_why(self, habit):
        """Connect the habit to its environmental impact"""
        if "water bottle" in habit:
            return "The average person uses 156 plastic bottles annually. Reusing just one saves energy and keeps plastic out of oceans!"
        elif "lights" in habit:
            return "Leaving lights on unnecessarily accounts for 5-10% of home energy use. Small actions add up!"
        elif "plant-based" in habit:
            return "One meatless meal can save ~1,000 liters of water and reduce your carbon footprint by 1kg!"
        elif "walk or bike" in habit:
            return "Short car trips are 60% more polluting per mile. Active transport reduces emissions and boosts health!"
        else:
            return "Small daily actions create big change over time. You're helping build a sustainable future!"
    
    def gamify_response(self, habit):
        """Add gamification elements to the habit"""
        xp_earned = random.randint(5, 15)
        self.xp += xp_earned
        
        # Check for level up
        new_level = min(3, 1 + self.xp // 30)
        if new_level > self.level:
            level_up_msg = f"\n🌟 LEVEL UP! You're now a {LEVELS[new_level]}! 🌟"
            self.level = new_level
        else:
            level_up_msg = ""
        
        # Check for badge
        badge = None
        if "water" in habit.lower():
            badge = BADGES["water"]
        elif "bike" in habit.lower() or "walk" in habit.lower():
            badge = BADGES["commute"]
        elif "meal" in habit.lower() or "plant" in habit.lower():
            badge = BADGES["diet"]
        elif "light" in habit.lower() or "energy" in habit.lower():
            badge = BADGES["energy"]
        
        if badge and badge not in self.badges_earned:
            self.badges_earned.append(badge)
            badge_msg = f"\n🎖️ New Badge Earned: {badge}!"
        else:
            badge_msg = ""
        
        return f"\n🎯 +{xp_earned} XP for taking action! Current level: {LEVELS[self.level]}{level_up_msg}{badge_msg}"
    
    def handle_progress(self, progress_data):
        """React to progress reports from Tracker Agent"""
        if progress_data["days_completed"] > 0:
            self.streak += 1
            encouragement = [
                "You're building momentum!",
                "Consistency is key - great job!",
                "Every action counts - keep it up!",
                "You're making a difference!"
            ][random.randint(0, 3)]
            
            if self.streak % 3 == 0:
                encouragement += f"\n🔥 {self.streak}-day streak! The planet thanks you!"
            
            return encouragement
        else:
            self.streak = 0
            return "No worries! Sustainability is a journey. Would you like to try a different approach?"

@session.bind(
    name="eco_guide",
    description="AI Sustainability Mentor-Coach that helps users build eco-friendly habits through personalized, gamified guidance"
)
async def eco_guide(agent_context: GenAIContext):
    agent_context.logger.info("🌍 Eco-Guide activated!")
    
    eco = EcoGuide()
    
    # Step 1: Personalized onboarding
    await agent_context.send_response("🌱 Welcome to Eco-Guide! Let's learn a bit about you to personalize your sustainability journey.")
    await eco.onboard_user(agent_context)
    
    # Step 2: Generate and present micro-habit
    habit, why = eco.generate_micro_habit()
    eco.current_habit = habit
    
    response = eco.adapt_language(f"Based on your profile, here's today's micro-habit:\n\n✨ {habit}\n\nWhy it matters: {why}")
    await agent_context.send_response(response)
    
    # Get user commitment
    commitment = await agent_context.prompt_user("Does this work for you? (yes/no)")
    if commitment.lower().startswith('n'):
        habit, why = eco.generate_micro_habit()
        eco.current_habit = habit
        await agent_context.send_response(f"No problem! How about this instead:\n\n✨ {habit}\n\nWhy it matters: {why}")
    
    # Step 3: Trigger Habit Tracker Agent
    habit_id = habit.lower().replace(" ", "_")[:20]
    tracker_command = {
        "action": "create_or_update_habit",
        "habit_id": habit_id,
        "description": habit,
        "target_days": 1,
        "tracking_window_days": 3,
        "start_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    await agent_context.send_command("tracker_agent", tracker_command)
    
    # Step 4: Gamify and conclude
    gamified = eco.gamify_response(habit)
    await agent_context.send_response(f"🎉 Habit logged!{gamified}\n\nI'll check in soon to see how it's going!")
    
    agent_context.logger.info(f"Eco-Guide session complete. Habit: {habit}")

async def main():
    print(f"Eco-Guide starting with token: {AGENT_JWT}")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())