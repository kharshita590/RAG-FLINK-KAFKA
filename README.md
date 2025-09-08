# RAG-FLINK-KAFKA
USE PYTHON 3.11.5

Clone The Repository

git clone 
cd rag 
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python -m flink_job.py
uvicorn app:app --reload

cd rag-fr 
npm i
npm run dev
