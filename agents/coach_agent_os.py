# agents/coach_agent_os.py

import sys
import os
import google.generativeai as genai # Import the Gemini SDK

# Add the project root directory to the Python path
# This allows absolute imports like 'from agents.schemas import ...' to work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low # Keep this, useful for testnet/mainnet

# Import your message schemas. Ensure these names match your schemas.py file.
# The 'agent_protos' is a common convention, but if your file is just 'schemas.py'
# and you import directly, adjust accordingly.
# Assuming your schemas are in agents/schemas.py and are named HabitInput, UserReport, CoachReply
from agents.schemas import HabitInput, UserReport, CoachReply

# --- Configure the Gemini API key ---
# IMPORTANT: Replace "YOUR_GEMINI_API_KEY" with the actual API key you obtained.
# For better security in production, you would load this from an environment variable:
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key="AIzaSyB3PVA7WIWjO47sx13mYx3p4v7T6BqqNNU") # <<<--- REPLACE THIS WITH YOUR ACTUAL KEY!

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-pro')

# --- Define the Agent's Protocol ---
# A protocol groups message handlers and makes the agent's responsibilities clear.
coach_proto = Protocol("CoachProtocol")

# --- Agent State (Simple for MVP) ---
# This dictionary will hold the agent's internal state (like streak, current goal).
# Note: This state is in-memory and will reset if the agent process restarts.
# For persistent state, you'd integrate a database (e.g., Firestore, SQLite).
agent_state = {"streak": 0, "current_goal": "", "current_user_id": ""}

# --- Agent Instance ---
# This is the agent instance that will be added to the Bureau in main.py.
# The 'name' should match what you expect to route messages to (e.g., "master" if your URL is /agent/master/message)
# The 'seed' is a secret phrase for your agent's identity; make it unique and secure.
agent = Agent(
    name="master", # This name is used by HTTPController to route messages to this agent
    seed="MySecretEcoPathwaY", # <<<--- CHANGE THIS TO A UNIQUE, SECURE PHRASE!
)

# --- Agent Message Handlers ---

# Handler for initial habit input from the frontend (via HTTPController)
@coach_proto.on_message(model=HabitInput, replies=CoachReply)
async def handle_habit_input(ctx: Context, sender: str, msg: HabitInput):
    ctx.logger.info(f"Received HabitInput from {sender} (User ID: {msg.user_id}): Habit='{msg.habit}'")
    
    # Update in-memory state (for this demo)
    agent_state["current_user_id"] = msg.user_id
    
    # --- Prompt for LLM (Gemini) ---
    prompt = f"""
    You are a friendly, encouraging, and highly practical sustainability coach named 'Coach AI'.
    Your goal is to help users adopt eco-friendly habits through small, actionable daily micro-goals.
    Always address the user directly and maintain a positive, supportive tone.

    User's current habit to improve: "{msg.habit}"

    Based on this habit, suggest a single, specific, and easy-to-start micro-goal for TODAY.
    The goal should directly address the habit and be something they can realistically do without much effort.
    Keep the goal concise (under 25 words).
    Example: If the user drives to nearby places, a goal could be "Today, choose one short trip and walk or cycle instead of driving."

    Current green streak: {agent_state["streak"]} days. Use this to encourage the user if it's high.

    Your response should start directly with the micro-goal, followed by encouragement.
    """

    try:
        # Generate content using the Gemini model
        response = model.generate_content(prompt)
        generated_goal = response.text.strip() # Get the text from Gemini's response
        
        # Store the generated goal in the agent's state
        agent_state["current_goal"] = generated_goal

        # Send the Gemini-generated goal back to the sender (HTTPController)
        await ctx.send(
            sender,
            CoachReply(text=generated_goal, streak=agent_state["streak"])
        )
        ctx.logger.info(f"Sent CoachReply: '{generated_goal}'")

    except Exception as e:
        ctx.logger.error(f"Error generating content with LLM: {e}")
        # Send a user-friendly error message if Gemini fails
        await ctx.send(
            sender,
            CoachReply(
                text="I'm sorry, I couldn't generate a goal right now. My AI brain might be busy. Please try again in a moment!",
                streak=agent_state["streak"]
            )
        )

# Handler for daily reports from the frontend (via HTTPController)
@coach_proto.on_message(model=UserReport, replies=CoachReply)
async def handle_user_report(ctx: Context, sender: str, msg: UserReport):
    ctx.logger.info(f"Received UserReport from {sender} (User ID: {msg.user_id}): Completed={msg.completed}, Habit='{msg.habit}', Goal_ID='{msg.goal_id}'")

    response_text = ""
    if msg.completed:
        agent_state["streak"] += 1
        response_text = f"Fantastic job! You've successfully completed your goal. Your green streak is now **{agent_state['streak']} days**! Keep up the amazing work! 🌱"
    else:
        agent_state["streak"] = 0 # Reset streak on failure
        response_text = "It's okay, not every day is perfect! The important thing is to keep trying. Let's aim for a better tomorrow. Your streak has been reset, but a new one starts now!"
    
    ctx.logger.info(f"Sending report feedback: '{response_text}'")

    # Send response back to the sender (HTTPController)
    await ctx.send(
        sender,
        CoachReply(text=response_text, streak=agent_state["streak"])
    )

# Include the defined protocol with the agent
agent.include(coach_proto)

# Optional: Fund the agent if its balance is low (primarily for testnet/mainnet deployments)
# @agent.on_event("startup")
# async def agent_startup(ctx: Context):
#     ctx.logger.info("Coach AgentOS starting up...")
#     # This line is for funding on a decentralized network, not strictly needed for local-only.
#     # if await fund_agent_if_low(ctx.wallet.address):
#     #     ctx.logger.info("Agent wallet funded.")