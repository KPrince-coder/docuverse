from llama_index.llms.groq import Groq
from utils.index_manager import IndexManager

PROMPT_TEMPLATE = """
You are an intelligent assistant tasked with answering questions based on the provided context. 
If the answer cannot be found in the context, respond with "I don't know."

Context: {context}

Question: {question}

Answer:
"""


class QueryEngine:
    def __init__(self, groq_api_key):
        self.index_manager = IndexManager()
        self.groq_api_key = groq_api_key
        self.llm = Groq(model="llama3-70b-8192", api_key=self.groq_api_key)

    def query(self, question):
        """Queries the index and uses Groq LLM to generate a response."""
        retrieved_context = self.index_manager.query_index(question)

        # Use the refined prompt template
        prompt = PROMPT_TEMPLATE.format(context=retrieved_context, question=question)

        # Generate response using Groq LLM
        response = self.llm.complete(prompt)
        return response.text
