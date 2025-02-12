from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.json import JSONReader
import os
from typing import Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_file_metadata(path: str) -> Dict[str, Any]:
    """Get metadata for a file."""
    # Get file stats
    stats = os.stat(path)
    
    # Get file extension and determine file type category
    ext = os.path.splitext(path)[1][1:].lower()
    file_type_categories = {
        'text': ['txt', 'md'],
        'document': ['pdf', 'docx'],
        'presentation': ['ppt', 'pptm', 'pptx'],
        'spreadsheet': ['csv'],
        'ebook': ['epub'],
        'email': ['mbox'],
        'notebook': ['ipynb'],
        'korean_doc': ['hwp'],
        'data': ['json']
    }
    
    file_category = next(
        (category for category, exts in file_type_categories.items() if ext in exts),
        'other'
    )
    
    return {
        "file_name": os.path.basename(path),
        "file_type": ext,
        "file_category": file_category,
        "file_size": stats.st_size,
        "file_size_formatted": f"{stats.st_size / 1024:.1f} KB",
        "created_at": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        "is_binary": ext not in ['txt', 'md', 'csv', 'json'],
    }


class IndexManager:
    def __init__(self, data_dir="data/uploads"):
        self.data_dir = data_dir
        self.storage_dir = "./storage"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)

        # Configure global settings
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
        Settings.num_output = 512
        Settings.context_window = 4096

        self.index = None
        self.load_index()

    def build_index(self):
        """Builds the index from scratch."""
        if not os.listdir(self.data_dir):
            logger.info("No documents found in data directory")
            storage_context = StorageContext.from_defaults()
            self.index = VectorStoreIndex.from_documents(
                [], storage_context=storage_context
            )
            storage_context.persist(persist_dir=self.storage_dir)
            return

        try:
            # Load documents with metadata
            reader = SimpleDirectoryReader(
                input_dir=self.data_dir,
                recursive=True,
                required_exts=[
                    ".txt",
                    ".md",
                    ".pdf",
                    ".docx",
                    ".ppt",
                    ".pptm",
                    ".pptx",
                    ".csv",
                    ".epub",
                    ".hwp",
                    ".ipynb",
                    ".mbox",
                    ".json",
                ],
                file_metadata=get_file_metadata,
                filename_as_id=True,  # Use filename as document ID
            )

            logger.info(f"Loading documents from {self.data_dir}")
            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents")

            # Handle JSON files separately
            json_documents = self._process_json_files()
            if json_documents:
                documents.extend(json_documents)

            # Create fresh storage context with better chunking
            storage_context = StorageContext.from_defaults()

            # Build index with proper configuration
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=True,  # Show progress bar
                embed_model=Settings.embed_model,
            )

            # Persist the index
            storage_context.persist(persist_dir=self.storage_dir)
            logger.info("Index built and persisted successfully")

        except Exception as e:
            logger.error(f"Error building index: {e}")
            raise

    def _process_json_files(self):
        """Process JSON files separately."""
        json_documents = []
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith(".json")]

        for json_file in json_files:
            try:
                json_reader = JSONReader(
                    levels_back=2,
                    collapse_length=500,
                    ensure_ascii=False,
                    clean_json=True,
                )
                json_path = os.path.join(self.data_dir, json_file)
                docs = json_reader.load_data(json_path)

                # Add metadata to JSON documents
                for doc in docs:
                    doc.metadata.update(get_file_metadata(json_path))

                json_documents.extend(docs)
                logger.info(f"Processed JSON file: {json_file}")
            except Exception as e:
                logger.error(f"Error processing JSON file {json_file}: {e}")

        return json_documents

    def load_index(self):
        """Loads the index from disk or builds it if it doesn't exist."""
        try:
            if os.path.exists(self.storage_dir):
                storage_context = StorageContext.from_defaults(
                    persist_dir=self.storage_dir
                )
                self.index = load_index_from_storage(storage_context)
            else:
                self.build_index()
        except Exception as e:
            print(f"Error loading index: {e}")
            self.build_index()

    def query_index(self, query_text: str, similarity_top_k: int = 3):
        """
        Query the index with improved metadata handling.
        Returns the most relevant nodes with their metadata.
        """
        if not self.index:
            logger.warning("No index available for querying")
            return []

        try:
            # Retrieve relevant nodes
            query_engine = self.index.as_query_engine(
                similarity_top_k=similarity_top_k,
                response_mode="no_text",  # We'll handle the response formatting
            )
            response = query_engine.query(query_text)
            
            # Get source nodes with metadata
            source_nodes = response.source_nodes
            
            # Log retrieved documents for debugging
            logger.info(f"Retrieved {len(source_nodes)} relevant documents")
            for node in source_nodes:
                logger.info(f"Document: {node.metadata.get('file_name')} "
                          f"(Score: {node.score:.3f})")
            
            return source_nodes

        except Exception as e:
            logger.error(f"Error querying index: {e}")
            return []
