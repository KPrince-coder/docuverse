from llama_index.llms.groq import Groq
from llama_index.core import Settings
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from utils.index_manager import IndexManager
import logging

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
You are an intelligent assistant tasked with answering questions based on the provided documents. 
Use the following context to answer the question. If the answer cannot be found in the context, 
respond with "I don't know."

Context: {context}

Question: {question}

Based on the provided documents, here's the answer:
"""


class QueryEngine:
    def __init__(self, groq_api_key):
        # Configure Groq LLM
        self.llm = Groq(
            model="mixtral-8x7b-32768",  # Using Mixtral for better performance
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=2048,
        )

        Settings.llm = self.llm
        self.index_manager = IndexManager()

        # Initialize evaluators
        self.faithfulness_evaluator = FaithfulnessEvaluator(llm=self.llm)
        self.relevancy_evaluator = RelevancyEvaluator(llm=self.llm)

    def query(self, question: str) -> str:
        """Queries the index and generates a response using the document context."""
        try:
            # Get context from documents
            retrieved_context = self.index_manager.query_index(question)

            # Log retrieved context for debugging
            logger.info(f"Retrieved context length: {len(str(retrieved_context))}")

            # Format prompt with context
            prompt = PROMPT_TEMPLATE.format(
                context=retrieved_context, question=question
            )

            # Generate response
            response = self.llm.complete(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            return "I apologize, but I encountered an error processing your question. Please try again."

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
