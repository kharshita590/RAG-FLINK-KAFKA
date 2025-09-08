# RAG-FLINK-KAFKA
USE PYTHON 3.11 or <=11

Clone The Repository

git clone https://github.com/kharshita590/RAG-FLINK-KAFKA
cd rag 
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python -m flink_job.py
uvicorn app:app --reload

cd rag-fr 
npm i
npm run dev
