# 🚀 RAG-FLINK-KAFKA

A **Real-time RAG-powered Financial Chatbot** built with **Apache Flink + Kafka + FastAPI + Next.js** ⚡  
It streams user queries in real-time, retrieves relevant financial data, and generates **AI-powered insights**.  

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)  
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)  
![Next.js](https://img.shields.io/badge/Next.js-13-black?logo=next.js)  
![Apache Flink](https://img.shields.io/badge/Flink-Kafka-orange?logo=apacheflink)  
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Prerequisites
Make sure you have installed:
- 🐍 **Python 3.11 or lower (<= 3.11)**  
- 🟢 **Node.js + npm**  
- 🌱 **Git**  
- ⚡ **Kafka + Flink (running locally or on Docker)**  

---

## 🔧 Installation & Setup  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/kharshita590/RAG-FLINK-KAFKA


cd rag
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt

# Run Flink job
python -m flink_job.py

# Start FastAPI server
uvicorn app:app --reload

cd rag-fr

# Install dependencies
npm install

# Run the development server
npm run dev
