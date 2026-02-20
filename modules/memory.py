from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

class NPCMemory:
    def __init__(self, backstory_file):
        self.db = Chroma.from_documents(
            documents=load_text(backstory_file),
            embedding=OllamaEmbeddings(model="nomic-embed-text")
        )
    
    def search(self, query):
        return self.db.similarity_search(query, k=2)