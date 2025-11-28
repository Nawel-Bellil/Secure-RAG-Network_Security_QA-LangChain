from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import uvicorn
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
import tempfile
import shutil

# Initialize FastAPI
app = FastAPI(title="RAG Document Q&A System")

# Global variables
vector_store = None

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Initialize LLM
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0.7
)

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    instance_id: str
    sources_count: int

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "instance_id": INSTANCE_ID,
        "documents_loaded": vector_store is not None
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a text document to the vector store"""
    global vector_store
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Load document
        loader = TextLoader(tmp_file_path, encoding='utf-8')
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        texts = text_splitter.split_documents(documents)
        
        # Create or update vector store
        if vector_store is None:
            vector_store = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )
        else:
            vector_store.add_documents(texts)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return {
            "status": "success",
            "message": f"Document '{file.filename}' uploaded successfully",
            "chunks_created": len(texts),
            "instance_id": INSTANCE_ID
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded documents"""
    global vector_store
    
    if vector_store is None:
        raise HTTPException(
            status_code=400,
            detail="No documents uploaded yet. Please upload a document first."
        )
    
    try:
        # Search for relevant documents (manual RAG - no chains needed!)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        relevant_docs = retriever.invoke(request.question)
        
        # Build context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Create prompt manually
        prompt = f"""Answer the question based on the following context:

Context:
{context}

Question: {request.question}

Answer:"""
        
        # Get answer from LLM
        response = llm.invoke(prompt)
        
        # Extract text from response
        answer_text = response.content if hasattr(response, 'content') else str(response)
        
        return AnswerResponse(
            answer=answer_text,
            instance_id=INSTANCE_ID,
            sources_count=len(relevant_docs)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get statistics about the vector store"""
    if vector_store is None:
        return {
            "status": "No documents loaded",
            "instance_id": INSTANCE_ID
        }
    
    collection = vector_store._collection
    count = collection.count()
    
    return {
        "instance_id": INSTANCE_ID,
        "total_chunks": count,
        "status": "active"
    }

@app.delete("/clear")
async def clear_documents():
    """Clear all documents from the vector store"""
    global vector_store
    
    try:
        if vector_store is not None:
            if os.path.exists("./chroma_db"):
                shutil.rmtree("./chroma_db")
            
            vector_store = None
        
        return {
            "status": "success",
            "message": "All documents cleared",
            "instance_id": INSTANCE_ID
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)