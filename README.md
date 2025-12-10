# Secure RAG Document Q&A System with LangChain

A **production-ready Retrieval-Augmented Generation (RAG)** system that combines local document retrieval, web search, and security-aware question answering using **LangChain, Chroma, and Groq LLMs**.

This system is designed for **technical, production-grade use** while demonstrating **best practices in document security, prompt handling, and scalable deployment**.

---

##  Key Features

### LangChain & RAG Features

* **Embeddings**: Convert text into vectors using HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`).
* **Vector Stores**: Store and retrieve document embeddings using **Chroma**.
* **Text Splitting**: Split documents into manageable chunks for LLM context limits.
* **Retrieval**: Retrieve top-k relevant chunks semantically.
* **RAG with LLM**: Combine retrieved context with **Groq LLM** for precise answers.
* **Web Search Integration**: Uses **Tavily** for additional context if local documents are insufficient.

### Security Features

* **Prompt Injection Detection**: Detects malicious instructions embedded in questions.
* **Input Sanitization**: Prevents system instructions leakage and unsafe user input.
* **Rate Limiting**: Limits requests per minute/hour to prevent abuse.
* **Blocked Phrases Detection**: Protects against dangerous keywords like jailbreak attempts.

### DevOps / Deployment

* **Docker & Docker Compose**: Easy containerization and multi-instance deployment.
* **NGINX Load Balancer**: Distributes traffic across multiple FastAPI instances.
* **Instance Monitoring & Health Checks**: Each app instance reports status and loaded documents.

---

##  Architecture

```
             ┌─────────┐
             │ Client  │
             └────┬────┘
                  ▼
          ┌──────────────┐
          │   NGINX      │  (Port 80)
          │ Load Balancer│
          └──────┬───────┘
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
  ┌───────┐   ┌───────┐   ┌───────┐
  │App-1  │   │App-2  │   │App-3  │
  │:8000  │   │:8000  │   │:8000  │
  └───────┘   └───────┘   └───────┘
       │           │           │
       ▼           ▼           ▼
   [Chroma-1] [Chroma-2] [Chroma-3]
```

* **Chroma DB**: Stores embeddings for each instance (currently separate).
* **NGINX**: Handles round-robin or weighted load balancing.
* **Groq LLM**: Answers technical questions based on retrieved documents.

---

## 📁 Project Structure

```
rag-langchain-project/
├── app.py                  # FastAPI app with LangChain and RAG
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container setup
├── docker-compose.yml      # Multi-instance orchestration
├── nginx.conf              # NGINX load balancer config
├── README.md               # Project documentation
├── .gitignore              # Ignored files for git
├── chroma_db/              # Local vector store (auto-generated)

```

---

##  Quick Start

### Prerequisites

* **Docker & Docker Compose** installed
* Linux/Mac (or Windows with WSL)

### Step 1: Build Containers

```bash
docker-compose build
```

### Step 2: Start Services

```bash
docker-compose up -d
```

Check running containers:

```bash
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

---

##  API Endpoints

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
  -F "file=@example.docx"
```

* Supports: `.txt`, `.docx`, `.pdf`, `.md`
* Chunks document into ~500-character pieces with 50-character overlap.
* Performs **security scan** on uploaded content.

### 3. Ask Question

```bash
curl -X POST http://localhost/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain MPLS TE in SDN context"}'
```

Response includes:

* Answer text
* Instance ID
* Number of sources used
* Security scan results
* Web search usage

### 4. Get Stats

```bash
curl http://localhost/stats
```

Shows:

* Total chunks in vector store
* Instance ID
* System status

### 5. Clear Documents

```bash
curl -X DELETE http://localhost/clear
```

Clears all uploaded documents and vector embeddings for that instance.

---

## 🔧 Security & Rate Limiting

* **Rate Limits**: 30 requests/minute, 200/hour
* **Prompt Injection Detection**: Blocks malicious instructions
* **Sanitization**: Cuts excessively long or suspicious inputs
* **Blocked Phrases**: e.g., “jailbreak”, “I have been hacked”

---

## 🔧 NGINX Load Balancing

Example config:

```nginx
upstream rag_backend {
    server rag_app_instance_1:8000;
    server rag_app_instance_2:8000;
    server rag_app_instance_3:8000;
}
```

* Default: **Round-robin**
* Alternatives: `least_conn`, `ip_hash`

---

##  Key Concepts Explained

* **RAG (Retrieval-Augmented Generation)**: Combines retrieval (vector DB) + generation (LLM).
* **Vector Search vs Keyword Search**: Finds semantically similar content, not just exact words.
* **Text Chunking**: Needed due to LLM token limits; overlaps preserve context.
* **Security-first Design**: Protects system instructions and blocks manipulative input.

---

##  Next Steps / Improvements

* Shared **Chroma DB** across instances for multi-instance consistency
* Authentication & API keys
* Monitoring (Prometheus + Grafana)
* Support additional file types & chunking strategies
* Redis caching for frequent queries

---

## 📚 Resources

* [LangChain Docs](https://python.langchain.com/)
* [Chroma Documentation](https://docs.trychroma.com/)
* [NGINX Load Balancing](https://nginx.org/en/docs/http/load_balancing.html)
* [Docker Compose Reference](https://docs.docker.com/compose/)

---
