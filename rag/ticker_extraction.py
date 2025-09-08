import re
class TickerExtraction:
    def __init__(self,query):
        self.query=query
        self.ticker_patterns = [
        r'\b([A-Z]{1,10}(?:\.[A-Z]{1,5})?)\b(?:\s+stock|\s+price|\s+analysis)?',
        r'(?:ticker|symbol|stock)\s+([A-Z]{1,10}(?:\.[A-Z]{1,5})?)\b'
]

    def extract_ticker_from_query(self):
        query_upper=self.query.upper()
        for pattern in self.ticker_patterns:
            matches=re.findall(pattern,query_upper)
            if matches:
                return matches[0]