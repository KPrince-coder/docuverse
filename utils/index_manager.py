from llama_index import GPTSimpleVectorIndex, SimpleDirectoryReader
from llama_index.readers.json import JSONReader
import os


class IndexManager:
    def __init__(self, data_dir="data/uploads"):
        self.data_dir = data_dir
        self.index = None
        self.load_index()

    def build_index(self):
        """Builds the index from scratch."""

        # Define a metadata extraction function
        def get_file_metadata(file_path):
            return {
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "timestamp": os.path.getmtime(file_path),
            }

        # Load documents with metadata and parallel processing
        reader = SimpleDirectoryReader(
            input_dir=self.data_dir,
            recursive=True,
            required_exts=[".pdf", ".docx", ".pptx", ".txt", ".csv"],
            file_metadata=get_file_metadata,
            num_workers=4,  # Enable parallel processing
        )
        documents = reader.load_data()

        # Handle JSON files separately using JSONReader
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith(".json")]
        for json_file in json_files:
            json_reader = JSONReader(
                levels_back=2,  # Traverse up to 2 levels back in the JSON tree
                collapse_length=500,  # Collapse JSON fragments longer than 500 characters
                ensure_ascii=False,  # Keep non-ASCII characters
                clean_json=True,  # Remove unnecessary formatting lines
            )
            json_file_path = os.path.join(self.data_dir, json_file)
            json_documents = json_reader.load_data(
                input_file=json_file_path, extra_info={"file_name": json_file}
            )
            documents.extend(json_documents)

        self.index = GPTSimpleVectorIndex(documents)
        self.index.save_to_disk("index.json")

    def load_index(self):
        """Loads the index from disk or builds it if it doesn't exist."""
        if not os.path.exists("index.json"):
            self.build_index()
        else:
            self.index = GPTSimpleVectorIndex.load_from_disk("index.json")

    def rebuild_index_after_deletion(self):
        """Rebuilds the index after deleting files."""
        self.build_index()

    def query_index(self, query):
        """Queries the index and returns the response."""
        return self.index.query(query)
