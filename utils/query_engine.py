# import logging
# import time
# from typing import List
# from llama_index.core import Settings
# from llama_index.llms.groq import Groq
# from .index_manager import IndexManager

# logger = logging.getLogger(__name__)

# PROMPT_TEMPLATE = """You are a helpful AI assistant analyzing documents and maintaining conversation context.

# Previous conversation:
# {conversation_history}

# Context from documents:
# {context}

# Current question: {question}

# Instructions:
# 1. Consider both the conversation history AND document context
# 2. Reference previous questions/answers when relevant
# 3. Cite specific documents when referencing information
# 4. Be consistent with previous responses
# 5. If information conflicts with previous answers, explain the difference
# 6. If the answer isn't in the context or previous conversation, say so

# Answer: """

# MODEL = "deepseek-r1-distill-llama-70b"


# class QueryEngine:
#     def __init__(self, groq_api_key, session_id: str = None):
#         self.llm = None
#         self.session_id = session_id
#         self.index_manager = IndexManager(
#             session_id=session_id
#         )  # Initialize index manager first
#         self.initialize_llm(groq_api_key)
#         Settings.llm = self.llm  # Set LLM after initialization
#         self._response_cache = {}
#         self._ensure_index()  # Add this method call

#     def _ensure_index(self):
#         """Ensure index is built or loaded."""
#         try:
#             if not self.index_manager.index:
#                 self.index_manager.load_index()
#             return True
#         except Exception as e:
#             logger.error(f"Failed to ensure index: {e}")
#             return False

#     def initialize_llm(self, api_key: str, max_retries: int = 3) -> None:
#         """Initialize the LLM with retries and error handling."""
#         retry_count = 0
#         last_error = None

#         while retry_count < max_retries:
#             try:
#                 self.llm = Groq(
#                     # model="mixtral-8x7b-32768",
#                     model=MODEL,
#                     api_key=api_key,
#                     temperature=0.3,
#                     max_tokens=2048,
#                 )
#                 logger.info("Successfully initialized Groq LLM")
#                 return
#             except Exception as e:
#                 retry_count += 1
#                 last_error = str(e)
#                 wait_time = min(2**retry_count, 30)  # Cap wait time at 30 seconds
#                 logger.warning(f"LLM init attempt {retry_count} failed: {last_error}")

#                 if retry_count < max_retries:
#                     logger.info(f"Retrying in {wait_time} seconds...")
#                     time.sleep(wait_time)
#                 else:
#                     logger.error(
#                         f"Failed to initialize LLM after {max_retries} attempts. Last error: {last_error}"
#                     )
#                     raise RuntimeError(f"Failed to initialize LLM: {last_error}")

#     def _format_context(self, nodes: List[dict], max_length: int = 4000) -> str:
#         """Format context from retrieved nodes with better source attribution."""
#         if not nodes:
#             return ""

#         context_parts = []
#         current_length = 0
#         sources_seen = set()

#         for node in nodes:
#             if not hasattr(node, "metadata") or not hasattr(node, "text"):
#                 continue

#             source = node.metadata.get("file_name", "Unknown Source")
#             text = node.text.strip()

#             # Skip if we've already included too much from this source
#             if source in sources_seen and len(sources_seen) > 1:
#                 continue

#             sources_seen.add(source)

#             # Format this chunk with source
#             chunk = f"\n[From {source}]\n{text}\n---\n"

#             # Check if adding this would exceed max length
#             if current_length + len(chunk) > max_length:
#                 # Try to include at least something from every source
#                 if len(sources_seen) < len(
#                     set(n.metadata.get("file_name", "") for n in nodes)
#                 ):
#                     continue
#                 break

#             context_parts.append(chunk)
#             current_length += len(chunk)

#         return "\n".join(context_parts)

#     def _format_conversation_history(self, history: List[dict]) -> str:
#         """Format conversation history for context."""
#         if not history:
#             return "No previous conversation."

#         formatted_history = []
#         for msg in history[:-1]:  # Exclude current question
#             role = "User" if msg["role"] == "user" else "Assistant"
#             formatted_history.append(f"{role}: {msg['content']}")

#         return "\n".join(formatted_history)

#     def query(self, question: str, conversation_history: List[dict] = None) -> str:
#         """Process query with conversation history."""
#         try:
#             # Ensure index exists
#             if not self._ensure_index():
#                 return "Failed to initialize document index. Please try refreshing the page."

#             # Check cache first
#             cache_key = (
#                 f"{self.session_id}_{hash(question)}"
#                 if self.session_id
#                 else hash(question)
#             )
#             if cache_key in self._response_cache:
#                 logger.info("Returning cached response")
#                 return self._response_cache[cache_key]

#             # Format conversation history
#             conv_history = self._format_conversation_history(conversation_history or [])

#             # Get document context
#             retrieved_nodes = self.index_manager.query_index(question, top_k=5)
#             if not retrieved_nodes:
#                 return "I couldn't find any relevant information in the documents. Please try uploading relevant documents or rephrasing your question."

#             # Format document context
#             doc_context = self._format_context(retrieved_nodes)

#             # Build prompt with both contexts
#             prompt = PROMPT_TEMPLATE.format(
#                 conversation_history=conv_history,
#                 context=doc_context,
#                 question=question,
#             )

#             # Get response from LLM with increased tokens
#             response = self.llm.complete(
#                 prompt,
#                 max_tokens=2000,  # Increased from 1000
#                 temperature=0.3,
#             )

#             # Cache and return response
#             result = response.text.strip()
#             self._response_cache[cache_key] = result
#             return result

#         except Exception as e:
#             error_msg = str(e)
#             logger.error(f"Error in query processing: {error_msg}", exc_info=True)

#             if "rate limit" in error_msg.lower():
#                 return "I'm currently experiencing high demand. Please try again in a few moments."
#             elif "timeout" in error_msg.lower():
#                 return "The request took too long to process. Please try again or try with a simpler question."
#             else:
#                 return "I encountered an error processing your question. Please try again or contact support if the problem persists."

#     def evaluate_response(self, query: str, response: str, contexts: List[str]) -> dict:
#         """Evaluates the response for faithfulness and relevancy."""
#         return {
#             "query": query,
#             "response": response,
#             "context_count": len(contexts),
#             "timestamp": time.time(),
#         }


import logging
import time
from typing import List
from llama_index.core import Settings
from llama_index.llms.groq import Groq
from .index_manager import IndexManager

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a helpful AI assistant analyzing documents and maintaining conversation context. 

Previous conversation:
{conversation_history}

Context from documents:
{context}

Current question: {question}

Instructions:
1. Consider both the conversation history AND document context
2. Reference previous questions/answers when relevant
3. Cite specific documents when referencing information
4. Be consistent with previous responses
5. If information conflicts with previous answers, explain the difference
6. If the answer isn't in the context or previous conversation, say so
7. Be universal and ready to do anything. Including quizing with the user, or even playing games.

Answer: """

# MODEL = "mixtral-8x7b-32768"
MODEL = "deepseek-r1-distill-llama-70b"


class QueryEngine:
    def __init__(self, groq_api_key, session_id: str = None):
        self.llm = None
        self.session_id = session_id
        self.index_manager = IndexManager(
            session_id=session_id
        )  # Initialize index manager first
        self.initialize_llm(groq_api_key)
        Settings.llm = self.llm  # Set LLM after initialization
        self._response_cache = {}
        self._ensure_index()  # Ensure index is loaded or built

    def _ensure_index(self):
        """Ensure index is built or loaded."""
        try:
            if not self.index_manager.index:
                self.index_manager.load_index()
            return True
        except Exception as e:
            logger.error(f"Failed to ensure index: {e}")
            return False

    def initialize_llm(self, api_key: str, max_retries: int = 3) -> None:
        """Initialize the LLM with retries and error handling."""
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                self.llm = Groq(
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

    def _format_conversation_history(self, history: List[dict]) -> str:
        """Format conversation history for context."""
        if not history:
            return "No previous conversation."

        formatted_history = []
        for msg in history[:-1]:  # Exclude current question
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_history.append(f"{role}: {msg['content']}")

        return "\n".join(formatted_history)

    def query(self, question: str, conversation_history: List[dict] = None) -> str:
        """Process query with conversation history."""
        try:
            # Ensure index exists
            if not self._ensure_index():
                return "Failed to initialize document index. Please try refreshing the page."

            # Check cache first
            cache_key = (
                f"{self.session_id}_{hash(question)}"
                if self.session_id
                else hash(question)
            )
            if cache_key in self._response_cache:
                logger.info("Returning cached response")
                return self._response_cache[cache_key]

            # Format conversation history
            conv_history = self._format_conversation_history(conversation_history or [])

            # Get document context
            retrieved_nodes = self.index_manager.query_index(question, top_k=5)
            if not retrieved_nodes:
                return "I couldn't find any relevant information in the documents. Please try uploading relevant documents or rephrasing your question."

            # Format document context
            doc_context = self._format_context(retrieved_nodes)

            # Build prompt with both contexts
            prompt = PROMPT_TEMPLATE.format(
                conversation_history=conv_history,
                context=doc_context,
                question=question,
            )

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
