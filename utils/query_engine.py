import logging
import time
from typing import List
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from utils.index_manager import IndexManager

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a helpful AI assistant analyzing multiple documents. Answer based on all available context. If you cannot find the complete answer in the provided context, say so.

Context from multiple documents:
{context}

Question: {question}

Instructions:
1. Consider ALL provided context from ALL documents when answering
2. Synthesize information from multiple sources if relevant
3. Cite specific documents when referencing information
4. Be thorough but concise
5. If information from multiple documents conflicts, mention this
6. If the answer isn't fully available in the context, say so

Answer: """

MODEL = "deepseek-r1-distill-llama-70b"


class QueryEngine:
    def __init__(self, groq_api_key, session_id: str = None):
        self.llm = None
        self.session_id = session_id
        self.initialize_llm(groq_api_key)
        Settings.llm = self.llm
        self.index_manager = IndexManager(session_id=session_id)
        self._response_cache = {}

    def initialize_llm(self, api_key: str, max_retries: int = 3) -> None:
        """Initialize the LLM with retries and error handling."""
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                self.llm = Groq(
                    # model="mixtral-8x7b-32768",
                    model=MODEL,
                    api_key=api_key,
                    temperature=0.3,
                    max_tokens=2048,
                )
                logger.info("Successfully initialized Groq LLM")
                return
            except Exception as e:
                retry_count += 1
                last_error = str(e)
                wait_time = min(2**retry_count, 30)  # Cap wait time at 30 seconds
                logger.warning(f"LLM init attempt {retry_count} failed: {last_error}")

                if retry_count < max_retries:
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to initialize LLM after {max_retries} attempts. Last error: {last_error}"
                    )
                    raise RuntimeError(f"Failed to initialize LLM: {last_error}")

    def _format_context(self, nodes: List[dict], max_length: int = 4000) -> str:
        """Format context from retrieved nodes with better source attribution."""
        if not nodes:
            return ""

        context_parts = []
        current_length = 0
        sources_seen = set()

        for node in nodes:
            if not hasattr(node, "metadata") or not hasattr(node, "text"):
                continue

            source = node.metadata.get("file_name", "Unknown Source")
            text = node.text.strip()

            # Skip if we've already included too much from this source
            if source in sources_seen and len(sources_seen) > 1:
                continue

            sources_seen.add(source)

            # Format this chunk with source
            chunk = f"\n[From {source}]\n{text}\n---\n"

            # Check if adding this would exceed max length
            if current_length + len(chunk) > max_length:
                # Try to include at least something from every source
                if len(sources_seen) < len(
                    set(n.metadata.get("file_name", "") for n in nodes)
                ):
                    continue
                break

            context_parts.append(chunk)
            current_length += len(chunk)

        return "\n".join(context_parts)

    def query(self, question: str) -> str:
        """Process query and return a response."""
        try:
            # Check cache first
            cache_key = (
                f"{self.session_id}_{hash(question)}"
                if self.session_id
                else hash(question)
            )
            if cache_key in self._response_cache:
                logger.info("Returning cached response")
                return self._response_cache[cache_key]

            # Get context from documents with increased retrieval
            retrieved_nodes = self.index_manager.query_index(
                question, top_k=5
            )  # Increased from 3
            if not retrieved_nodes:
                return "I couldn't find any relevant information in the documents. Please try uploading relevant documents or rephrasing your question."

            # Format context with source attribution
            context = self._format_context(retrieved_nodes)
            if not context:
                return "I encountered an error processing the document context. Please try again."

            # Build prompt using template
            prompt = PROMPT_TEMPLATE.format(context=context, question=question)

            # Get response from LLM with increased tokens
            response = self.llm.complete(
                prompt,
                max_tokens=2000,  # Increased from 1000
                temperature=0.3,
            )

            # Cache and return response
            result = response.text.strip()
            self._response_cache[cache_key] = result
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in query processing: {error_msg}", exc_info=True)

            if "rate limit" in error_msg.lower():
                return "I'm currently experiencing high demand. Please try again in a few moments."
            elif "timeout" in error_msg.lower():
                return "The request took too long to process. Please try again or try with a simpler question."
            else:
                return "I encountered an error processing your question. Please try again or contact support if the problem persists."

    def evaluate_response(self, query: str, response: str, contexts: List[str]) -> dict:
        """Evaluates the response for faithfulness and relevancy."""
        return {
            "query": query,
            "response": response,
            "context_count": len(contexts),
            "timestamp": time.time(),
        }
