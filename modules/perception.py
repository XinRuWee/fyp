from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from modules.prompts import INTENT_PROMPT

class PerceptionModule:
    def __init__(self):
        self.llm = ChatOllama(
            model="llama3", 
            temperature=0.8,  # Higher = more unique/creative, Lower = more robotic/repetitive
            repeat_penalty=1.2 # Forces the AI to avoid repeating words or phrases
        )

    def get_intent(self, user_input):
        """
        Takes user text and returns: empathy, aggression, probing, or neutral.
        """
        messages = [
            SystemMessage(content=INTENT_PROMPT),
            HumanMessage(content=user_input)
        ]
        try:
            response = self.llm.invoke(messages)
            return response.content.strip().lower()
        except Exception as e:
            print(f"Ollama Error: {e}")
            return "neutral"