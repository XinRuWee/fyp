import streamlit as st
import time

# --- CONFIGURATION ---
# (Later, we will replace this with the real LLM call)
def get_llm_response(prompt, character_name):
    # This is a FAKE LLM for testing the story flow
    time.sleep(1) # Simulate thinking
    return f"[{character_name} says something passive-aggressive about the prompt: '{prompt}']"

# --- SESSION STATE INITIALIZATION ---
# This is how Streamlit remembers data between clicks
if "turn_counter" not in st.session_state:
    st.session_state.turn_counter = 0
    st.session_state.history = [] # Stores the chat log
    # Initial Emotional State (The "Variables" for your experiment)
    st.session_state.alex_state = {"Suspicion": 0.8, "Anger": 0.2}
    st.session_state.ben_state = {"Guilt": 0.9, "Fear": 0.8}

# --- THE UI LAYOUT ---
st.title("FYP Experiment: 'The Anniversary'")
st.markdown("**Objective:** Survive the dinner. De-escalate the conflict.")

# Display the "Hidden" Debug Dashboard (For you, the developer)
with st.expander("🛠️ Developer / Debug View", expanded=True):
    col1, col2 = st.columns(2)
    col1.metric("Alex Suspicion", st.session_state.alex_state["Suspicion"])
    col2.metric("Ben Guilt", st.session_state.ben_state["Guilt"])
    st.write(f"**Current Turn:** {st.session_state.turn_counter}")

# --- THE "DIRECTOR" LOGIC (Your Story Engine) ---
def process_turn(player_input):
    st.session_state.turn_counter += 1
    current_turn = st.session_state.turn_counter
    
    # Add player move to history
    st.session_state.history.append({"role": "user", "content": player_input})

    # --- ACT 1: THE PROXY WAR ---
    if current_turn == 3:
        # BEAT 1: The Proxy Question (Hard-coded event)
        beat_context = "Alex asks the player a leading question about keeping secrets."
        
        # 1. Alex speaks first
        alex_response = "So, [Player]... do you think partners should keep secrets if it's for the 'best'?"
        st.session_state.history.append({"role": "assistant", "name": "Alex", "content": alex_response})
        
        # 2. Ben reacts (Simulated LLM)
        ben_prompt = f"React nervously to Alex asking about secrets. Your Guilt is {st.session_state.ben_state['Guilt']}."
        ben_response = get_llm_response(ben_prompt, "Ben")
        st.session_state.history.append({"role": "assistant", "name": "Ben", "content": ben_response})

    # --- ACT 2: THE ESCALATION ---
    elif current_turn == 7:
        # BEAT 2: The Phone Call
        st.session_state.history.append({"role": "system", "content": " *Ben's phone rings. Caller ID: 'Berlin Relocation Services'. Alex sees it.* "})
        
        # Alex Reacts (Simulated LLM)
        alex_prompt = f"You just saw the Berlin caller ID. Your Suspicion is {st.session_state.alex_state['Suspicion']}. React with ice-cold anger."
        alex_response = get_llm_response(alex_prompt, "Alex")
        st.session_state.history.append({"role": "assistant", "name": "Alex", "content": alex_response})

    # --- NORMAL CONVERSATION LOOP ---
    else:
        # Standard turn: Both NPCs react to the player
        # (In the full version, you'd check who the player addressed)
        
        # Alex Reacts
        alex_response = get_llm_response(f"React to: {player_input}", "Alex")
        st.session_state.history.append({"role": "assistant", "name": "Alex", "content": alex_response})
        
        # Ben Reacts
        ben_response = get_llm_response(f"React to: {player_input}", "Ben")
        st.session_state.history.append({"role": "assistant", "name": "Ben", "content": ben_response})

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    elif message["role"] == "system":
        st.info(message["content"]) # Special styling for narrative events
    else:
        with st.chat_message("assistant", avatar="😠" if message["name"]=="Alex" else "😰"):
            st.write(f"**{message['name']}:** {message['content']}")

# --- INPUT AREA ---
if prompt := st.chat_input("What do you say?"):
    process_turn(prompt)
    st.rerun() # Refresh page to show new messages