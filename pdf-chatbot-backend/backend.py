import os
import fitz  # from PyMuPDF
#print(fitz.__file__)
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from together import Together

# Load environment variables
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory FAISS vector database
vector_db = None


def generate_exam_questions(context_text, style_reference=None):
    try:
        client = Together(api_key=TOGETHER_API_KEY)

        style_instruction = (
            f" Match the style of the following example question:\n{style_reference}\n"
            if style_reference else ""
        )

        prompt = (
            f"Based on the following lecture content, generate 5 exam-style questions that test understanding of the topic."
            f"{style_instruction}\n\nLecture Notes:\n{context_text}\n\nQuestions:"
        )

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[
                {"role": "system", "content": "You are a tutor generating exam questions from lecture notes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error generating questions: {str(e)}"



# --- PDF Processing Functions ---
def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def store_pdf(file_path):
    global vector_db
    raw_text = extract_text_from_pdf(file_path)
    chunks = chunk_text(raw_text)

    # Store in FAISS DB
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = FAISS.from_texts(chunks, embeddings)
    vector_db.save_local("faiss_index")

    # Generate questions (from full text or just first chunk)
    questions = generate_exam_questions(raw_text[:2000])  # LLM token limit safety

    with open("generated_questions.txt", "w") as f:
        f.write(questions)

    return "PDF processed, stored, and exam questions generated!"


# --- Routes ---
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)

    try:
        global vector_db
        raw_text = extract_text_from_pdf(file_path)
        chunks = chunk_text(raw_text)

        # Store in FAISS vector DB
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_db = FAISS.from_texts(chunks, embeddings)
        vector_db.save_local("faiss_index")

        return jsonify({"message": "Lecture notes uploaded and indexed successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/ask', methods=['POST'])
def ask_question():
    global vector_db

    if vector_db is None:
        try:
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        except Exception:
            return jsonify({"error": "No PDF processed or saved index found!"}), 400

    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided!"}), 400

    retriever = vector_db.as_retriever()
    relevant_docs = retriever.get_relevant_documents(question)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    try:
        client = Together(api_key=TOGETHER_API_KEY)

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions from documents."},
                {"role": "user", "content": f"Answer the question based on the following context:\n\n{context}\n\nQuestion: {question}"}
            ],
            temperature=0.7,
            max_tokens=512
        )

        answer = response.choices[0].message.content
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate_questions_by_topic', methods=['POST'])
def generate_questions_by_topic():
    global vector_db

    if vector_db is None:
        try:
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        except Exception:
            return jsonify({"error": "No lecture notes processed!"}), 400

    data = request.get_json()
    topic = data.get('topic')
    sample_style = data.get('style')  # Optional

    if not topic:
        return jsonify({"error": "No topic provided!"}), 400

    retriever = vector_db.as_retriever()
    relevant_docs = retriever.get_relevant_documents(topic)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    context = context[:6000] 

    questions = generate_exam_questions(context_text=context, style_reference=sample_style)

    return jsonify({"topic": topic, "questions": questions})



# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
