import os
import time
import json
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.table.types import DataTypes
from pyflink.table.udf import ScalarFunction, udf
import sys
from kafka import KafkaProducer, KafkaConsumer
import threading
import re
import yfinance as yf
import requests
from models import InitializeModels
from fetch_price import FetchPrice
from ticker_extraction import TickerExtraction
from fetch_news import FetchNews

class RagPipeline(ScalarFunction):
    def open(self, function_context):
        try:
            self.models = InitializeModels()
            ok = self.models.initialize_models()
            if not ok:
                raise RuntimeError("InitializeModels.initialize_models() returned False")

            self._embedder = self.models._embedder
            self._genai_model = self.models._genai_model
            self._pinecone_index = self.models._pinecone_index

        except Exception as e:
            raise

    def eval(self, user_query):
        try:
            if not user_query or user_query.strip() == "":
                return "Please provide a valid query"

            if getattr(self, "_embedder", None) is None or getattr(self, "_genai_model", None) is None or getattr(self, "_pinecone_index", None) is None:
                return "AI models unavailable"

            extract_ticker = TickerExtraction(user_query)
            ticker = extract_ticker.extract_ticker_from_query()
            if not ticker:
                return "Please specify a stock ticker (e.g., AAPL, TSLA, META)"

            current_price_instance = FetchPrice(ticker)
            current_price = current_price_instance.fetch_price()
            if current_price is None:
                return f"Unable to fetch price for {ticker}"

            news_context_instance = FetchNews(ticker)
            news_context = news_context_instance.fetch_news()

            comprehensive_query = f"{user_query} {ticker} current price ₹{current_price:.2f}"
            query_embedding = self._embedder.encode(comprehensive_query)
            query_vector = query_embedding.tolist()

            search_results = None
            try:
                search_results = self._pinecone_index.query(
                    vector=query_vector,
                    top_k=5,
                    include_metadata=True,
                    filter={"ticker": ticker}
                )
            except Exception as e_query:
                search_results = None

            historical_context = "Limited historical data available"
            if search_results and hasattr(search_results, 'matches') and search_results.matches:
                contexts = []
                for match in search_results.matches:
                    metadata = match.metadata if hasattr(match, 'metadata') else {}
                    context_text = metadata.get('insight') or metadata.get('text') or metadata.get('content')
                    if context_text:
                        contexts.append(f"• {context_text}")
                if contexts:
                    historical_context = "\n".join(contexts)

            ai_prompt = f"""You are a financial analyst. User asked: "{user_query}"

    CURRENT DATA:
    • {ticker} trading at ₹{current_price:.2f}

    RECENT NEWS:
    {news_context}

    HISTORICAL CONTEXT:
    {historical_context}

    Provide a brief, actionable analysis addressing the user's question. Keep it conversational and under 400 characters."""

            response = self._genai_model.generate_content(ai_prompt)
            ai_analysis = response.text if hasattr(response, 'text') else str(response)

            try:
                insight_text = f"User asked about {ticker}: {ai_analysis[:150]}"
                analysis_embedding = self._embedder.encode(insight_text)
                self._pinecone_index.upsert([{
                    "id": f"{ticker}_query_{int(time.time())}",
                    "values": analysis_embedding.tolist(),
                    "metadata": {
                        "ticker": ticker,
                        "price": current_price,
                        "insight": insight_text,
                        "timestamp": time.time(),
                        "type": "user_interaction"
                    }
                }])
            except Exception as store_error:
                print(f"Could not store to Pinecone: {store_error}")
            final_response = f" {ticker}  ₹{current_price:.2f}\n\n{ai_analysis}\n{news_context}"
            return final_response[:1000]

        except Exception as e:
            return f"Error: {str(e)}"
