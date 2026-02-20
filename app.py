import streamlit as st
import pandas as pd
from modules.engine import StoryDirector
from modules.perception import PerceptionModule

st.cache_data.clear()
st.cache_resource.clear()

# Initialize Session State
if "director" not in st.session_state:
    st.session_state.director = StoryDirector()
    st.session_state.perceiver = PerceptionModule() 
    st.session_state.history = []
    # Track emotional history for the graph
    st.session_state.chart_data = pd.DataFrame(columns=["Turn", "Suspicion", "Guilt"])

st.title("The Anniversary: An Interactive Narrative Experiment")

# --- SIDEBAR: LIVE DEBUG DASHBOARD ---
with st.sidebar:
    st.header("📊 Emotional Metrics")
    
    # KPIs
    col1, col2 = st.columns(2)
    col1.metric("Alex Suspicion", st.session_state.director.alex.states["Suspicion"])
    col2.metric("Ben Guilt", st.session_state.director.ben.states["Guilt"])
    
    # Real-time Line Chart
    if not st.session_state.chart_data.empty:
        st.subheader("Emotional Drift")
        st.line_chart(st.session_state.chart_data.set_index("Turn"))

    if st.button("Reset Experiment"):
        st.session_state.clear()
        st.rerun()

# --- CHAT INTERFACE ---
if "narrative_started" not in st.session_state:
    st.session_state.narrative_started = False

if not st.session_state.narrative_started:
    st.subheader("The Scene")
    st.write("""
    You're at 'The Gilded Rose' restaurant. Across the room, you spot two familiar faces: 
    **Alex and Ben.** You haven't spoken since graduation. 
    
    They look... different. Alex is staring at a wine glass; Ben looks like he wants to bolt.
    As you approach the table, they both jump slightly and look up.
    """)
    if st.button("Walk up and say hi"):
        st.session_state.narrative_started = True
        st.rerun()
else:

    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.history:
            # Use avatars to make it look like a real app
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])

    progress = min(st.session_state.director.turn / 12, 1.0)
    st.progress(progress, text=f"Current Act: {st.session_state.director.current_beat}")

    if prompt := st.chat_input("Speak to Alex and Ben..."):
        # 1. SHOW USER INPUT IMMEDIATELY
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.write(prompt)
        
        # Save it to history so it persists after rerun
        st.session_state.history.append({"role": "user", "content": prompt})

        current_beat, event_text = st.session_state.director.update_beat()

        # If an event happens, show it as a special "Narrative Note"
        if event_text:
            st.session_state.history.append({"role": "event", "content": event_text})

        # 2. TRIGGER THE "THINKING" PHASE
        # This prevents the app from feeling frozen
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("Alex and Ben are reacting...", expanded=False) as status:
                # A. Perception
                intent = st.session_state.perceiver.get_intent(prompt)
                st.write(f"Perceived intent: **{intent}**")
                
                # B. Update Engine
                st.session_state.director.turn += 1
                st.session_state.director.alex.update(intent, prompt)
                st.session_state.director.ben.update(intent, prompt)
                st.write("Updating emotional states...")

                # C. Generate Responses
                # Alex's turn
                alex_reply = st.session_state.director.alex.generate_response(
                    prompt, 
                    st.session_state.perceiver.llm, 
                    current_beat,
                    intent,
                    st.session_state.history
                )

                # IMPORTANT: We add Alex's reply to history IMMEDIATELY 
                # so Ben can "hear" it before he generates his own response.
                st.session_state.history.append({"role": "assistant", "content": f"Alex: {alex_reply}"})
                
                # Ben's turn
                ben_reply = st.session_state.director.ben.generate_response(
                    prompt, 
                    st.session_state.perceiver.llm, 
                    current_beat,
                    intent,
                    st.session_state.history
                )

                st.session_state.history.append({"role": "assistant", "content": f"Ben: {ben_reply}"})

                status.update(label="Response ready!", state="complete", expanded=False)

        new_entry = pd.DataFrame([{
            "Turn": st.session_state.director.turn, 
            "Suspicion": st.session_state.director.alex.states["Suspicion"],
            "Guilt": st.session_state.director.ben.states["Guilt"]
        }])
        st.session_state.chart_data = pd.concat([st.session_state.chart_data, new_entry], ignore_index=True)

        # This forces Streamlit to clean up the UI and show the new history
        st.rerun()

# --- ENDING CHECK ---
if st.session_state.director.turn >= 12:
    ending = st.session_state.director.check_ending()
    st.success(f"**SCENE COMPLETE:** {ending}")
    if st.button("Reset Experiment"):
        st.session_state.clear()
        st.rerun()