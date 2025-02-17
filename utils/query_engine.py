import logging
import time
import concurrent.futures
import threading
from typing import List
import backoff
from requests.exceptions import RequestException
from datetime import datetime, timedelta
from collections import deque

from llama_index.core import Settings
from llama_index.llms.groq import Groq
from .index_manager import IndexManager

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a highly versatile AI assistant designed to interact with documents and maintain an engaging, dynamic conversation. Your goal is to provide tailored responses, engage the user in activities (such as quizzes or games), and be ready for any request based on the documents provided.

Previous conversation:
{conversation_history}

Context from documents:
{context}

Current question: {question}

Instructions:
1. Consider both the conversation history AND document context thoroughly before answering.
2. Respond to questions in a clear, precise, and engaging manner.
3. Reference specific documents when answering, ensuring transparency and accuracy.
4. Keep responses consistent with previous interactions and document context.
5. **Only refer to relevant parts of previous conversations.** Focus on information that is pertinent to the current question or request. Avoid referring to irrelevant or unnecessary prior conversations that do not contribute to answering the current prompt.
6. If new information conflicts with previous responses, explain the discrepancy in a helpful and clear manner.
7. **Do not guess or add any information that is not directly supported by the context or files provided.** All answers should be based strictly on the documents or context given, without any speculation or hallucination.
8. If the requested information cannot be found in the provided documents or context, inform the user directly and concisely. Say something like, "The requested information is not available in the documents provided" or "I couldn't find that in the context."
9. Be ready to assist in a wide range of scenarios, including but not limited to:
   - Quizzing the user on the documents: Ask questions about the content, and prompt the user for answers.
   - Playing games or engaging in other interactive experiences, based on the documents or general knowledge.
   - Offering summaries, explanations, or breaking down complex sections of documents.
   - Performing document-specific tasks such as finding keywords, extracting quotes, or comparing passages.
10. Always be open to dynamic requests and be prepared to switch between different modes of interaction (informative, casual, interactive, playful, etc.).
11. Adapt to the user's tone and style of communication. Be flexible in providing information, whether the user prefers short answers, detailed explanations, or interactive responses.

Answer:

"""


class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = deque()
        self.lock = threading.Lock()

    def can_make_request(self):
        now = datetime.now()
        with self.lock:
            # Remove old requests outside the time window
            while self.requests and (now - self.requests[0]) > timedelta(
                seconds=self.time_window
            ):
                self.requests.popleft()

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False

    def wait_for_slot(self):
        while not self.can_make_request():
            time.sleep(1)


class QueryEngine:
    def __init__(
        self, groq_api_key, session_id: str = None, model: str = "mixtral-8x7b-32768"
    ):
        self.llm = None
        self.session_id = session_id
        self.model = model
        self.index_manager = IndexManager(session_id=session_id)
        self.initialize_llm(groq_api_key)
        Settings.llm = self.llm

        # Dedicated thread pool for query processing
        self._query_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._response_cache = {}
        self._cache_lock = threading.Lock()

        # Ensure index is loaded/initialized lazily
        self._ensure_index()

        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
        self.retries = 3
        self.retry_delay = 5

    def _ensure_index(self):
        """Lazy-load or reload the document index."""
        try:
            if not self.index_manager.index:
                self.index_manager.load_index()
            return True
        except Exception as e:
            logger.error(f"Failed to ensure index: {e}")
            return False

    def initialize_llm(self, api_key: str, max_retries: int = 3) -> None:
        """Initialize the LLM with retries and exponential backoff."""
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                self.llm = Groq(
                    model=self.model,  # Use the selected model
                    api_key=api_key,
                    temperature=0.3,
                    max_tokens=2048,
                )
                logger.info(
                    f"Successfully initialized Groq LLM with model {self.model}"
                )
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

            # Format this chunk with source information
            chunk = f"\n[From {source}]\n{text}\n---\n"

            # Check if adding this would exceed max_length
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

    def _format_conversation_history(self, history: List[dict]) -> str:
        """Format conversation history for context."""
        if not history:
            return "No previous conversation."

        formatted_history = []
        for msg in history[:-1]:  # Exclude current question
            role = "User" if msg.get("role") == "user" else "Assistant"
            formatted_history.append(f"{role}: {msg.get('content', '')}")

        return "\n".join(formatted_history)

    @backoff.on_exception(
        backoff.expo,
        (RequestException, Exception),
        max_tries=3,
        max_time=30,
        giveup=lambda e: "429" in str(e),  # Don't retry on rate limits
    )
    def query(self, question: str, conversation_history: List[dict] = None) -> str:
        """Process query with rate limiting and enhanced error handling."""
        try:
            # Wait for rate limit slot
            self.rate_limiter.wait_for_slot()

            # Use a cache key based on session and question hash
            cache_key = (
                f"{self.session_id}_{hash(question)}"
                if self.session_id
                else hash(question)
            )
            with self._cache_lock:
                if cache_key in self._response_cache:
                    return self._response_cache[cache_key]

            def _async_query():
                try:
                    # Ensure the document index is available
                    if not self._ensure_index():
                        return "⚠️ Document index initialization failed. Please try refreshing the page."

                    conv_history = self._format_conversation_history(
                        conversation_history or []
                    )

                    # Retrieve relevant document nodes
                    retrieved_nodes = self.index_manager.query_index(question, top_k=5)
                    if not retrieved_nodes:
                        return (
                            "I couldn't find any relevant information in the documents. "
                            "Please try uploading relevant documents or rephrasing your question."
                        )

                    doc_context = self._format_context(retrieved_nodes)

                    # Build the prompt using both conversation history and document context
                    prompt = PROMPT_TEMPLATE.format(
                        conversation_history=conv_history,
                        context=doc_context,
                        question=question,
                    )

                    # Get response from the LLM
                    response = self.llm.complete(
                        prompt,
                        max_tokens=2000,  # Increased token limit for detailed responses
                        temperature=0.3,
                    )
                    result = response.text.strip()
                    return result

                except Exception as e:
                    error_msg = str(e)
                    if "503" in error_msg:
                        return "⚠️ The AI service is temporarily unavailable. Please try again in a few moments."
                    elif "429" in error_msg:
                        return "⚠️ Too many requests. Please wait a moment before trying again."
                    else:
                        logger.error(f"Query processing error: {error_msg}")
                        return f"⚠️ An error occurred: {error_msg}"

            # Run the query in the dedicated thread pool
            future = self._query_pool.submit(_async_query)
            try:
                result = future.result(timeout=45)  # Increased timeout
                # Cache successful results
                if not result.startswith("⚠️"):
                    with self._cache_lock:
                        self._response_cache[cache_key] = result
                return result
            except concurrent.futures.TimeoutError:
                return "⚠️ The request took too long. Please try a simpler question or try again later."

        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return "⚠️ Something went wrong. Please try again in a few moments."

    def evaluate_response(self, query: str, response: str, contexts: List[str]) -> dict:
        """Evaluate the response for relevancy and timeliness."""
        return {
            "query": query,
            "response": response,
            "context_count": len(contexts),
            "timestamp": time.time(),
        }
