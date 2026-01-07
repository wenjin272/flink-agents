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

package org.apache.flink.agents.integrations.vectorstores.elasticsearch;

import org.apache.flink.agents.api.embedding.model.BaseEmbeddingModelSetup;
import org.apache.flink.agents.api.resource.Resource;
import org.apache.flink.agents.api.resource.ResourceDescriptor;
import org.apache.flink.agents.api.resource.ResourceType;
import org.apache.flink.agents.api.vectorstores.BaseVectorStore;
import org.apache.flink.agents.api.vectorstores.CollectionManageableVectorStore;
import org.apache.flink.agents.api.vectorstores.CollectionManageableVectorStore.Collection;
import org.apache.flink.agents.api.vectorstores.Document;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Test for {@link ElasticsearchVectorStore}
 *
 * <p>Need setup Elasticsearch server to run this test. Look <a
 * href="https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-basic">Start
 * a single-node cluster in Docker</a> for details.
 *
 * <p>For {@link ElasticsearchVectorStore} doesn't support security check yet, when start the
 * container, should add "-e xpack.security.enabled=false" option.
 */
@Disabled("Should setup Elasticsearch server.")
public class ElasticsearchVectorStoreTest {
    public static BaseVectorStore store;

    public static Resource getResource(String name, ResourceType type) {
        BaseEmbeddingModelSetup embeddingModel = Mockito.mock(BaseEmbeddingModelSetup.class);
        Mockito.when(embeddingModel.embed("Elasticsearch is a search engine"))
                .thenReturn(new float[] {0.2f, 0.3f, 0.4f, 0.5f, 0.6f});
        Mockito.when(
                        embeddingModel.embed(
                                "Apache Flink Agents is an Agentic AI framework based on Apache Flink."))
                .thenReturn(new float[] {0.1f, 0.2f, 0.3f, 0.4f, 0.5f});
        return embeddingModel;
    }

    @BeforeAll
    public static void initialize() {
        final ResourceDescriptor.Builder builder =
                ResourceDescriptor.Builder.newBuilder(ElasticsearchVectorStore.class.getName())
                        .addInitialArgument("embedding_model", "embeddingModel")
                        .addInitialArgument("host", "localhost:9200")
                        .addInitialArgument("dims", 5)
                        .addInitialArgument("username", "elastic")
                        .addInitialArgument("password", System.getenv("ES_PASSWORD"));
        ;
        store =
                new ElasticsearchVectorStore(
                        builder.build(), ElasticsearchVectorStoreTest::getResource);
    }

    @Test
    public void testCollectionManagement() throws Exception {
        CollectionManageableVectorStore vectorStore = (CollectionManageableVectorStore) store;
        String name = "collection_management";
        Map<String, Object> metadata = Map.of("key1", "value1", "key2", "value2");
        vectorStore.getOrCreateCollection(name, metadata);

        Collection collection = vectorStore.getCollection(name);

        Assertions.assertNotNull(collection);
        Assertions.assertEquals(name, collection.getName());
        Assertions.assertEquals(0, store.size(name));
        Assertions.assertEquals(metadata, collection.getMetadata());

        vectorStore.deleteCollection(name);

        Assertions.assertThrows(
                RuntimeException.class,
                () -> vectorStore.getCollection(name),
                String.format("Collection %s not found", name));
    }

    @Test
    public void testDocumentManagement() throws Exception {
        String name = "document_management";
        Map<String, Object> metadata = Map.of("key1", "value1", "key2", "value2");
        ((CollectionManageableVectorStore) store).getOrCreateCollection(name, metadata);

        List<Document> documents = new ArrayList<>();
        documents.add(
                new Document(
                        "Elasticsearch is a search engine",
                        Map.of("category", "database", "source", "test"),
                        "doc1"));
        documents.add(
                new Document(
                        "Apache Flink Agents is an Agentic AI framework based on Apache Flink.",
                        Map.of("category", "ai-agent", "source", "test"),
                        "doc2"));
        store.add(documents, name, Collections.emptyMap());
        // wait for the documents to become visible in the elasticsearch server.
        Thread.sleep(1000);
        for (Document doc : documents) {
            doc.setEmbedding(null);
        }

        // test get all documents
        List<Document> all = store.get(null, name, Collections.emptyMap());
        Assertions.assertEquals(documents, all);

        // test get specific document
        List<Document> specific =
                store.get(Collections.singletonList("doc1"), name, Collections.emptyMap());
        Assertions.assertEquals(1, specific.size());
        Assertions.assertEquals(documents.get(0), specific.get(0));

        // test delete specific document
        store.delete(Collections.singletonList("doc1"), name, Collections.emptyMap());
        Thread.sleep(1000);
        List<Document> remain = store.get(null, name, Collections.emptyMap());
        Assertions.assertEquals(1, remain.size());
        Assertions.assertEquals(documents.get(1), remain.get(0));

        // test delete all documents
        store.delete(null, name, Collections.emptyMap());
        Thread.sleep(1000);
        List<Document> empty = store.get(null, name, Collections.emptyMap());
        Assertions.assertTrue(empty.isEmpty());

        ((CollectionManageableVectorStore) store).deleteCollection(name);
    }
}
