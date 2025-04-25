from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from app.config import OPENAI_API_KEY, VECTOR_DB_PATH

def create_vectorstore_from_pdf(file_path: str):
    loader = PyPDFLoader(file_path)
    documents = loader.load_and_split()
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = Chroma.from_documents(documents, embeddings, persist_directory=VECTOR_DB_PATH)
    vectordb.persist()
    return vectordb
