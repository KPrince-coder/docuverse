from llama_index.llms.groq import Groq
from llama_index.core import Settings
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from utils.index_manager import IndexManager

PROMPT_TEMPLATE = """
You are an intelligent assistant tasked with answering questions based on the provided context. 
If the answer cannot be found in the context, respond with "I don't know."

Context: {context}
Question: {question}
Answer:
"""

MODEL = "deepseek-r1-distill-llama-70b"


class QueryEngine:
    def __init__(self, groq_api_key):
        # Set up Groq LLM in global settings
        Settings.llm = Groq(model=MODEL, temperature=0.5, api_key=groq_api_key)

        self.index_manager = IndexManager()
        self.llm = Settings.llm

        # Initialize evaluators with global LLM
        self.faithfulness_evaluator = FaithfulnessEvaluator()
        self.relevancy_evaluator = RelevancyEvaluator()

    def query(self, question):
        """Queries the index and uses Groq LLM to generate a response."""
        retrieved_context = self.index_manager.query_index(question)

        # Use the refined prompt template
        prompt = PROMPT_TEMPLATE.format(context=retrieved_context, question=question)

        # Generate response using Groq LLM
        response = self.llm.complete(prompt)
        return response.text

    def evaluate_response(self, query, response, contexts):
        """Evaluates the response for faithfulness and relevancy."""
        faithfulness_result = self.faithfulness_evaluator.evaluate(
            query=query, response=response, contexts=contexts
        )
        relevancy_result = self.relevancy_evaluator.evaluate(
            query=query, response=response, contexts=contexts
        )
        return {
            "faithfulness": faithfulness_result.passing,
            "relevancy": relevancy_result.passing,
            "faithfulness_feedback": faithfulness_result.feedback,
            "relevancy_feedback": relevancy_result.feedback,
        }
