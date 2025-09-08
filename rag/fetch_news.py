import os
import requests
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
class FetchNews:
    def __init__(self,ticker):
        self.ticker=ticker

    def fetch_news(self):
        try:
            url="https://newsapi.org/v2/everything"
            params={
                'q':f"{self.ticker} stock news",
                'apiKey':NEWS_API_KEY,
                'sortBy':'publishedAt',
                'language':'en',
                'pageSize':3
            }
            response=requests.get(url,params=params)
            if response.status_code==200:
                articles=response.json().get('articles',[])
                news_context=[]
                for x in articles:
                    title=x.get('title','')
                    description=x.get('description','')
                    if title and description:
                     news_context.append(f"• {title}: {description}")
                return "\n".join(news_context)
            else:
                return "No recent news available"
        except Exception as e:
            print(f"Error fetching news for {self.ticker}: {e}")
            return "No recent news available"