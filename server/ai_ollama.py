import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

# הגדרת מודל שפה קל ויעיל מתוך Ollama
llm = Ollama(model="llama3:instruct")

# הגדרת מודל embedding מקומי שמתאים ל-RAG
embed_model = OllamaEmbedding(model_name="nomic-embed-text:latest")

# הגדרות גלובליות – יחולו אוטומטית על כל הרכיבים
Settings.llm = llm
Settings.embed_model = embed_model

def run_ai_assistant(question):
    """
    מקבלת שאלה, מחפשת מידע במסמכים שבתיקייה rag_data, ומחזירה תשובה חכמה.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'rag_data')

    # טעינת כל המסמכים מהתיקייה
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    print(f"Loaded {len(documents)} documents from: {DATA_DIR}")
    print("QUESTION:", question)
    print("TYPE:", type(question))

    # בניית אינדקס למסמכים
    index = VectorStoreIndex.from_documents(documents)
    print("Index built successfully.")
    # יצירת מנוע לשאילתות (RAG)
    query_engine = index.as_query_engine()
    print("Query engine created successfully.")
    # שליחת השאלה וקבלת תשובה
    response = query_engine.query(question)
    print("Response generated successfully.")
    return str(response)