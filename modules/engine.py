from modules.knowledge import KnowledgeBase 
from modules.prompts import ALEX_PROFILE, BEN_PROFILE, SHARED_CONTEXT

import csv
from datetime import datetime

class NPC:
    def __init__(self, name, states, profile, knowledge_file):
        self.name = name
        self.states = states
        self.profile = profile
        self.kb = KnowledgeBase(knowledge_file, f"{name}_lore")
        self.memory = []

    def update(self, intent, player_text):
        """
        The NPC assesses the player's intent and updates their internal 
        metrics based on their specific personality.
        """
        # Alex is sensitive to 'Probing' (it raises suspicion)
        if self.name == "Alex":
            if intent == "probing":
                self.states["Suspicion"] = min(1.0, self.states["Suspicion"] + 0.15)
            elif intent == "empathy":
                self.states["Suspicion"] = max(0.0, self.states["Suspicion"] - 0.05)
                
        # Ben is sensitive to 'Aggression' (it raises guilt/anxiety)
        if self.name == "Ben":
            if intent == "aggression":
                self.states["Guilt"] = min(1.0, self.states["Guilt"] + 0.2)
            elif intent == "empathy":
                self.states["Guilt"] = max(0.0, self.states["Guilt"] - 0.1)

        # Standard intent-based update
        factor = 0.1 if intent in ["aggression", "probing"] else -0.05
        
        # NEW: Keyword-based assessment (High-level Social Reasoning)
        # If the user mentions "Berlin" or "Work", the tension spikes instantly!
        if "berlin" in player_text.lower() or "work" in player_text.lower():
            if self.name == "Ben":
                self.states["Guilt"] = min(1.0, self.states["Guilt"] + 0.2)
            if self.name == "Alex":
                self.states["Suspicion"] = min(1.0, self.states["Suspicion"] + 0.2)

        # Keep values rounded for the UI
        self.states = {k: round(v, 2) for k, v in self.states.items()}
        
        # Clamp values
        self.states = {k: round(max(0, min(1, v)), 2) for k, v in self.states.items()}

    def generate_response(self, user_input, llm, current_beat, perceived_intent, full_history):
        # 1. RAG retrieval (The 'Knowledge' part)
        relevant_lore = self.kb.query(user_input)

        formatted_history = []

        for msg in full_history[-6:]:
            if msg["role"] == "user":
                # Label the player clearly
                formatted_history.append(f"OLD FRIEND (The Player): {msg['content']}")
            else:
                # The assistant messages already start with "Alex:" or "Ben:" 
                # because of how we appended them in app.py
                formatted_history.append(msg["content"])

        history_str = "\n".join(formatted_history)

        beat_instructions = {
            "The Forced Smile": "Stay polite. Deflect with nostalgia.",
            "The Crack": "Losing patience. Be passive-aggressive.",
            "The Confrontation": "The truth is coming out. Be emotional."
        }

        # 2. Assessment Logic (The 'Reasoning' part)
        assessment = ""
        if perceived_intent == "probing":
            assessment = f"You feel like the player is digging for secrets. You are on the defensive."
        elif perceived_intent == "empathy":
            assessment = f"The player is being kind. You feel a flicker of the old high school bond."

        perspective = ""
        if self.name == "Alex":
            perspective = "If the player mentions Berlin or a Law Firm, you are suspicious and demanding. You want answers."
        else:
            perspective = "If the player mentions Berlin or a Law Firm, you are terrified. You must lie, deflect, or change the subject immediately."

        system_prompt = f"""
        ### YOUR IDENTITY ###
        You are {self.name}. 
        {self.profile}

        ### THE ROOM ###
        Current Tension: {self.states}
        Narrative Act: {current_beat}

        ### RECENT DIALOGUE ###
        {history_str}

        ### THE SETTING ###
        You are {self.name}. You are sitting at a dinner table.
        The person speaking to you is an OLD FRIEND from high school.
        The other person at the table is your spouse.

        ### YOUR PERSPECTIVE ON THE SECRET ###
        {perspective}   

        ### DRAMATIC CONSTRAINTS ###
        1. SUBTEXT: Never say exactly how you feel. Use passive-aggression.
        2. DISCOMFORT: If the 'old friend' asks a personal question, deflect it.
        3. FRICTION: You and your spouse are NOT on the same page. If they say 'everything is fine', you should roll your eyes or sigh.
        4. LORE: {relevant_lore} (Use this as a weapon or a shield).
                
        ### RESPONSE STYLE ###
        - Max 2 sentences.
        - Use stage directions for comedy.
        - For Alex (Claire): *narrows eyes*, *takes a massive gulp of wine*, *forced smile*.
        - For Ben (Phil): *accidentally drops a fork*, *starts sweating*, *looks directly at an imaginary camera*.

        SITUATION ASSESSMENT: {assessment}
        GOAL: {beat_instructions[current_beat]}
        PLAYER INTENT: {perceived_intent}
        RELEVANT LORE: {relevant_lore}

        ### YOUR MANDATE ###
        - You are NOT the other NPC. 
        - If the player is talking to the other person, just give a short reaction (e.g. *scoffs* or "Is that so?").
        - Use your unique voice. 
        - Do NOT repeat what your spouse said.
        - Do NOT use the same phrasing as the conversation history.
        - You are a separate human being with your own thoughts.
        - If you are {self.name}, your secret is {self.kb.query(user_input)}.

        TASK:
        1. Read the history. If the player or the other NPC just said something that concerns you, you MUST respond.
        2. If you aren't being addressed and have nothing to add, keep it very short (e.g., a nod or a sigh).
        3. If you ARE addressed or your secret is at risk, defend yourself.
        4. React to what the OTHER NPC just said if it was suspicious.
        5. Do NOT say 'I got a call from a law firm' unless your name is Ben.
        6. - If you are Alex, ask Ben: 'What is they talking about, Ben?
        """
            
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        
        return llm.invoke(messages).content
    
class StoryDirector:
    def __init__(self):
        self.turn = 0
        self.current_beat = "The Forced Smile"
        self.alex = NPC(
            "Alex", 
            {"Suspicion": 0.8, "Anger": 0.2}, 
            ALEX_PROFILE,
            knowledge_file="data/alex_lore.txt"
        )
        self.ben = NPC(
            "Ben", 
            {"Guilt": 0.7, "Anxiety": 0.4}, 
            BEN_PROFILE,
            knowledge_file="data/ben_lore.txt"
        )

    def update_beat(self):
        event_text = None
    
        if self.turn <= 3:
            self.current_beat = "The Forced Smile"
        elif 4 <= self.turn <= 8:
            self.current_beat = "The Crack"
            # Let's trigger our 'Smoking Gun' event on Turn 5
            if self.turn == 5:
                event_text = "Ben's phone buzzes on the table. Alex squints at the notification from a 'Berlin Law Firm'."
        else:
            self.current_beat = "The Confrontation"
            if self.turn == 9:
                event_text = "The restaurant music fades. The silence at the table is deafening."

        # CRITICAL: Always return TWO values
        return self.current_beat, event_text

    def get_context(self):
        return f"Alex State: {self.alex.states}, Ben State: {self.ben.states}"

    def check_ending(self):
            """
            Calculates the ending based on final emotional variables.
            This is your quantitative result!
            """
            # Logic: If tension is low, you get the 'Calm' ending.
            # If Alex is highly suspicious but Ben is low fear, 'Upset Confession'.
            # If both are high, 'Stalemate'.
            
            suspicion = self.alex.states["Suspicion"]
            guilt = self.ben.states["Guilt"]

            if suspicion > 0.8 and guilt > 0.8:
                return "THE EXPLOSION: Alex confronts Ben about the 'Berlin Law Firm' right at the table. The secrets are out, and the marriage is likely over. You stand there, holding your wine glass, as they both storm out."
            
            elif suspicion > 0.7 and guilt < 0.4:
                return "THE COLD WAR: Alex is certain Ben is lying, but Ben plays it cool. They leave together in a terrifying silence. You get the feeling you'll never see them as a couple again."
            
            elif suspicion < 0.4 and guilt < 0.4:
                return "THE MASK HEDS: Against all odds, you managed to keep things nostalgic and light. They leave holding hands, though you wonder how long that peace will last."
                
            else:
                return "THE UNSETTLED TRUCE: The dinner ends awkwardly. Nothing was settled, but nothing was destroyed. They thank you for coming, but their eyes tell a story of deep exhaustion."

    def log_experiment_data(self, player_input, intent, ending="In Progress"):
        """
        Saves every turn to a CSV file. 
        This is your 'Quantitative Data' for the FYP.
        """
        file_path = "experiment_logs.csv"
        file_exists = os.path.isfile(file_path)
        
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Add headers if it's a new file
            if not file_exists:
                writer.writerow(["Timestamp", "Turn", "Player_Input", "Perceived_Intent", "Alex_Suspicion", "Ben_Guilt", "Ending"])
            
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.turn,
                player_input,
                intent,
                self.alex.states["Suspicion"],
                self.ben.states["Guilt"],
                ending
            ])