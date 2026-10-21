from src.rag.retrieve import EvidenceRetriever

class InsightAgent:
    def __init__(self):
        self.retriever = EvidenceRetriever()

    def generate_answer(self, query, temperature_data=None):
        # Retrieve relevant chunks from official documents
        evidence_chunks = self.retriever.retrieve(query, top_k=3)
        
        if not evidence_chunks:
            return "I don't know"

        # Build context from retrieved chunks with explicit citations
        context_str = ""
        citations = []
        for chunk in evidence_chunks:
            src = chunk["source"]
            page = chunk["page"]
            context_str += f"\n\n{chunk['text']}\n"
            citations.append(f"{src} (p. {page})")

        # Construct final response incorporating temperature data (if provided from gold db)
        response = f"Based on official guidelines ({', '.join(set(citations))}):\n"
        if temperature_data:
            response += f"Current temperature data (Row ID: {temperature_data.get('row_id')}): {temperature_data.get('temp')}°C.\n"
        
        response += f"\nRelevant Guidance:\n{evidence_chunks[0]['text']}"
        return response

if __name__ == "__main__":
    agent = InsightAgent()
    print(agent.generate_answer("What are the emergency measures for Karachi heatwave?"))