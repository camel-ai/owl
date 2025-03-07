import re
import uuid
from typing import (
    TYPE_CHECKING,
    Collection,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from camel.embeddings import BaseEmbedding, OpenAIEmbedding
from camel.retrievers.vector_retriever import VectorRetriever
from camel.storages import (
    BaseVectorStorage,
    MilvusStorage,
    QdrantStorage,
)
from camel.types import StorageType
from camel.utils import Constants

if TYPE_CHECKING:
    from unstructured.documents.elements import Element
