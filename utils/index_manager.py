import os
import time
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    Settings,
)
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.json import JSONReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# EMBEDDING IMPLEMENTATIONS
# ========================


class BasicEmbedding(BaseEmbedding):
    """Fallback embedding using text hashing"""

    def __init__(self):
        super().__init__()
        self._model_name = "basic-hash-embedding"
        self._model_dim = 384
        self._normalize = True

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._hash_text(query)

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._hash_text(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._hash_text(text)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._hash_text(text)

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_text(text) for text in texts]

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_text(text) for text in texts]

    def _hash_text(self, text: str) -> List[float]:
        """Create hash-based embedding vector"""
        import hashlib

        hash_obj = hashlib.sha384(text.encode())
        hash_bytes = hash_obj.digest()
        embedding = np.frombuffer(hash_bytes, dtype=np.uint8)
        embedding = embedding.astype(np.float32) / 255.0
        return embedding.tolist()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_dim(self) -> int:
        return self._model_dim

    @property
    def normalize(self) -> bool:
        return self._normalize


# =================
# CORE FUNCTIONALITY
# =================


def get_file_metadata(path: str) -> Dict[str, Any]:
    """Generate metadata for files"""
    stats = os.stat(path)
    ext = os.path.splitext(path)[1][1:].lower()

    file_type_categories = {
        "text": ["txt", "md"],
        "document": ["pdf", "docx"],
        "presentation": ["ppt", "pptm", "pptx"],
        "spreadsheet": ["csv"],
        "ebook": ["epub"],
        "email": ["mbox"],
        "notebook": ["ipynb"],
        "korean_doc": ["hwp"],
        "data": ["json"],
    }

    file_category = next(
        (cat for cat, exts in file_type_categories.items() if ext in exts), "other"
    )

    return {
        "file_name": os.path.basename(path),
        "file_type": ext,
        "file_category": file_category,
        "file_size": stats.st_size,
        "file_size_formatted": f"{stats.st_size / 1024:.1f} KB",
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "is_binary": ext not in ["txt", "md", "csv", "json"],
    }


class IndexManager:
    """Main index management class"""

    def __init__(self, data_dir: str = "data/uploads", session_id: str = None):
        # Configuration paths
        self.data_dir = data_dir
        self.session_id = session_id
        self.storage_dir = f"./storage/{session_id}" if session_id else "./storage"
        self.cache_dir = f"./cache/{session_id}" if session_id else "./cache"
        self.models_cache = os.path.join(os.path.dirname(__file__), "models")
        self.session_dir = (
            f"data/uploads/{session_id}" if session_id else "data/uploads"
        )

        # Model configuration
        self.model_name = "BAAI/bge-small-en"  # Changed model for better compatibility
        self.embedding_dimension = 384
        self.processed_files = set()
        self.index = None
        self.last_index_time = 0
        self.index_rebuild_interval = 300  # 5 minutes

        # Initialize directories
        for path in [
            self.session_dir,  # Add session-specific upload directory
            self.storage_dir,
            self.cache_dir,
            self.models_cache,
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)

        # Initialize components
        self._initialize_embedding_model()
        self._load_caches()

        # Configure global settings
        Settings.chunk_size = 512  # Smaller chunks for better retrieval
        Settings.chunk_overlap = 50
        Settings.num_output = 1024
        Settings.embed_model = self.embed_model

    def _initialize_embedding_model(self):
        """Initialize embedding model with correct parameters"""
        try:
            # Initialize embedding model directly without SentenceTransformer
            self.embed_model = HuggingFaceEmbedding(
                model_name=self.model_name,
                cache_folder=self.models_cache,
                embed_batch_size=32,
            )
            Settings.embed_model = self.embed_model
            logger.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            logger.warning("Using basic fallback embedding")
            self.embed_model = BasicEmbedding()
            Settings.embed_model = self.embed_model

    def _load_caches(self):
        """Load cached data"""
        self.embedding_cache_file = Path(self.cache_dir) / "embeddings.pkl"
        self.index_cache_file = Path(self.cache_dir) / "index.pkl"

        try:
            if self.embedding_cache_file.exists():
                with open(self.embedding_cache_file, "rb") as f:
                    self._embedding_cache = pickle.load(f)
            else:
                self._embedding_cache = {}

            if self.index_cache_file.exists():
                with open(self.index_cache_file, "rb") as f:
                    cache_data = pickle.load(f)
                    self.index = cache_data.get("index")
                    self.last_index_time = cache_data.get("timestamp", 0)
        except Exception as e:
            logger.error(f"Cache load error: {e}")
            self._embedding_cache = {}

    def _save_caches(self):
        """Persist cached data"""
        try:
            with open(self.embedding_cache_file, "wb") as f:
                pickle.dump(self._embedding_cache, f)

            if self.index:
                cache_data = {"index": self.index, "timestamp": time.time()}
                with open(self.index_cache_file, "wb") as f:
                    pickle.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Cache save error: {e}")

    def _should_rebuild(self) -> bool:
        """Determine if index needs rebuilding"""
        if not self.index:
            return True

        if time.time() - self.last_index_time > self.index_rebuild_interval:
            return True

        current_files = {f: self._get_file_hash(f) for f in os.listdir(self.data_dir)}
        cached_files = self._embedding_cache.get("file_hashes", {})
        return current_files != cached_files

    def _get_file_hash(self, filename: str) -> str:
        """Generate quick file hash"""
        path = os.path.join(self.data_dir, filename)
        stats = os.stat(path)
        return f"{stats.st_size}_{stats.st_mtime}"

    def build_index(self):
        """Build or rebuild vector index with improved multi-document handling."""
        try:
            logger.info("Starting index construction...")
            documents = []
            processed_count = 0
            failed_count = 0

            # Get files for this session from database
            from utils.database import ConversationDB

            db = ConversationDB()

            if not self.session_id:
                logger.error("No session_id provided")
                return

            session_files = db.get_conversation_files(self.session_id)

            if not session_files:
                logger.warning(f"No documents found for session {self.session_id}")
                return

            logger.info(
                f"Processing {len(session_files)} files for session {self.session_id}"
            )

            for file_path, file_name in session_files:
                try:
                    if not os.path.exists(file_path):
                        logger.error(f"File not found: {file_path}")
                        failed_count += 1
                        continue

                    if file_path.endswith(".json"):
                        docs = self._process_json_file(file_path)
                        if docs:
                            documents.extend(docs)
                            processed_count += 1
                    else:
                        reader = SimpleDirectoryReader(
                            input_files=[file_path],
                            file_metadata=get_file_metadata,
                            filename_as_id=True,
                            exclude_hidden=True,
                        )
                        docs = reader.load_data()
                        if docs:
                            documents.extend(docs)
                            processed_count += 1

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    failed_count += 1
                    continue

            logger.info(f"Successfully processed {processed_count} files")
            if failed_count > 0:
                logger.warning(f"Failed to process {failed_count} files")

            if not documents:
                logger.warning("No documents could be processed")
                return

            # Create index with improved settings
            storage_context = StorageContext.from_defaults()
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                transformations=[
                    SentenceSplitter(
                        chunk_size=Settings.chunk_size,
                        chunk_overlap=Settings.chunk_overlap,
                        separator=" ",
                        paragraph_separator="\n\n",
                    )
                ],
                embed_model=self.embed_model,
                show_progress=True,
            )

            # Persist index
            storage_context.persist(persist_dir=self.storage_dir)
            self.last_index_time = time.time()
            logger.info(f"Index built with {len(documents)} documents")

        except Exception as e:
            logger.error(f"Index build failed: {e}", exc_info=True)
            raise

    def _process_json_file(self, file_path: str):
        """Handle a single JSON document"""
        try:
            reader = JSONReader(levels_back=2, collapse_length=500)
            docs = reader.load_data(file_path)
            for doc in docs:
                doc.metadata.update(get_file_metadata(file_path))
            logger.info(f"Processed JSON file: {file_path}")
            return docs
        except Exception as e:
            logger.error(f"JSON error {file_path}: {e}")
            return []

    def _process_json_files(self):
        """Handle JSON documents - Deprecated, use _process_json_file instead"""
        return []

    def load_index(self):
        """Load existing index"""
        try:
            required_files = ["docstore.json", "vector_store.json"]
            if all((Path(self.storage_dir) / f).exists() for f in required_files):
                storage_context = StorageContext.from_defaults(
                    persist_dir=self.storage_dir
                )
                self.index = load_index_from_storage(storage_context)
                logger.info("Loaded existing index")
            else:
                logger.warning("Missing index files - rebuilding...")
                self.build_index()
        except Exception as e:
            logger.error(f"Index load error: {e}")
            self.build_index()

    def query_index(self, query: str, top_k: int = 5):
        """Execute search query with improved retrieval."""
        if not self.index or self._should_rebuild():
            self.build_index()

        try:
            # Create query engine with improved settings
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k,
                vector_store_kwargs={
                    "similarity_cutoff": 0.7,  # Only include relevant results
                    "distance_metric": "cosine",  # Use cosine similarity
                },
                response_mode="compact",
            )

            response = query_engine.query(query)
            nodes = getattr(response, "source_nodes", [])

            # Sort nodes by relevance score if available
            if nodes and hasattr(nodes[0], "score"):
                nodes = sorted(
                    nodes, key=lambda x: getattr(x, "score", 0), reverse=True
                )

            return nodes

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
