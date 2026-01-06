"""
RAG (Retrieval-Augmented Generation) system for ClauseCraft
Manages clause storage, embeddings, and semantic retrieval
"""
import uuid
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from config import CHROMA_DB_PATH, EMBEDDING_MODEL, TOP_K_SIMILAR_CLAUSES


class ClauseStore:
    """
    Manages the RAG knowledge base for lease clauses.

    Features:
    - Stores clauses with metadata (label, confidence, source document)
    - Automatically generates embeddings using sentence-transformers
    - Enables semantic search for similar clauses
    - Persistent storage with ChromaDB
    - Filtering by clause type (label)
    """

    def __init__(self, persist_directory: str = CHROMA_DB_PATH):
        """
        Initialize the clause store with ChromaDB and embedding model.

        Args:
            persist_directory: Path where ChromaDB will store data

        Note:
            First run downloads ~400MB sentence-transformers model (1-2 minutes)
        """
        print(f"🔧 Initializing RAG system...")
        print(f"📁 ChromaDB path: {persist_directory}")

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Initialize embedding model (runs locally)
        print(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")
        print("   (First time may take 1-2 minutes to download ~400MB model)")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Embedding model loaded!")

        # Get or create collection
        self.collection = self._get_or_create_collection()

        # Get current stats
        count = self.collection.count()
        print(f"📊 Loaded {count} existing clauses from knowledge base")

    def _get_or_create_collection(self):
        """
        Get existing collection or create new one.

        Returns:
            ChromaDB collection object
        """
        try:
            return self.client.get_collection("lease_clauses")
        except:
            return self.client.create_collection(
                name="lease_clauses",
                metadata={"description": "Lease agreement clauses with classifications"}
            )

    def add_clause(self, clause_data: dict) -> str:
        """
        Add a single clause to the knowledge base.

        Args:
            clause_data: Dictionary containing:
                - text (required): The clause text
                - label (required): Classification label
                - confidence (required): Classification confidence
                - clause_id (optional): Unique ID (auto-generated if not provided)
                - source_doc (optional): Source document filename
                - timestamp (optional): When clause was added

        Returns:
            clause_id: The unique ID assigned to this clause

        Example:
            >>> clause_store.add_clause({
            ...     "text": "The tenant shall pay rent monthly",
            ...     "label": "term_of_payment",
            ...     "confidence": 0.95,
            ...     "source_doc": "lease_001.pdf"
            ... })
        """
        clause_id = clause_data.get("clause_id", str(uuid.uuid4()))

        # Generate embedding
        embedding = self.embedding_model.encode(
            clause_data["text"],
            convert_to_tensor=False
        ).tolist()

        # Store in ChromaDB
        self.collection.add(
            ids=[clause_id],
            embeddings=[embedding],
            documents=[clause_data["text"]],
            metadatas=[{
                "label": clause_data["label"],
                "confidence": float(clause_data["confidence"]),
                "source_doc": clause_data.get("source_doc", ""),
                "timestamp": clause_data.get("timestamp", "")
            }]
        )

        return clause_id

    def add_clauses_batch(self, clauses: List[dict]) -> List[str]:
        """
        Add multiple clauses efficiently in batch mode.

        This is much faster than calling add_clause() repeatedly because:
        - Embeddings are generated in batch
        - Database writes are batched

        Args:
            clauses: List of clause dictionaries (same format as add_clause)

        Returns:
            List of clause IDs

        Example:
            >>> clauses = [
            ...     {"text": "Clause 1...", "label": "lessee", "confidence": 0.9},
            ...     {"text": "Clause 2...", "label": "lessor", "confidence": 0.95},
            ... ]
            >>> clause_ids = clause_store.add_clauses_batch(clauses)
        """
        if not clauses:
            return []

        clause_ids = [c.get("clause_id", str(uuid.uuid4())) for c in clauses]
        texts = [c["text"] for c in clauses]

        # Batch encode for efficiency
        print(f"🔄 Generating embeddings for {len(clauses)} clauses...")
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_tensor=False,
            show_progress_bar=True
        ).tolist()

        metadatas = [{
            "label": c["label"],
            "confidence": float(c["confidence"]),
            "source_doc": c.get("source_doc", ""),
            "timestamp": c.get("timestamp", "")
        } for c in clauses]

        # Batch insert
        print(f"💾 Storing {len(clauses)} clauses in ChromaDB...")
        self.collection.add(
            ids=clause_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"✅ Successfully stored {len(clauses)} clauses!")
        return clause_ids

    def retrieve_similar_clauses(
        self,
        query: str,
        top_k: int = TOP_K_SIMILAR_CLAUSES,
        label_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve clauses similar to the query using semantic search.

        Args:
            query: The query text (typically a clause to find similar examples for)
            top_k: Number of similar clauses to return
            label_filter: Optional filter by clause type (e.g., "redflag")

        Returns:
            List of dictionaries containing:
                - clause_id: Unique clause ID
                - text: The clause text
                - distance: Similarity distance (lower = more similar)
                - metadata: Dict with label, confidence, source_doc, timestamp

        Example:
            >>> similar = clause_store.retrieve_similar_clauses(
            ...     "The rent can be increased by 50% annually",
            ...     top_k=3,
            ...     label_filter="redflag"
            ... )
            >>> for clause in similar:
            ...     print(f"Found: {clause['text'][:50]}...")
            ...     print(f"Label: {clause['metadata']['label']}")
            ...     print(f"Similarity: {clause['distance']:.3f}")
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_tensor=False
        ).tolist()

        # Build filter if label specified
        where_filter = {"label": label_filter} if label_filter else None

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),  # Don't request more than available
            where=where_filter
        )

        # Format results
        similar_clauses = []
        if results['ids'] and results['ids'][0]:  # Check if results exist
            for i in range(len(results['ids'][0])):
                similar_clauses.append({
                    "clause_id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "distance": results['distances'][0][i],
                    "metadata": results['metadatas'][0][i]
                })

        return similar_clauses

    def get_clause_by_id(self, clause_id: str) -> Optional[Dict]:
        """
        Retrieve a specific clause by its unique ID.

        Args:
            clause_id: The unique clause identifier

        Returns:
            Dictionary with clause info, or None if not found
        """
        results = self.collection.get(ids=[clause_id])
        if not results['ids']:
            return None

        return {
            "clause_id": results['ids'][0],
            "text": results['documents'][0],
            "metadata": results['metadatas'][0]
        }

    def get_clauses_by_label(self, label: str, limit: int = 50) -> List[Dict]:
        """
        Retrieve all clauses with a specific classification label.

        Args:
            label: The clause type (e.g., "redflag", "term_of_payment")
            limit: Maximum number of clauses to return

        Returns:
            List of clause dictionaries

        Example:
            >>> all_redflags = clause_store.get_clauses_by_label("redflag")
            >>> print(f"Found {len(all_redflags)} red flag clauses")
        """
        results = self.collection.get(
            where={"label": label},
            limit=limit
        )

        clauses = []
        for i in range(len(results['ids'])):
            clauses.append({
                "clause_id": results['ids'][i],
                "text": results['documents'][i],
                "metadata": results['metadatas'][i]
            })

        return clauses

    def get_statistics(self) -> Dict:
        """
        Get statistics about the clause knowledge base.

        Returns:
            Dictionary with:
                - total_clauses: Total number of clauses stored
                - collection_name: Name of the ChromaDB collection
        """
        return {
            "total_clauses": self.collection.count(),
            "collection_name": self.collection.name
        }

    def clear_all(self):
        """
        Clear all clauses from the knowledge base.

        WARNING: This deletes all stored data. Use only for testing/reset.
        """
        self.client.delete_collection("lease_clauses")
        self.collection = self._get_or_create_collection()
        print("🗑️ All clauses cleared from knowledge base")
