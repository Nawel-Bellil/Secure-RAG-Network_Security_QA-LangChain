#!/bin/bash

echo "======================================"
echo "RAG Document Q&A System - Test Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost"

echo -e "${BLUE}1. Testing Health Check...${NC}"
curl -s "${BASE_URL}/" | jq '.'
echo ""

echo -e "${BLUE}2. Creating a sample document...${NC}"
cat > sample_doc.txt << 'EOF'
Machine Learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.

There are three main types of machine learning:
1. Supervised Learning: The algorithm learns from labeled training data
2. Unsupervised Learning: The algorithm finds patterns in unlabeled data
3. Reinforcement Learning: The algorithm learns through trial and error

Deep Learning is a specialized branch of machine learning that uses neural networks with multiple layers. It has revolutionized fields like computer vision, natural language processing, and speech recognition.

Popular machine learning frameworks include TensorFlow, PyTorch, and scikit-learn. These tools make it easier for developers to build and deploy ML models.
EOF
echo "Sample document created!"
echo ""

echo -e "${BLUE}3. Uploading document...${NC}"
curl -s -X POST "${BASE_URL}/upload" \
  -F "file=@sample_doc.txt" | jq '.'
echo ""

echo -e "${BLUE}4. Checking stats...${NC}"
curl -s "${BASE_URL}/stats" | jq '.'
echo ""

echo -e "${BLUE}5. Testing multiple questions (watch the instance_id change)...${NC}"
echo ""

questions=(
  "What is machine learning?"
  "What are the three types of machine learning?"
  "What is deep learning?"
  "What frameworks are mentioned?"
  "Explain supervised learning"
)

for question in "${questions[@]}"; do
  echo -e "${GREEN}Question: $question${NC}"
  curl -s -X POST "${BASE_URL}/ask" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"$question\"}" | jq -r '.instance_id as $id | .answer as $ans | "Instance: \($id)\nAnswer: \($ans)\n"'
  echo "---"
  sleep 1
done

echo -e "${BLUE}6. Testing load distribution - 10 rapid requests...${NC}"
for i in {1..10}; do
  curl -s -X POST "${BASE_URL}/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "What is ML?"}' | jq -r '.instance_id' &
done
wait
echo ""

echo -e "${GREEN}Test completed!${NC}"
echo "Cleanup: rm sample_doc.txt"
rm sample_doc.txt