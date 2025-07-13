import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from datetime import datetime, timedelta

AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlY2ZhN2E0ZC1jZjkyLTQ5YWMtOTNjMy0xNmE5YTU2YjUxOTAiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjkzYjJlZDU2LWUxZjgtNDVmZS04OTljLTdjNTY0MDk4NjlmMCJ9.B9bCpZOwKV6qfETPrj7un_bYD1Suoba6Sy5VPZaEEZk" # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

@session.bind(
    name="habit_tracker_agent",
    description="Tracks daily habit completion and provides detailed feedback to the Eco-Guide system"
)
async def habit_tracker_agent(agent_context: GenAIContext):
    agent_context.logger.info("📊 Habit Tracker Agent started.")
    
    # Check for new habit commands from Eco-Guide
    if agent_context.command and agent_context.command.get("action") == "create_or_update_habit":
        habit_data = {
            "habit_id": agent_context.command["habit_id"],
            "description": agent_context.command["description"],
            "target_days": agent_context.command["target_days"],
            "tracking_window_days": agent_context.command["tracking_window_days"],
            "start_date": agent_context.command["start_date"],
            "streak": 0,
            "completion_history": [],
            "last_checkin": None,
            "xp_earned": 0
        }
        agent_context.state["current_habit"] = habit_data
        await agent_context.send_response(f"🔄 New habit registered: {habit_data['description']}")
        return
    
    # Check if there's an active habit
    if "current_habit" not in agent_context.state:
        await agent_context.send_response("🌱 No active habit found. Please set a habit with Eco-Guide first.")
        return
    
    current_habit = agent_context.state["current_habit"]
    
    # Daily check-in prompt
    response = (
        f"📝 Today's Eco-Habit: {current_habit['description']}\n\n"
        "How did you do today?\n"
        "1. Completed successfully ✅\n"
        "2. Partially completed ✨\n"
        "3. Didn't complete today ❌\n"
        "4. Need to adjust this habit 🔄"
    )
    await agent_context.send_response(response)

    # Get user response
    answer = await agent_context.prompt_user("Please enter your choice (1-4):")
    
    # Process response
    today = datetime.now().strftime("%Y-%m-%d")
    if answer == "1":  # Completed
        current_habit["streak"] += 1
        current_habit["completion_history"].append({"date": today, "status": "completed", "xp": 10})
        current_habit["xp_earned"] += 10
        
        feedback = (
            f"🎉 Excellent! {current_habit['streak']}-day streak!\n"
            f"➕ 10 XP earned (Total: {current_habit['xp_earned']} XP)\n\n"
            f"\"{current_habit['description']}\" is making a real impact!"
        )
        
    elif answer == "2":  # Partial
        current_habit["streak"] += 0.5
        current_habit["completion_history"].append({"date": today, "status": "partial", "xp": 5})
        current_habit["xp_earned"] += 5
        
        feedback = (
            f"✨ Good effort! Partial completion counts too!\n"
            f"➕ 5 XP earned (Total: {current_habit['xp_earned']} XP)\n\n"
            "What made it challenging today?"
        )
        
    elif answer == "3":  # Didn't complete
        current_habit["streak"] = 0
        current_habit["completion_history"].append({"date": today, "status": "missed", "xp": 0})
        
        feedback = (
            "💪 No worries! Every day is a new opportunity.\n\n"
            "Would reflecting on what happened help for tomorrow?"
        )
        
    elif answer == "4":  # Adjust goal
        feedback = "🔄 Let's work with Eco-Guide to adjust your habit..."
        agent_context.state["needs_habit_adjustment"] = True
    else:
        feedback = "⚠️ Let's try again tomorrow with a valid response."
    
    current_habit["last_checkin"] = today
    await agent_context.send_response(feedback)
    
    # Prepare analytics for Eco-Guide
    completed_days = sum(1 for entry in current_habit["completion_history"] if entry["status"] in ["completed", "partial"])
    total_days = len(current_habit["completion_history"])
    completion_rate = completed_days / total_days if total_days > 0 else 0
    
    progress_report = {
        "habit_id": current_habit["habit_id"],
        "days_completed": completed_days,
        "days_missed": total_days - completed_days,
        "streak": current_habit["streak"],
        "engagement_level": self._determine_engagement(completion_rate),
        "xp_earned": current_habit["xp_earned"],
        "completion_rate": completion_rate
    }
    
    # Send progress report back to Eco-Guide
    await agent_context.send_command("eco_guide", {
        "action": "progress_update",
        "data": progress_report
    })
    
    agent_context.logger.info(
        f"Habit Tracking Update - {current_habit['description']}\n"
        f"Streak: {current_habit['streak']}, "
        f"Completion: {completion_rate:.0%}, "
        f"Total XP: {current_habit['xp_earned']}"
    )

def _determine_engagement(self, completion_rate):
    if completion_rate >= 0.8:
        return "high"
    elif completion_rate >= 0.5:
        return "medium"
    return "low"

async def main():
    print(f"Habit Tracker Agent starting with token: {AGENT_JWT}")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())