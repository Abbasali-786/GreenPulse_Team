import random

SUGGESTED_HABITS = [
    "I drive to nearby places",
    "I use plastic bags regularly",
    "I leave lights on unnecessarily",
    "I buy bottled water daily",
    "I take long showers",
]

def suggest_goal(habit: str) -> str:
    habit = habit.strip().lower()

    if not habit or "start" in habit or "journey" in habit or len(habit.split()) < 3:
        suggested_list = "\n".join([f"- {h}" for h in SUGGESTED_HABITS])
        return (
            "👋 Welcome! I'm your Sustainability Coach 🤖\n\n"
            "To begin your journey, tell me one habit you'd like to change.\n"
            "Here are some ideas you can type:\n\n"
            f"{suggested_list}\n\n"
            "Once you enter a habit, I'll suggest a personal micro-goal. 🌱"
        )

    responses = [
        f"💡 Try replacing '{habit}' with walking, biking, or public transport — small step, big impact!",
        f"🌿 Let's improve '{habit}' — switch to reusable or energy-efficient options.",
        f"♻️ Your habit '{habit}' is common — but we can do better! Try a planet-positive swap.",
        f"🌎 You’ve got this! Reduce the impact of '{habit}' with a greener choice.",
        f"🚀 Micro-goal: Make one change around '{habit}' today and track your impact!"
    ]
    return random.choice(responses)

def adjust_feedback(done: bool, streak: int, habit: str = "") -> str:
    if done:
        positive_feedback = [
            f"🔥 Fantastic! That’s {streak} day(s) of action. You're making a real difference. 🌍",
            f"✅ Awesome! Your habit '{habit}' is changing. You’re on a sustainability roll!",
            f"🌱 Great job completing your goal! That {streak}-day streak is impressive!",
        ]
        return random.choice(positive_feedback)
    else:
        motivation = [
            "😌 Everyone slips up sometimes. What matters is that you come back stronger!",
            f"🌞 Let’s reset. Try improving '{habit}' again tomorrow with a fresh start!",
            "📆 It’s okay! Tomorrow is another chance to make progress. Keep going 💪",
        ]
        return random.choice(motivation)
