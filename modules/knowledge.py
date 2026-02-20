from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import CharacterTextSplitter

class KnowledgeBase:
    def __init__(self, fact_file, collection_name):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # 1. Load the text file
        with open(fact_file, "r") as f:
            text = f.read().strip()
        
        if not text:
            # If file is empty, we create a placeholder so Chroma doesn't crash
            text = "No specific backstory available."
        
        # 2. Split text into small chunks
        text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        docs = text_splitter.create_documents([text])

        # If docs is somehow empty, Chroma will throw that '[]' error
        if len(docs) > 0:
            self.db = Chroma.from_documents(
                documents=docs, 
                embedding=self.embeddings,
                collection_name=collection_name
            )
        else:
            raise ValueError(f"Failed to split text into documents for {fact_file}")
        
        # 3. Create the Vector Store (lives in memory for now)
        self.db = Chroma.from_documents(
            documents=docs, 
            embedding=self.embeddings,
            collection_name=collection_name
        )

    def query(self, user_input):
        # Find the top 2 most relevant facts
        results = self.db.similarity_search(user_input, k=2)
        return "\n".join([doc.page_content for doc in results])