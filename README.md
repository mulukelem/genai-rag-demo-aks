
# RAG PDF Chatbot

This project demonstrates a Retrieval-Augmented Generation (RAG) chatbot using a local LLaMA model deployed on Azure Kubernetes Service (AKS).

## 🧱 Project Structure

```
rag-pdf-chatbot/
├── app.py
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── models/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── pv.yaml
│   └── pvc.yaml
└── README.md
```

## 🚀 Prerequisites
- Azure CLI & logged in
- AKS cluster
- Azure Container Registry (ACR)
- Jenkins server with necessary Azure CLI and Docker installed

## 🔁 Jenkins Pipeline Steps

1. Build and push Docker image to ACR
2. Provision AKS credentials
3. Apply Kubernetes manifests for persistent volume and deployment

## 🔄 Model Volume

Make sure your LLaMA model is available on your AKS node at `/mnt/models/llama`.
