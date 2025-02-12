from llama_index.llms.groq import Groq
from llama_index.core import Settings
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator
from utils.index_manager import IndexManager
import logging

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
You are DocuVerse, an intelligent document analysis assistant. You have access to various documents and their metadata.
For each piece of context, you know:
- The source file name
- The file type
- When it was created and modified
- The file size
- The actual content

Use this information to provide comprehensive answers that reference both the content and the source documents.

Context Documents:
{context}

Question: {question}

Please provide a detailed response following this structure:
1. Direct Answer: Provide a clear, concise answer to the question
2. Source Details: List the relevant source documents used, including their names and types
3. Additional Context: Include any relevant metadata about the sources that might be helpful
4. Confidence: Indicate how confident you are in the answer based on the available information

Response:
"""


class QueryEngine:
    def __init__(self, groq_api_key):
        # Configure Groq LLM
        self.llm = Groq(
            model="mixtral-8x7b-32768",  # Using Mixtral for better performance
            api_key=groq_api_key,
            temperature=0.3,
            max_tokens=2048,
            context_window=32768,  # Increased context window
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
            retrieved_nodes = self.index_manager.query_index(question)

            # Extract metadata from nodes
            context_with_metadata = []
            for node in retrieved_nodes:
                metadata = node.metadata
                content = node.text
                context_entry = f"""
                Source: {metadata.get('file_name', 'Unknown')}
                Type: {metadata.get('file_type', 'Unknown')}
                Last Modified: {metadata.get('modified_at', 'Unknown')}
                Content: {content}
                ---
                """
                context_with_metadata.append(context_entry)

            # Format prompt with context
            prompt = PROMPT_TEMPLATE.format(
                context="\n".join(context_with_metadata),
                question=question
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
