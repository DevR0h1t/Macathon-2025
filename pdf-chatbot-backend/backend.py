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

from supabase import create_client, Client

from datetime import datetime

# Load environment variables
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Helper functions
def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def generate_exam_questions(context_text, style_reference=None):
    try:
        client = Together(api_key=TOGETHER_API_KEY)
        style_instruction = f" Match the style of the following example question:\n{style_reference}\n" if style_reference else ""
        prompt = f"Based on the following lecture content, generate 5 exam-style questions that test understanding of the topic.{style_instruction}\n\nLecture Notes:\n{context_text}\n\nQuestions:"

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

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "No user_id provided!"}), 400

    file = request.files['file']
    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)

    uploaded_at = datetime.utcnow().isoformat()

    try:
        global vector_db
        raw_text = extract_text_from_pdf(file_path)
        chunks = chunk_text(raw_text)

        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_db = FAISS.from_texts(chunks, embeddings)
        vector_db.save_local("faiss_index")

        # Store document metadata
        supabase.table("documents").insert({
            "user_id": int(user_id),
            "file_name": file.filename,
            "timestamp": uploaded_at
        }).execute()

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
    user_id = data.get('user_id')
    if not question:
        return jsonify({"error": "No question provided!"}), 400

    retriever = vector_db.as_retriever()
    relevant_docs = retriever.get_relevant_documents(question)
    context_from_notes = "\n\n".join([doc.page_content for doc in relevant_docs])

    try:
        # 1. Fetch all past Q&A
        past_chats_response = supabase.table("chat_history") \
            .select("question, answer") \
            .eq("user_id", user_id) \
            .execute()

        past_chats = past_chats_response.data or []

        # 2. Semantic Search: find most relevant past Q&As
        if past_chats:
            # Embed current question
            embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            current_question_embedding = embeddings_model.embed_query(question)

            # Score each past chat based on similarity
            scored_chats = []
            for chat in past_chats:
                past_question = chat['question']
                past_embedding = embeddings_model.embed_query(past_question)
                # Cosine similarity manually
                similarity = cosine_similarity(current_question_embedding, past_embedding)
                scored_chats.append((similarity, chat))

            # Sort by similarity descending
            scored_chats.sort(key=lambda x: x[0], reverse=True)

            # Top 5 most relevant
            top_chats = [chat for _, chat in scored_chats[:5]]

            # Build context
            past_context = ""
            for chat in top_chats:
                past_context += f"Q: {chat['question']}\nA: {chat['answer']}\n\n"
        else:
            past_context = ""

        # 3. Final prompt
        full_prompt = f"""
                        Use the following past conversation history and lecture notes to answer the user's question.

                        Past Conversations:
                        {past_context}

                        Lecture Notes Context:
                        {context_from_notes}

                        Now, here is the user's new question:
                        {question}
                        """

        client = Together(api_key=TOGETHER_API_KEY)

        response = client.chat.completions.create(
            model="meta-llama/Llama-3-8b-chat-hf",
            messages=[
                {"role": "system", "content": "You are a helpful tutor chatbot that uses past chats and lecture notes to answer questions."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=512
        )

        answer = response.choices[0].message.content
        answer = answer.replace("\n", " ")

        # 4. Store the new Q&A
        supabase.table("chat_history").insert({
            "user_id": int(user_id),
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cosine_similarity(vec1, vec2):
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

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
    style_hint = data.get('style')
    user_id = data.get('user_id')
    uploaded_at = datetime.utcnow().isoformat()

    if not topic or not user_id:
        return jsonify({"error": "Missing topic or user_id!"}), 400

    retriever = vector_db.as_retriever()
    relevant_docs = retriever.get_relevant_documents(topic)
    context = "".join([doc.page_content for doc in relevant_docs])[:6000]

    questions = generate_exam_questions(context_text=context, style_reference=style_hint)
    questions = questions.replace("\n", " ")

    supabase.table("generated_questions").insert({
        "user_id": str(user_id),
        "topic": topic,
        "style": style_hint or "",
        "questions": questions,
        "timestamp": uploaded_at
    }).execute()

    return jsonify({"topic": topic, "questions": questions})

if __name__ == "__main__":
    app.run(debug=True)
