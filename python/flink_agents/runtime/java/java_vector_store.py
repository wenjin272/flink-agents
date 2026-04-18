################################################################################
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
# limitations under the License.
#################################################################################

from typing import Any, Dict, List

from typing_extensions import override

from flink_agents.api.vector_stores.java_vector_store import (
    JavaCollectionManageableVectorStore,
)
from flink_agents.api.vector_stores.vector_store import (
    Document,
    VectorStoreQuery,
    VectorStoreQueryResult,
    _maybe_cast_to_list,
)
from flink_agents.runtime.python_java_utils import (
    from_java_document,
    from_java_vector_store_query_result,
)

_PRIVATE_HOOK_MSG = (
    "Protected embedding hooks are never called on the Java wrapper; "
    "public methods forward directly to the Java resource."
)


class JavaVectorStoreImpl(JavaCollectionManageableVectorStore):
    """Java-based implementation of EmbeddingModelSetup that wraps a Java embedding
    model object.
    This class serves as a bridge between Python and Java embedding model environments,
    but unlike JavaEmbeddingModelConnection, it does not provide direct embedding
    functionality in Python.
    """

    _j_resource: Any
    _j_resource_adapter: Any

    def __init__(self, j_resource: Any, j_resource_adapter: Any, **kwargs: Any) -> None:
        """Creates a new JavaEmbeddingModelSetup.

        Args:
            j_resource: The Java resource object
            j_resource_adapter: The Java resource adapter for method invocation
            **kwargs: Additional keyword arguments
        """
        # embedding_model are required parameters for BaseVectorStore
        embedding_model = kwargs.pop("embedding_model", "")
        super().__init__(embedding_model=embedding_model, **kwargs)

        self._j_resource = j_resource
        self._j_resource_adapter = j_resource_adapter

    @property
    @override
    def store_kwargs(self) -> Dict[str, Any]:
        return {}

    @override
    def open(self) -> None:
        self._j_resource.open()

    @override
    def add(
        self,
        documents: Document | List[Document],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> List[str]:
        documents = _maybe_cast_to_list(documents)
        j_documents = [
            self._j_resource_adapter.fromPythonDocument(document)
            for document in documents
        ]

        return self._j_resource.add(j_documents, collection_name, kwargs)

    @override
    def query(self, query: VectorStoreQuery) -> VectorStoreQueryResult:
        j_query = self._j_resource_adapter.fromPythonVectorStoreQuery(query)
        j_query_result = self._j_resource.query(j_query)
        return from_java_vector_store_query_result(j_query_result)

    def size(self, collection_name: str | None = None) -> int:
        """Return document count, forwarded to the underlying Java store.

        Java-side convenience; not part of :class:`BaseVectorStore`'s
        contract.
        """
        return self._j_resource.size(collection_name)

    @override
    def get(
        self,
        ids: str | List[str] | None = None,
        collection_name: str | None = None,
        filters: Dict[str, Any] | None = None,
        limit: int | None = 100,
        **kwargs: Any,
    ) -> List[Document]:
        ids = _maybe_cast_to_list(ids)
        if filters is not None:
            kwargs = {**kwargs, "filters": filters}
        if limit is not None:
            kwargs = {**kwargs, "limit": limit}
        j_documents = self._j_resource.get(ids, collection_name, kwargs)
        return [from_java_document(j_document) for j_document in j_documents]

    @override
    def delete(
        self,
        ids: str | List[str] | None = None,
        collection_name: str | None = None,
        filters: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> List[str]:
        ids = _maybe_cast_to_list(ids)
        if filters is not None:
            kwargs = {**kwargs, "filters": filters}
        return self._j_resource.delete(ids, collection_name, kwargs)

    @override
    def update(
        self,
        documents: Document | List[Document],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        err_msg = (
            "Update is not yet supported on the Java VectorStore wrapper. "
            "Implement it on the Java side first."
        )
        raise NotImplementedError(err_msg)

    @override
    def create_collection_if_not_exists(self, name: str, **kwargs: Any) -> None:
        """Forward to the Java side. Currently only ``metadata`` is forwarded;
        the Java API will be widened in a follow-up PR.
        """
        metadata = kwargs.get("metadata")
        self._j_resource.getOrCreateCollection(name, metadata)

    @override
    def delete_collection(self, name: str) -> None:
        self._j_resource.deleteCollection(name)

    @override
    def _add_embedding(
        self,
        *,
        documents: List[Document],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> List[str]:
        raise NotImplementedError(_PRIVATE_HOOK_MSG)

    @override
    def _query_embedding(
        self, embedding: list[float], limit: int = 10, **kwargs: Any
    ) -> list[Document]:
        raise NotImplementedError(_PRIVATE_HOOK_MSG)

    @override
    def _update_embedding(
        self,
        *,
        documents: List[Document],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError(_PRIVATE_HOOK_MSG)
