/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.agents.api.vectorstores;

import org.apache.flink.agents.api.embedding.model.BaseEmbeddingModelSetup;
import org.apache.flink.agents.api.resource.Resource;
import org.apache.flink.agents.api.resource.ResourceDescriptor;
import org.apache.flink.agents.api.resource.ResourceType;

import javax.annotation.Nullable;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.function.BiFunction;

/**
 * Base abstract class for vector store. Provides vector store functionality that integrates
 * embedding models for text-based semantic search. Handles both connection management and embedding
 * generation internally.
 */
public abstract class BaseVectorStore extends Resource {

    /** Name of the embedding model resource to use. */
    protected final String embeddingModel;

    public BaseVectorStore(
            ResourceDescriptor descriptor, BiFunction<String, ResourceType, Resource> getResource) {
        super(descriptor, getResource);
        this.embeddingModel = descriptor.getArgument("embedding_model");
    }

    @Override
    public ResourceType getResourceType() {
        return ResourceType.VECTOR_STORE;
    }

    /**
     * Returns vector store setup settings passed to connection. These parameters are merged with
     * query-specific parameters when performing vector search operations.
     *
     * @return A map containing the store configuration parameters
     */
    public abstract Map<String, Object> getStoreKwargs();

    /**
     * Add documents to vector store.
     *
     * @param documents The documents to be added.
     * @param collection The name of the collection to add to. If is null, will add documents to the
     *     default collection.
     * @param extraArgs The vector store specific arguments.
     * @return The IDs of the documents added.
     */
    public List<String> add(
            List<Document> documents, @Nullable String collection, Map<String, Object> extraArgs)
            throws IOException {
        final BaseEmbeddingModelSetup embeddingModel =
                (BaseEmbeddingModelSetup)
                        this.getResource.apply(this.embeddingModel, ResourceType.EMBEDDING_MODEL);

        for (Document doc : documents) {
            if (doc.getEmbedding() == null) {
                doc.setEmbedding(embeddingModel.embed(doc.getContent()));
            }
        }

        final Map<String, Object> storeKwargs = this.getStoreKwargs();
        storeKwargs.putAll(extraArgs);

        return this.addEmbedding(documents, collection, extraArgs);
    }

    /**
     * Performs vector search using structured query object. Converts text query to embeddings and
     * returns structured query result.
     *
     * @param query VectorStoreQuery object containing query parameters
     * @return VectorStoreQueryResult containing the retrieved documents
     */
    public VectorStoreQueryResult query(VectorStoreQuery query) {
        final BaseEmbeddingModelSetup embeddingModel =
                (BaseEmbeddingModelSetup)
                        this.getResource.apply(this.embeddingModel, ResourceType.EMBEDDING_MODEL);

        final float[] queryEmbedding = embeddingModel.embed(query.getQueryText());

        final Map<String, Object> storeKwargs = this.getStoreKwargs();
        storeKwargs.putAll(query.getExtraArgs());

        final List<Document> documents =
                this.queryEmbedding(
                        queryEmbedding, query.getLimit(), query.getCollection(), storeKwargs);

        return new VectorStoreQueryResult(documents);
    }

    /**
     * Get the size of the collection in vector store.
     *
     * @param collection The name of the collection to count. If is null, count the default
     *     collection.
     * @return The documents count in the collection.
     */
    public abstract long size(@Nullable String collection) throws Exception;

    /**
     * Retrieve documents from the vector store.
     *
     * @param ids The ids of the documents. If is null, get all the documents or first n documents
     *     according to implementation specific limit.
     * @param collection The name of the collection to be retrieved. If is null, retrieve the
     *     default collection.
     * @param extraArgs Additional arguments.
     * @return List of documents retrieved.
     */
    public abstract List<Document> get(
            @Nullable List<String> ids, @Nullable String collection, Map<String, Object> extraArgs)
            throws IOException;

    /**
     * Delete documents in the vector store.
     *
     * @param ids The ids of the documents. If is null, delete all the documents.
     * @param collection The name of the collection the documents belong to. If is null, use the
     *     default collection.
     * @param extraArgs Additional arguments.
     */
    public abstract void delete(
            @Nullable List<String> ids, @Nullable String collection, Map<String, Object> extraArgs)
            throws IOException;

    /**
     * Performs vector search using a pre-computed embedding.
     *
     * @param embedding The embedding vector to search with
     * @param limit Maximum number of results to return
     * @param collection The collection to query to. If is null, query the default collection.
     * @param args Additional arguments for the vector search
     * @return List of documents matching the query embedding
     */
    protected abstract List<Document> queryEmbedding(
            float[] embedding, int limit, @Nullable String collection, Map<String, Object> args);

    /**
     * Add documents with pre-computed embedding to vector store.
     *
     * @param documents The documents to be added.
     * @param collection The name of the collection to add to. If is null, add to the default
     *     collection.
     * @param extraArgs Additional arguments.
     * @return IDs of the added documents.
     */
    protected abstract List<String> addEmbedding(
            List<Document> documents, @Nullable String collection, Map<String, Object> extraArgs)
            throws IOException;
}
