from fastapi import APIRouter, UploadFile
from services.db import create_vectorstore_from_pdf
from services.llm_chain import get_qa_chain

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile):
    with open(f"./docs/{file.filename}", "wb") as f:
        f.write(await file.read())
    vectordb = create_vectorstore_from_pdf(f"./docs/{file.filename}")
    return {"message": "Vector DB created!"}

@router.post("/chat")
async def chat_with_notes(question: str):
    qa_chain = get_qa_chain(vectorstore=...)  # Inject global or session vectorstore
    result = qa_chain({"question": question, "chat_history": []})
    return {"answer": result["answer"]}
