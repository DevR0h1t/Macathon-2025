from app.services.db import create_vectorstore_from_pdf

vectordb = create_vectorstore_from_pdf("Deloitte_Resume.pdf")
print("Vector DB created with", vectordb._collection.count(), "documents.")