# 🌐 Networking Concepts Quick Reference
## For Advanced Networks Course - Secure RAG Project

---

## 1. Reverse Proxy vs Forward Proxy

### Reverse Proxy (What We Use)
```
Client → NGINX → Backend Servers
         (hides backend)
```

**Purpose:** 
- Load balancing
- SSL termination
- Caching
- Security (hide backend IPs)

**Our Implementation:**
```nginx
# NGINX acts as reverse proxy
upstream rag_backend {
    server instance_1:8000;
    server instance_2:8000;
    server instance_3:8000;
}
```
 
 
### Forward Proxy
```
Client → Proxy → Internet
         (hides client)
```

**Purpose:**
- Anonymity
- Content filtering
- Caching
- Bypass geo-restrictions

---

## 2. Load Balancing Algorithms

### Round-Robin (Our Default)
```
Request 1 → Instance 1
Request 2 → Instance 2
Request 3 → Instance 3
Request 4 → Instance 1 (repeats)
```

**Pros:** Simple, fair distribution  
**Cons:** Doesn't consider server load

### Least Connections
```nginx
upstream rag_backend {
    least_conn;
    server instance_1:8000;
    server instance_2:8000;
}
```

Routes to server with fewest active connections.

**Pros:** Better for long-lived connections  
**Cons:** More complex to manage

### IP Hash (Sticky Sessions)
```nginx
upstream rag_backend {
    ip_hash;
    server instance_1:8000;
    server instance_2:8000;
}
```

Same client IP always goes to same server.

**Pros:** Maintains session state  
**Cons:** Uneven distribution possible

### Weighted
```nginx
upstream rag_backend {
    server instance_1:8000 weight=5;
    server instance_2:8000 weight=3;
    server instance_3:8000 weight=1;
}
```

Distributes based on server capacity.

**Pros:** Handles heterogeneous servers  
**Cons:** Manual weight configuration

---

## 3. OSI Model - Where This Project Operates

```
┌────────────────────────────────────────────┐
│ Layer 7 - Application │ HTTP, FastAPI, REST│ ← Our app logic
├────────────────────────────────────────────┤
│ Layer 6 - Presentation│ JSON encoding      │
├────────────────────────────────────────────┤
│ Layer 5 - Session     │ TCP connections    │
├────────────────────────────────────────────┤
│ Layer 4 - Transport   │ TCP (port 8080)    │ ← Load balancing
├────────────────────────────────────────────┤
│ Layer 3 - Network     │ IP routing         │ ← Docker network
├────────────────────────────────────────────┤
│ Layer 2 - Data Link   │ Ethernet           │
├────────────────────────────────────────────┤
│ Layer 1 - Physical    │ Network cables     │
└────────────────────────────────────────────┘
```

**NGINX operates at Layer 7** - makes routing decisions based on HTTP content.

---

## 4. Quality of Service (QoS)

### What is QoS?
Prioritizing certain types of network traffic to ensure performance.

### Our QoS Implementation

#### 1. Traffic Shaping
```
Load balancer distributes requests evenly → no single server overloaded
```

#### 2. Connection Limits
```python
MAX_REQUESTS_PER_MINUTE = 30  # Per client
MAX_REQUESTS_PER_HOUR = 200
```

#### 3. Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 5s
  retries: 5
```

Unhealthy instances removed from pool → maintains service quality.

### QoS Mechanisms

| Mechanism | Purpose | Implementation |
|-----------|---------|----------------|
| Traffic Policing | Drop excess packets | Rate limiting |
| Traffic Shaping | Delay excess packets | Request queuing |
| Priority Queuing | Serve important traffic first | Endpoint-based routing |
| Resource Reservation | Guarantee bandwidth | Container CPU/memory limits |

---

## 5. SDN (Software-Defined Networking) Principles

### Traditional Networking
```
Switch/Router contains:
  - Control Plane (routing decisions)
  - Data Plane (packet forwarding)
  - Hardware-dependent
```

### SDN Approach
```
┌─────────────────────┐
│  Controller (Brain) │ ← Control Plane
│  (Docker Compose)   │
└──────────┬──────────┘
           │ API
    ┌──────┴──────┬──────────┐
    ▼             ▼          ▼
[Switch 1]   [Switch 2]  [Switch 3] ← Data Plane
(Instance 1) (Instance 2) (Instance 3)
```

### Our SDN Characteristics

#### 1. Separation of Control & Data Planes
```yaml
# Control Plane: docker-compose.yml
services:
  nginx_load_balancer:  # Routing controller
    image: nginx:alpine
  
  rag_app_instance_1:   # Data plane worker
    build: .
```

#### 2. Programmable Infrastructure
```bash
# Add new instance programmatically
docker-compose up --scale rag_app_instance_1=5

# Update routing rules
vim nginx.conf
docker-compose restart nginx_load_balancer
```

#### 3. Centralized Control
- All routing decisions in NGINX config
- Single point of management
- Consistent policy enforcement

### SDN Benefits in Our Project

| Traditional | SDN (Our Approach) |
|------------|-------------------|
| Manual server config | Declarative YAML |
| Per-server firewall rules | Centralized rate limiting |
| Static load balancing | Dynamic service discovery |
| Vendor lock-in | Container portability |

---

## 6. NFV (Network Functions Virtualization)

### Traditional Network Functions
```
Hardware Load Balancer (F5)     → $50,000+
Hardware Firewall (Cisco ASA)   → $10,000+
Physical Router                 → $5,000+
```

### NFV Approach
```
NGINX Container (Load Balancer)    → $0 (open source)
Python App (Firewall/Rate Limiter) → $0
Docker Network (Router)            → $0
```

### Our VNFs (Virtual Network Functions)

#### 1. Virtual Load Balancer
```yaml
nginx_load_balancer:
  image: nginx:alpine  # Replaces F5 hardware
  ports:
    - "8080:80"
```

#### 2. Virtual Firewall
```python
class SecurityScanner:
    # Replaces hardware firewall functionality
    def scan_for_injection(text: str):
        # Pattern matching, rate limiting, input validation
```

#### 3. Virtual Router
```yaml
networks:
  rag_network:
    driver: bridge  # Software-defined routing
```

### NFV Benefits

| Aspect | Hardware | NFV (Ours) |
|--------|---------|-----------|
| Cost | High CapEx | Low OpEx |
| Deployment | Weeks | Minutes |
| Scaling | Buy more hardware | `docker-compose up --scale` |
| Updates | Manual, risky | Automated CI/CD |
| Portability | Vendor lock-in | Container = portable |

---

## 7. Network Security Concepts

### Defense in Depth
```
┌─────────────────────────────────────────┐
│ Layer 1: Network (NGINX)                │ → Reverse proxy, rate limits
├─────────────────────────────────────────┤
│ Layer 2: Application (FastAPI)          │ → Input validation, sanitization
├─────────────────────────────────────────┤
│ Layer 3: Container (Docker)             │ → Isolation, resource limits
├─────────────────────────────────────────┤
│ Layer 4: Host OS                        │ → Firewall, SELinux
└─────────────────────────────────────────┘
```

### Our Security Implementations

#### 1. Intrusion Detection System (IDS)
```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions?",
    r"disregard\s+(previous|above|all)\s+instructions?",
    # ... more patterns
]
```

Pattern-based detection (similar to Snort rules).

#### 2. Rate Limiting (DDoS Protection)
```python
class RateLimiter:
    MAX_REQUESTS_PER_MINUTE = 30
    MAX_REQUESTS_PER_HOUR = 200
```

Token bucket algorithm implementation.

#### 3. Input Sanitization (Firewall)
```python
def sanitize_input(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)     # Normalize whitespace
    text = text.replace('\x00', '')      # Remove null bytes
    text = text[:MAX_LENGTH]             # Truncate
    return text.strip()
```

#### 4. Least Privilege
```dockerfile
# Run as non-root user
RUN useradd -m -u 1000 appuser
USER appuser
```

---

## 8. MPLS Concepts (Bonus)

### What is MPLS?
Multiprotocol Label Switching - routes packets using labels instead of IP addresses.

### MPLS Terminology

```
┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
│  LER   │ ───→ │  LSR   │ ───→ │  LSR   │ ───→ │  LER   │
│ (Edge) │      │(Core 1)│      │(Core 2)│      │ (Edge) │
└────────┘      └────────┘      └────────┘      └────────┘
    ↓               ↓               ↓               ↓
Add Label      Swap Label      Swap Label     Remove Label
```

- **LER (Label Edge Router):** Adds/removes MPLS labels
- **LSR (Label Switch Router):** Forwards based on labels
- **LSP (Label Switched Path):** The path through network
- **FEC (Forwarding Equivalence Class):** Group of packets treated same

### MPLS-TE (Traffic Engineering)

**Goal:** Control exactly which path traffic takes (not just shortest path).

**Benefits:**
- Load balancing across multiple paths
- Bandwidth reservation
- Fast reroute on failure

### Our "MPLS-like" Implementation

#### Label = Docker Service Name
```yaml
nginx_load_balancer:
  depends_on:
    - rag_app_instance_1  # "Label 1"
    - rag_app_instance_2  # "Label 2"
    - rag_app_instance_3  # "Label 3"
```

#### LSP = Request Flow
```
Client → NGINX (LER) → Instance (LSR) → Database
         [Add route]   [Process]        [Store]
```

#### Traffic Engineering = NGINX Config
```nginx
upstream high_priority {
    server instance_1:8000 weight=10;  # More important
}

upstream low_priority {
    server instance_2:8000 weight=1;   # Less important
}
```

---

## 9. Docker Networking

### Network Types

#### Bridge Network (What We Use)
```yaml
networks:
  rag_network:
    driver: bridge
```

- Default for Docker Compose
- Containers can talk to each other by name
- Isolated from host network

#### Host Network
```yaml
network_mode: "host"
```

- Container uses host's network directly
- No network isolation
- Better performance (no NAT)

#### Overlay Network
```yaml
networks:
  rag_network:
    driver: overlay
```

- For Docker Swarm (multi-host)
- Containers across different hosts communicate
- Requires Swarm mode

### Service Discovery

```bash
# Inside container, these work:
ping rag_app_instance_1
curl http://rag_app_instance_2:8000/
```

Docker's embedded DNS resolves service names to IPs.

---

## 10. Monitoring & Observability

### Health Check Endpoints

```bash
# Overall system health
curl http://localhost:8080/

# Individual instances
curl http://localhost:8001/
curl http://localhost:8002/
curl http://localhost:8003/

# Statistics
curl http://localhost:8080/stats
```

### Docker Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rag_app_instance_1

# NGINX access logs
docker-compose logs nginx_load_balancer
```

### Performance Metrics

```bash
# Container stats (CPU, memory, network)
docker stats

# Network inspection
docker network inspect secure-rag_rag_network
```

---

## 11. Common Networking Commands

### Docker Network

```bash
# List networks
docker network ls

# Inspect network
docker network inspect rag_network

# Create network
docker network create my_network

# Connect container to network
docker network connect rag_network my_container
```

### Container Networking

```bash
# Get container IP
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' rag_app_instance_1

# Port mapping
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Test connectivity between containers
docker exec rag_app_instance_1 ping rag_app_instance_2
```

### NGINX

```bash
# Test config syntax
docker exec nginx_load_balancer nginx -t

# Reload config (graceful)
docker exec nginx_load_balancer nginx -s reload

# View upstream status (if status module enabled)
curl http://localhost:8080/status
```

---

## 12. Troubleshooting Checklist

### Problem: Can't access service

```bash
# 1. Check if containers are running
docker-compose ps

# 2. Check logs
docker-compose logs [service-name]

# 3. Check port bindings
docker ps --format "table {{.Names}}\t{{.Ports}}"

# 4. Test from inside container
docker exec rag_app_instance_1 curl http://localhost:8000/

# 5. Check firewall
sudo ufw status
sudo iptables -L
```

### Problem: Load balancer not distributing

```bash
# 1. Check NGINX config
docker exec nginx_load_balancer cat /etc/nginx/nginx.conf

# 2. Check backend health
curl http://localhost:8001/
curl http://localhost:8002/
curl http://localhost:8003/

# 3. Check NGINX logs
docker-compose logs nginx_load_balancer

# 4. Test directly to backends
for i in {8001..8003}; do curl http://localhost:$i/; done
```

### Problem: High latency

```bash
# 1. Check container resources
docker stats

# 2. Check if rate limited
# Look for HTTP 429 responses

# 3. Check instance count
docker-compose ps | grep rag_app

# 4. Scale up
docker-compose up --scale rag_app_instance_1=5 -d
```

---

## 13. Key Takeaways for Course

### Concepts Demonstrated

✅ **Layer 7 Load Balancing:** Application-aware traffic distribution  
✅ **Reverse Proxy:** Security and performance benefits  
✅ **QoS:** Rate limiting and traffic shaping  
✅ **SDN:** Programmable network infrastructure  
✅ **NFV:** Software-based network functions  
✅ **Security:** Defense in depth, IDS, rate limiting  
✅ **High Availability:** Failover and health checks  
✅ **Automation:** CI/CD for network deployments  

### Real-World Applications

- **Enterprise:** Internal APIs with load balancing
- **Cloud:** Kubernetes ingress controllers (similar pattern)
- **Security:** WAF (Web Application Firewall) implementations
- **DevOps:** GitOps-based infrastructure management

---

**End of Quick Reference**

For detailed explanations, see:
- `NETWORK_SECURITY_LAB_REPORT.md` - Comprehensive analysis
- `README_ENHANCED.md` - Full documentation
- `demo_test.sh` - Practical testing script