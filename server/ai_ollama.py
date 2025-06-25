import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama

def run_ai_assistant(question):
    """
    מריץ עוזר AI על שאלה טקסטואלית ומחזיר תשובה מבוססת מסמכים בתיקייה rag_data.
    """

    # מיקום תיקיית המסמכים
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'rag_data')

    # טעינת קבצי טקסט
    documents = SimpleDirectoryReader(DATA_DIR).load_data()

    # מודל מקומי מ־Ollama
    llm = Ollama(model="deepseek-r1")

    # יצירת אינדקס עם הגדרה מפורשת של llm כדי למנוע שימוש ב-embed_model של ברירת מחדל
    index = VectorStoreIndex.from_documents(documents, service_context=None)
    query_engine = index.as_query_engine(llm=llm)

    # ביצוע השאילתה והחזרת התשובה
    response = query_engine.query(question)
    return str(response)
