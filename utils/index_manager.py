from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.groq import Groq
from llama_index.readers.json import JSONReader
import os


class IndexManager:
    def __init__(self, data_dir="data/uploads"):
        self.data_dir = data_dir
        self.storage_dir = "./storage"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.storage_dir, exist_ok=True)

        # Configure global settings
        Settings.llm = Groq(model="llama2-70b-4096", api_key=os.getenv("GROQ_API_KEY"))
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
        Settings.num_output = 512
        Settings.context_window = 4096

        self.index = None
        self.load_index()

    def build_index(self):
        """Builds the index from scratch."""
        if not os.listdir(self.data_dir):
            storage_context = StorageContext.from_defaults()
            self.index = VectorStoreIndex.from_documents(
                [],
                storage_context=storage_context,
            )
            storage_context.persist(persist_dir=self.storage_dir)
            return

        # Load non-JSON documents with all supported extensions
        reader = SimpleDirectoryReader(
            input_dir=self.data_dir,
            recursive=True,
            required_exts=[
                # Text and Documents
                ".txt",
                ".md",
                ".pdf",
                ".docx",
                # Presentations
                ".ppt",
                ".pptm",
                ".pptx",
                # Data files
                ".csv",
                # Ebooks
                ".epub",
                # Korean word processor
                ".hwp",
                # Jupyter notebooks
                ".ipynb",
                # Email archives
                ".mbox",
            ],
            file_metadata=lambda path: {
                "file_name": os.path.basename(path),
                "file_type": os.path.splitext(path)[1][1:],  # Extension without dot
                "file_size": os.path.getsize(path),
                "created_at": os.path.getctime(path),
                "modified_at": os.path.getmtime(path),
            },
        )
        try:
            documents = reader.load_data(num_workers=4)
        except Exception as e:
            print(f"Error loading documents: {e}")
            documents = []

        # Handle JSON files separately with JSONReader
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith(".json")]
        for json_file in json_files:
            json_reader = JSONReader(
                levels_back=2,  # Parse nested JSON up to 2 levels
                collapse_length=500,  # Collapse JSON fragments longer than 500 chars
                ensure_ascii=False,  # Keep non-ASCII characters
                clean_json=True,  # Remove unnecessary formatting
            )
            json_file_path = os.path.join(self.data_dir, json_file)
            try:
                json_docs = json_reader.load_data(json_file_path)
                for doc in json_docs:
                    doc.metadata = {"file_name": json_file}  # Add filename metadata
                documents.extend(json_docs)
            except Exception as e:
                print(f"Error processing JSON file {json_file}: {e}")

        # Create fresh storage context and build index
        storage_context = StorageContext.from_defaults()
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
        )
        storage_context.persist(persist_dir=self.storage_dir)

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

    def query_index(self, query):
        """Queries the index and returns the response."""
        if not self.index:
            raise ValueError("Index not initialized")

        query_engine = self.index.as_query_engine(
            similarity_top_k=3,
            response_mode="compact",
            llm=Settings.llm,  # Explicitly pass LLM
        )
        return query_engine.query(query)
