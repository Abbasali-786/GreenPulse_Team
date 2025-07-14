import streamlit as st
import requests
import json

# --- Configuration & Setup ---
st.set_page_config(page_title="Sustainability Coach", page_icon="🌱", layout="wide")

# Custom CSS for styling and background image
st.markdown(
    """
    <style>
    /* Background Image */
    .stApp {
        background-image: url("https://i.pinimg.com/736x/62/0d/1e/620d1e45864bec4a2bf0a79dd001696d.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Main content area background (slightly transparent for readability) */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.1); /* Very light white/shady transparency */
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    /* Heading Color */
    h1, h2, h3, .stMarkdown strong {
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5); /* Adds a slight shadow for readability */
    }

    /* Text Colors (for general markdown and inputs) */
    .stMarkdown, .stTextInput label, .stSelectbox label, .stButton {
        color: white !important;
    }

    /* Chat messages styling */
    .stMarkdown {
        word-wrap: break-word;
    }
    .user-message {
        background-color: rgba(224, 247, 250, 0.8); /* Light cyan for user messages with transparency */
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 8px;
        text-align: right;
        margin-left: auto;
        max-width: 80%;
        color: black; /* Ensure text is visible */
    }
    .coach-message {
        background-color: rgba(220, 237, 200, 0.8); /* Light green for coach messages with transparency */
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 8px;
        text-align: left;
        max-width: 80%;
        color: black; /* Ensure text is visible */
    }
    .system-message {
        background-color: rgba(255, 249, 196, 0.8); /* Light yellow for system messages with transparency */
        padding: 8px 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-style: italic;
        font-size: 0.9em;
        color: black; /* Ensure text is visible */
    }
    /* Note: .error-message CSS is kept but the code will no longer append this type to chat_messages */
    .error-message {
        background-color: rgba(255, 205, 210, 0.8); /* Light red for error messages with transparency */
        padding: 8px 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-weight: bold;
        color: black; /* Ensure text is visible */
    }
    .stInfo { /* For st.info messages like streak */
        background-color: rgba(0, 150, 136, 0.3); /* Teal with transparency */
        color: white !important;
    }
    .stSuccess { /* For st.success messages */
        background-color: rgba(76, 175, 80, 0.3); /* Green with transparency */
        color: white !important;
    }
    .stWarning { /* For st.warning messages */
        background-color: rgba(255, 152, 0, 0.3); /* Orange with transparency */
        color: white !important;
    }


    /* Input and button styling */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 1px solid #4CAF50;
        padding: 10px;
        background-color: rgba(255, 255, 205, 0.7); /* Light yellow for text input with transparency */
        color: black; /* Ensure input text is visible */
    }
    .stButton>button {
        background-color: #4CAF50; /* Green */
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stSelectbox>div>div {
        border-radius: 10px;
        border: 1px solid #4CAF50;
        background-color: rgba(255, 255, 205, 0.7); /* Light yellow for selectbox with transparency */
        color: black; /* Ensure text is visible */
    }
    .stSelectbox>div>div>div {
        padding: 5px;
    }
    /* Style for the form container itself (the "prompt" area) */
    .stForm {
        background-color: rgba(255, 255, 205, 0.2); /* Very light yellow with more transparency */
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌿 Sustainability Coach AI")

# --- Session State Management ---
if "goal" not in st.session_state:
    st.session_state["goal"] = ""
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [("coach", "Hello! I'm your Sustainability Coach. Tell me one habit you'd like to improve.")]
if "current_habit_tracked" not in st.session_state:
    st.session_state["current_habit_tracked"] = ""
if "current_streak" not in st.session_state:
    st.session_state["current_streak"] = 0

# --- Agent Configuration ---
COACH_AGENT_ADDRESS = "agent1qdqyks7u4uxlwcutsk5fgfhs2p432dcp4v2cvwqe0l5n234k7pvm7u0q0qf"
AGENT_URL = "http://localhost:3000/submit"

# --- Display Chat Messages ---
chat_container = st.container(height=250, border=True) # Reduced height
with chat_container:
    for msg_type, msg_content in st.session_state.chat_messages:
        # Only display messages that are not of type 'error'
        if msg_type == "user":
            st.markdown(f'<div class="user-message">**You:** {msg_content}</div>', unsafe_allow_html=True)
        elif msg_type == "coach":
            st.markdown(f'<div class="coach-message">**Coach:** {msg_content}</div>', unsafe_allow_html=True)
        elif msg_type == "system":
            st.markdown(f'<div class="system-message">*{msg_content}*</div>', unsafe_allow_html=True)

# --- User Input Forms & Suggestions ---
st.subheader("👋 Start by telling me one habit you'd like to improve")

with st.form("habit_form"):
    habit_input_key = "habit_input_text"
    
    initial_habit_value = st.session_state.get(habit_input_key, "")
    
    if "suggested_habit_select" in st.session_state and st.session_state["suggested_habit_select"] != "":
        if st.session_state[habit_input_key] != st.session_state["suggested_habit_select"]:
            initial_habit_value = st.session_state["suggested_habit_select"]
            st.session_state["suggested_habit_select"] = "" 

    habit = st.text_input("Enter your current habit (e.g., I usually drive to school)", 
                          value=initial_habit_value, key=habit_input_key)

    st.markdown("👇 Or pick a habit from suggestions:")
    suggested = st.selectbox("Choose an example habit", [
        "",
        "I drive to nearby places",
        "I use plastic bags regularly",
        "I leave lights on unnecessarily",
        "I buy bottled water daily",
        "I take long showers"
    ], key="suggested_habit_select")

    submitted_habit = st.form_submit_button("🎯 Get Today's Goal")

    if submitted_habit:
        if not habit:
            st.session_state.chat_messages.append(("system", "Please enter or select a habit first."))
            st.rerun()
        else:
            st.session_state.chat_messages.append(("user", f"My habit: {habit}"))
            st.session_state.chat_messages.append(("system", "Sending request to AI Coach..."))
            st.session_state["current_habit_tracked"] = habit
            
            # --- DIRECT PROMPT FEATURES ---
            lower_habit = habit.lower().strip()
            direct_response_text = ""

            if lower_habit == "tell me a green fact":
                direct_response_text = "Did you know that recycling one aluminum can saves enough energy to power a TV for three hours? Every little bit helps! 🌱"
            elif lower_habit == "what can i recycle today?":
                direct_response_text = "For today, focus on recycling all clean paper, cardboard, plastic bottles (with caps), and aluminum cans. Check local guidelines for more specifics! ♻️"
            elif lower_habit == "eco tip":
                direct_response_text = "Here's a quick eco tip: Unplug electronics when not in use. They can still draw 'phantom' power even when turned off! 💡"
            elif lower_habit == "why is climate change bad?":
                direct_response_text = "Climate change is leading to more extreme weather, rising sea levels, and impacts on ecosystems, threatening human health and natural habitats globally. 🌍"
            elif lower_habit == "inspire me":
                direct_response_text = "Remember, every small action you take for sustainability creates a ripple effect. Your effort matters, and together, we can build a greener future! ✨"
            # --- END OF DIRECT PROMPT FEATURES ---

            if direct_response_text: # If a direct prompt was matched
                st.session_state["goal"] = direct_response_text
                st.session_state.chat_messages.append(("coach", direct_response_text))
                st.rerun() 
            else: # If it's not a direct prompt, proceed with backend call
                try:
                    payload = {
                        "to": COACH_AGENT_ADDRESS,
                        "body": {
                            "type": "HabitInput", # This must match the class name in schemas.py
                            "user_id": "user123", 
                            "habit": habit 
                        }
                    }
                    
                    response = requests.post(AGENT_URL, json=payload)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if "text" in data:
                                st.session_state["goal"] = data["text"]
                                st.session_state["current_streak"] = data.get("streak", 0)
                                st.session_state.chat_messages.append(("coach", data["text"]))
                            else:
                                print(f"DEBUG: Unexpected agent response format. Data: {data}")
                            
                        except json.JSONDecodeError:
                            print(f"DEBUG: Backend returned non-JSON response for goal: {response.text}")
                        except KeyError as ke:
                            print(f"DEBUG: Agent response missing expected key: {ke}, Full response: {response.text}")
                    else:
                        print(f"DEBUG: Failed to get a response from AI Coach. Status: {response.status_code}, Response: {response.text}")
                except requests.exceptions.ConnectionError:
                    print("DEBUG: Could not connect to the backend AgentOS. Is it running?")
                except Exception as e:
                    print(f"DEBUG: An unexpected error occurred: {e}")
                st.rerun()

# --- Goal Completion and Reporting ---
if st.session_state.goal:
    st.divider()
    st.markdown(f"<p style='color:white;'>📌 <strong>Your Micro-Goal:</strong> {st.session_state.goal}</p>", unsafe_allow_html=True)
    if st.session_state.current_streak > 0:
        st.info(f"🔥 Current Green Streak: **{st.session_state.current_streak} days**!")

    col1, col2 = st.columns(2)
    with col1:
        # Reverted to standard Streamlit button
        if st.button("✅ Yes, I completed it!"):
            st.session_state.chat_messages.append(("user", f"Yes, I completed my goal: {st.session_state.goal}"))
            st.session_state.chat_messages.append(("system", "Reporting completion to AI Coach..."))
            try:
                payload = {
                    "to": COACH_AGENT_ADDRESS,
                    "body": {
                        "type": "UserReport", 
                        "user_id": "user123", 
                        "completed": True, 
                        "habit": st.session_state["current_habit_tracked"],
                        "goal_id": st.session_state["goal"] 
                    }
                }
                response = requests.post(AGENT_URL, json=payload)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        st.session_state.current_streak = data.get("streak", 0)
                        st.balloons()
                        # Python logic for success message (replaces JS alert)
                        st.success(data.get("text", f"🎉 YOHOO! You are on a great streak of Day {st.session_state.current_streak}! Keep going!"))
                        st.session_state.chat_messages.append(("coach", data.get("text", "Great job! Progress logged.")))
                        if st.session_state.current_streak > 0:
                            st.session_state.chat_messages.append(("system", f"🔥 You're on a **{st.session_state.current_streak}-day green streak**!"))
                    except json.JSONDecodeError:
                        print(f"DEBUG: Backend returned non-JSON on completion: {response.text}")
                    except KeyError as ke:
                        print(f"DEBUG: Agent response missing key on completion: {ke}, Full response: {response.text}")
                else:
                    print(f"DEBUG: Couldn't log progress. Status: {response.status_code}, Response: {response.text}")
            except requests.exceptions.ConnectionError:
                print("DEBUG: Could not connect to the backend AgentOS for completion report.")
            except Exception as e:
                print(f"DEBUG: An unexpected error occurred on completion: {e}")
            st.rerun()

    with col2:
        # Reverted to standard Streamlit button
        if st.button("❌ No, I missed it"):
            st.session_state.chat_messages.append(("user", f"No, I missed my goal: {st.session_state.goal}"))
            st.session_state.chat_messages.append(("system", "Reporting miss to AI Coach..."))
            try:
                payload = {
                    "to": COACH_AGENT_ADDRESS,
                    "body": {
                        "type": "UserReport", 
                        "user_id": "user123", 
                        "completed": False, 
                        "habit": st.session_state["current_habit_tracked"],
                        "goal_id": st.session_state["goal"] 
                    }
                }
                response = requests.post(AGENT_URL, json=payload)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        st.session_state.current_streak = data.get("streak", 0)
                        # Python logic for warning message (replaces JS alert)
                        st.warning(data.get("text", 'Keep your head up! "Success is not final, failure is not fatal: it is the courage to continue that counts."'))
                        st.session_state.chat_messages.append(("coach", data.get("text", "It's okay, keep trying!")))
                        if st.session_state.current_streak > 0:
                            st.session_state.chat_messages.append(("system", f"🔥 You're on a **{st.session_state.current_streak}-day green streak**!"))
                    except json.JSONDecodeError:
                        print(f"DEBUG: Backend returned non-JSON on miss: {response.text}")
                    except KeyError as ke:
                        print(f"DEBUG: Agent response missing key on miss: {ke}, Full response: {response.text}")
                else:
                    print(f"DEBUG: Couldn't log progress. Status: {response.status_code}, Response: {response.text}")
            except requests.exceptions.ConnectionError:
                print("DEBUG: Could not connect to the backend AgentOS for miss report.")
            except Exception as e:
                print(f"DEBUG: An unexpected error occurred on miss: {e}")
            st.rerun()