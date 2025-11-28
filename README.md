# RAG Document Q&A System with LangChain

A production-ready Retrieval Augmented Generation (RAG) system demonstrating LangChain features with Docker Compose and NGINX load balancing.

## 🎯 What You'll Learn

### LangChain Concepts
1. **Embeddings**: Converting text to vectors using HuggingFace models
2. **Vector Stores**: Storing and retrieving document embeddings with Chroma
3. **Text Splitting**: Breaking documents into manageable chunks
4. **Chains**: Connecting LLM with retrieval (RetrievalQA chain)
5. **Retrievers**: Searching for relevant document chunks

### DevOps Concepts
1. **Docker**: Containerizing Python applications
2. **Docker Compose**: Multi-container orchestration
3. **NGINX Load Balancing**: Distributing traffic across instances
4. **Upstream Blocks**: Defining backend server pools

## 🏗️ Architecture

```
┌─────────┐
│  Client │
└────┬────┘
     │
     ▼
┌─────────────┐
│   NGINX     │  (Port 80)
│Load Balancer│
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │ App-1  │   │ App-2  │   │ App-3  │
   │:8000   │   │:8000   │   │:8000   │
   └────┬───┘   └────┬───┘   └────┬───┘
        │            │            │
        ▼            ▼            ▼
   [Chroma-1]   [Chroma-2]   [Chroma-3]
```

## 📁 Project Structure

```
rag-langchain-project/
├── app.py              # FastAPI application with LangChain
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Multi-container setup
├── nginx.conf          # NGINX load balancer config
├── test_api.sh         # Testing script
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Linux/Mac (for test script) or Windows with WSL

### Step 1: Setup Project

```bash
# Create project directory
mkdir rag-langchain-project
cd rag-langchain-project

# Create all files (copy the artifacts provided)
# - app.py
# - requirements.txt
# - Dockerfile
# - docker-compose.yml
# - nginx.conf
```

### Step 2: Build and Run

```bash
# Build the Docker images
docker-compose build

# Start all services (3 app instances + NGINX)
docker-compose up -d

# Check if all containers are running
docker-compose ps
```

Expected output:
```
NAME                    STATUS    PORTS
nginx_load_balancer     Up        0.0.0.0:80->80/tcp
rag_app_instance_1      Up        0.0.0.0:8001->8000/tcp
rag_app_instance_2      Up        0.0.0.0:8002->8000/tcp
rag_app_instance_3      Up        0.0.0.0:8003->8000/tcp
```

### Step 3: Test the System

```bash
# Make test script executable
chmod +x test_api.sh

# Run tests
./test_api.sh
```

## 🔍 How It Works

### 1. Document Upload Flow

```
User uploads TXT file
    ↓
FastAPI receives file
    ↓
LangChain TextLoader reads content
    ↓
RecursiveCharacterTextSplitter breaks into chunks (500 chars)
    ↓
HuggingFace embeddings convert chunks to vectors
    ↓
Chroma stores vectors in database
```

**Code walkthrough:**
```python
# Load document
loader = TextLoader(file_path)
documents = loader.load()

# Split into chunks - why? LLMs have token limits!
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Each chunk ~500 characters
    chunk_overlap=50     # 50 char overlap for context continuity
)
texts = text_splitter.split_documents(documents)

# Create embeddings and store
vector_store = Chroma.from_documents(
    documents=texts,
    embedding=embeddings  # Converts text → numbers
)
```

### 2. Question Answering Flow

```
User asks question
    ↓
NGINX routes to available instance (round-robin)
    ↓
Question converted to embedding vector
    ↓
Chroma finds top 3 most similar chunks (k=3)
    ↓
Relevant chunks + question sent to Groq LLM
    ↓
LLM generates answer based on context
    ↓
Response returned with instance_id
```

**Code walkthrough:**
```python
# Create QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,                    # Groq LLM
    chain_type="stuff",         # "stuff" = insert all context into prompt
    retriever=vector_store.as_retriever(
        search_kwargs={"k": 3}  # Return top 3 matches
    ),
    return_source_documents=True
)

# Query the chain
result = qa_chain.invoke({"query": question})
```

### 3. NGINX Load Balancing

```nginx
upstream rag_backend {
    server app1:8000 weight=1;  # Equal weight = round-robin
    server app2:8000 weight=1;
    server app3:8000 weight=1;
}
```

**Load balancing methods:**
- **Round-robin** (default): Requests distributed evenly
- **least_conn**: Routes to instance with fewest connections
- **ip_hash**: Same client always goes to same instance

## 📡 API Endpoints

### 1. Health Check
```bash
curl http://localhost/
```

Response:
```json
{
  "status": "healthy",
  "instance_id": "instance-1",
  "documents_loaded": true
}
```

### 2. Upload Document
```bash
curl -X POST http://localhost/upload \
  -F "file=@document.txt"
```

### 3. Ask Question
```bash
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

### 4. Get Stats
```bash
curl http://localhost/stats
```

### 5. Clear Documents
```bash
curl -X DELETE http://localhost/clear
```

## 🔧 Testing Load Balancing

### Test 1: Watch Instance Rotation
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -s http://localhost/ | jq '.instance_id'
done
```

Output should rotate: instance-1 → instance-2 → instance-3 → instance-1 ...

### Test 2: Direct Instance Access
```bash
# Bypass NGINX, test individual instances
curl http://localhost:8001/  # Instance 1
curl http://localhost:8002/  # Instance 2
curl http://localhost:8003/  # Instance 3
```

## 🐛 Troubleshooting

### Check logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs app1
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f
```

### Restart services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app1
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🎓 Key Concepts Explained

### Why RAG?
- LLMs have knowledge cutoffs and can hallucinate
- RAG grounds responses in your actual documents
- Combines retrieval (search) + generation (LLM)

### Why Vector Databases?
- Traditional search: exact keyword matching
- Vector search: semantic similarity
- "ML algorithms" and "machine learning methods" = similar vectors

### Why Text Splitting?
- LLMs have context window limits (tokens)
- Smaller chunks = more precise retrieval
- Overlap preserves context between chunks

### Why Load Balancing?
- Distributes traffic across instances
- Improves reliability (if one fails, others handle requests)
- Scales horizontally (add more instances easily)

## 🚀 Next Steps & Improvements

1. **Add Persistence**: Share Chroma DB across instances (use volume mount)
2. **Add Authentication**: Secure endpoints with API keys
3. **Add Monitoring**: Prometheus + Grafana for metrics
4. **PDF Support**: Add PDF document loading
5. **Better Chunking**: Experiment with different chunk sizes
6. **Caching**: Add Redis for frequent queries
7. **Health Checks**: Implement proper health endpoints in NGINX

## 📚 Resources

- [LangChain Docs](https://python.langchain.com/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [NGINX Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## 🤝 Contributing

This is a learning project! Experiment, break things, and learn.

## 📝 Notes

- Each instance has its own Chroma database (separate volumes)
- Upload to one instance doesn't sync to others (by design for learning)
- In production, you'd use a shared database or sync mechanism
- Groq API key is embedded (replace with environment variable in production)