from pinecone import Pinecone,ServerlessSpec
import google.generativeai as genai
import os
from sentence_transformers import SentenceTransformer
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
INDEX_NAME = os.getenv("PINECONE_INDEX", "finance-rag")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
class InitializeModels:
    def __init__(self):
        self._embedder=None
        self._genai_model=None
        self._pinecone_index=None

    def initialize_models(self,auto_create_index=True):
        if self._embedder is not None and self._genai_model is not None and self._pinecone_index is not None:
            return True
        
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self._genai_model=genai.GenerativeModel("gemini-1.5-flash")
            self._embedder=SentenceTransformer("all-mpnet-base-v2")
            embed_dim=(self._embedder.get_sentence_embedding_dimension()
                      if hasattr(self._embedder,"get_sentence_embedding_dimension")
                      else len(self._embedder.encode("test")))
            _pinecone_client=Pinecone(api_key=PINECONE_API_KEY,environment=os.getenv("PINECONE_ENV",None))
            existing=_pinecone_client.list_indexes()
            if hasattr(existing,"names"):
                existing=existing.names()
            if not isinstance(existing, (list, tuple)):
                try:
                    existing = list(existing)
                except Exception:
                    existing = []
            if INDEX_NAME not in existing:
                if not auto_create_index:
                    raise RuntimeError(f"Pinecone index '{INDEX_NAME}' not found and auto_create_index=False")
                pinecone_cloud = os.getenv("PINECONE_CLOUD", "aws")        
                pinecone_region = os.getenv("PINECONE_REGION", "us-east-1") 
                spec = ServerlessSpec(cloud=pinecone_cloud, region=pinecone_region)

                print(f"Pinecone index '{INDEX_NAME}' not found. Creating index dim={embed_dim} spec={pinecone_cloud}/{pinecone_region} ...")
                _pinecone_client.create_index(name=INDEX_NAME, dimension=int(embed_dim), metric='cosine', spec=spec)
                for _ in range(15):
                    time.sleep(1)
                    existing = _pinecone_client.list_indexes()
                    if hasattr(existing, "names"):
                        existing = existing.names()
                    if INDEX_NAME in existing:
                        break
                else:
                    raise RuntimeError("Index creation timed out / index not visible in list_indexes()")
            self._pinecone_index = _pinecone_client.Index(INDEX_NAME)
            print("Models and Pinecone index ready.")
            return True

        except Exception as e:
            print(f"Error initializing models: {e}")
            if "not found" in str(e).lower() or "404" in str(e):
                print("Hint: index missing or API key/permissions issue. Check PINECONE_API_KEY, PINECONE_ENV, PINECONE_CLOUD and PINECONE_REGION.")
            return False

                


        

