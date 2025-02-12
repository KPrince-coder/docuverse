import os
import time
import logging
import pickle
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import requests.exceptions
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

    def __init__(self, data_dir: str = "data/uploads"):
        # Configuration paths
        self.data_dir = data_dir
        self.storage_dir = "./storage"
        self.cache_dir = "./cache"
        self.models_cache = os.path.join(os.path.dirname(__file__), "models")

        # Model configuration
        self.model_name = "BAAI/bge-small-en"  # Changed model for better compatibility
        self.embedding_dimension = 384
        self.processed_files = set()
        self.index = None
        self.last_index_time = 0
        self.index_rebuild_interval = 300  # 5 minutes

        # Initialize directories
        for path in [
            self.data_dir,
            self.storage_dir,
            self.cache_dir,
            self.models_cache,
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)

        # Initialize components
        self._initialize_embedding_model()
        self._load_caches()

        # Configure global settings
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 50
        Settings.num_output = 512
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
        """Build or rebuild vector index"""
        try:
            logger.info("Starting index construction...")

            # Clear existing index
            if Path(self.storage_dir).exists():
                shutil.rmtree(self.storage_dir)
            Path(self.storage_dir).mkdir()

            # Load documents
            reader = SimpleDirectoryReader(
                self.data_dir,
                file_metadata=get_file_metadata,
                filename_as_id=True,
                exclude_hidden=True,
            )
            documents = reader.load_data()
            documents += self._process_json_files()

            if not documents:
                logger.warning("No documents found for indexing")
                return

            # Create index
            storage_context = StorageContext.from_defaults()
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                transformations=[
                    SentenceSplitter(
                        chunk_size=Settings.chunk_size,
                        chunk_overlap=Settings.chunk_overlap,
                    )
                ],
                embed_model=self.embed_model,
            )

            # Persist index
            storage_context.persist(persist_dir=self.storage_dir)
            self.last_index_time = time.time()
            logger.info(f"Index built with {len(documents)} documents")

        except Exception as e:
            logger.error(f"Index build failed: {e}")
            raise

    def _process_json_files(self):
        """Handle JSON documents"""
        json_docs = []
        for fname in os.listdir(self.data_dir):
            if fname.endswith(".json"):
                try:
                    reader = JSONReader(levels_back=2, collapse_length=500)
                    docs = reader.load_data(os.path.join(self.data_dir, fname))
                    for doc in docs:
                        doc.metadata.update(get_file_metadata(fname))
                    json_docs.extend(docs)
                    logger.info(f"Processed JSON file: {fname}")
                except Exception as e:
                    logger.error(f"JSON error {fname}: {e}")
        return json_docs

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

    def query_index(self, query: str, top_k: int = 3):
        """Execute search query"""
        if not self.index or self._should_rebuild():
            self.build_index()

        try:
            query_engine = self.index.as_query_engine(
                similarity_top_k=top_k, response_mode="compact"
            )
            response = query_engine.query(query)
            return getattr(response, "source_nodes", [])
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
