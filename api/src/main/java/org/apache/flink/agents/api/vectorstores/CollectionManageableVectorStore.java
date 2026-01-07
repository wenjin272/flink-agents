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

import java.util.Map;

/** Base abstract class for vector store which support collection management. */
public interface CollectionManageableVectorStore {

    class Collection {
        private final String name;
        private final Map<String, Object> metadata;

        public Collection(String name, Map<String, Object> metadata) {
            this.name = name;
            this.metadata = metadata;
        }

        public String getName() {
            return name;
        }

        public Map<String, Object> getMetadata() {
            return metadata;
        }
    }

    /**
     * Get a collection, or create it if it doesn't exist.
     *
     * @param name The name of the collection to get or create.
     * @param metadata The metadata of the collection.
     * @return The retrieved or created collection.
     */
    Collection getOrCreateCollection(String name, Map<String, Object> metadata) throws Exception;

    /**
     * Get a collection by name.
     *
     * @param name The name of the collection to get.
     * @return The retrieved collection.
     */
    Collection getCollection(String name) throws Exception;

    /**
     * Delete a collection by name.
     *
     * @param name The name of the collection to delete.
     * @return The deleted collection.
     */
    Collection deleteCollection(String name) throws Exception;
}
