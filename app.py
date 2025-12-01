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

# ---- INTERNET SEARCH TOOL ----
from langchain.tools.tavily_search import TavilySearchResults


# ============================================
# FASTAPI INIT
# ============================================
app = FastAPI(title="RAG Document Q&A System")

# Global variables
vector_store = None

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

# Purpose: Identify which Docker container handled the request
#Why: Helps see load balancing in action
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")

# Initialize embeddings
# Using a lightweight model for embeddings 
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)


# Initialize LLM
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    tavily_api_key=TAVILY_API_KEY,
    temperature=0.3
)
# ============================================
# Internet Search
# ============================================

tavily = TavilySearchResults(
    max_results=5,
    api_key=os.getenv("TAVILY_API_KEY", "")
)


# Purpose: Define the shape of incoming JSON
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    instance_id: str
    sources_count: int
# ============================================
# ROOT
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "instance_id": INSTANCE_ID,
        "documents_loaded": vector_store is not None
    }
# ============================================
# DOCUMENT UPLOAD
# ============================================

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
# ============================================
# ASK HYBRID RAG
# ============================================

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
        # 1️⃣ ---- Local Retrieval ----
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        retrieved_docs = retriever.invoke(request.question)
        
        # Build context from retrieved documents
        local_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        sources_count = len(retrieved_docs)
        

        # decide if we need internet search
        web_used = False

        if len(local_context.strip()) < 50:
            web_used = True
            # 2️⃣ ---- Internet Search ----
            web_results = tavily.run(request.question)
            web_context = "\n\n".join([r["content"] for r in web_results])
            web_used = True   
        else:
            wweb_results = tavily.run(request.question)
            web_context = "\n\n".join([r["content"] for r in web_results])
            web_used = True   
        # Combine contexts ( merge local and web)
        full_context = f"""
Local Documents Context:
{local_context}
Web Search Context:
{web_context}
        """
        
             # Create prompt manually
        prompt = f"""
You are a hybrid intelligence agent combining:
- Local RAG documents
- Internet real-time search
- Expert-level explanations

Your mission:
1. Answer the question accurately.
2. Merge local content + online sources.
3. Provide:
   - simple explanation
   - technical explanation
   - step-by-step execution plan
   - CLI commands (if relevant)
   - troubleshooting tips
   - verification steps

Question: {request.question}

Context:
{full_context}

Provide a structured final answer.
"""

        
        # Get answer from LLM
        response = llm.invoke(prompt)
        answer_text = response.content 
        
        return AnswerResponse(
            answer=answer_text,
            instance_id=INSTANCE_ID,
            sources_count=sources_count,
            web_used=web_used
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
# ============================================
# STATS
# ============================================
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
# ============================================
# CLEAR
# ============================================
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

# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)