import os 
import logging
from fastapi import FastAPI
import chromadb
import ollama

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

MODEL_NAME = os.getenv("MODEL_NAME", "tinyllama")
logging.info(f"Using model: {MODEL_NAME}")

app = FastAPI()
chroma = chromadb.PersistentClient(path="./db")
collection = chroma.get_or_create_collection("docs")
         #points to host computer from inside the container
ollama_client = ollama.Client(host="http://host.docker.internal:11434")

@app.post("/query")
def query(q: str):
    results = collection.query(query_texts=[q], n_results=1)
    context = results["documents"][0][0] if results["documents"] else ""

    answer = ollama_client.generate(
        model=MODEL_NAME,
        prompt=f"Context:\n{context}\n\nQuestion: {q}\n\nAnswer clearly and concisely:"

    )

    logging.info(f"/query asked: {q}")
    return {"answer": answer["response"]}


@app.post("/add")
def add_knowledge(content: str):
    """Add content to knowledge base dynamically"""
    try:
        #Generate a unique id for this document
        import uuid
        content_id = str(uuid.uuid4())

        #Add the knowledge to the Chroma collection
        collection.add(documents=[content], ids=[content_id])
        logging.info(f"/add recieved new content (id will be generated): {content_id}")

        return {
            "status": "success",
            "message": "Content added to knowledge base",
            "id": content_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/health")
def health():
    return {"status": "ok"}