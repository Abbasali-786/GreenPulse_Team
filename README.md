AI-powered Sustainability Coach
Your friendly AI guide for greener habits

Description
- Problem: Sustainability education is fragmented, complex, and often inaccessible.
- Vision: Make sustainable living feel as easy as texting a friend.
- Mission: Help millions take small, daily steps that add up to real climate impact.
- Core belief: Personalized micro-habits can drive macro change.

Getting Started
Dependencies
Using agentOS protocol and Gemini model for optimization. Has 3 agents - 
Master, Coach and Habit Tracking 
Installing

How/where to download your program

Any modifications needed to be made to files/folders

Executing program :

## Program Execution

Your program runs in two distinct, yet interconnected, parts: a **backend AgentOS service** and a **frontend Streamlit application**.

***

### 1. Backend AgentOS Service

* **Role**: This is the core "brain" of your AI coach. It handles all the AI logic, including interactions with the **Gemini model** and managing the user's habit tracking and streak.
* **Execution**: You start it by running `uvicorn main:app --reload --port 3000` from your project's root directory.
* **Functionality**:
    * It operates as a **FastAPI** application, listening for requests from the frontend on `http://localhost:3000`.
    * When it receives a user's habit input (from the frontend), it processes this information.
    * It then uses your configured Gemini model (via your **API key**) to generate an appropriate response.
    * It updates the user's **streak** based on reported progress.
    * Finally, it sends the AI coach's reply and the updated streak information back to the frontend.

***

### 2. Frontend Streamlit Application

* **Role**: This is the **user interface (UI)**. It's what the user sees and interacts with to communicate with the AI coach.
* **Execution**: You launch it by running `streamlit run app.py` from your `frontend` directory. This typically opens the application in your web browser.
* **Functionality**:
    * It displays the **chat history** and the user's current micro-goal and streak.
    * It provides an input field for users to enter their habits.
    * For specific **direct commands** (e.g., "tell me a green fact"), it provides a pre-defined, instant response without contacting the backend.
    * For all other habit inputs, it **sends a request** to your running **AgentOS backend**.
    * Upon receiving a response from the backend, it **renders the AI coach's reply** and any updated streak information in the UI.
    * It allows users to report goal completion ("Yes, I completed it!") or failure ("No, I missed it"), sending this information back to the backend to update the streak.

How to run the program
Step-by-step bullets
code blocks for commands
Help
Any advise for common problems or issues.

command to run if program contains helper info


Authors
Contributors names and contact info

Syed Zain, Ghulam Abbas, Wasim
