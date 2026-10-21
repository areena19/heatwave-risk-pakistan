import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class EvidenceRetriever:
    def __init__(self):
        processed_path = "data/processed/evidence_chunks.pkl"
        if os.path.exists(processed_path):
            self.df = pd.read_pickle(processed_path)
            self.vectorizer = TfidfVectorizer(stop_words='english')
            if not self.df.empty:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.df['text'])
            else:
                self.tfidf_matrix = None
        else:
            self.df = pd.DataFrame()
            self.tfidf_matrix = None

    def retrieve(self, query, top_k=3):
        if self.df.empty or self.tfidf_matrix is None:
            return []
        
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05: # threshold
                row = self.df.iloc[idx]
                results.append({
                    "source": row["source"],
                    "page": row["page"],
                    "text": row["text"],
                    "score": float(similarities[idx])
                })
        return results

if __name__ == "__main__":
    retriever = EvidenceRetriever()
    test_results = retriever.retrieve("heatwave SOPs Karachi")
    print(f"Test retrieved {len(test_results)} chunks.")