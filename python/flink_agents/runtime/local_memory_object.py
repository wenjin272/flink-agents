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
from typing import Any, Dict, List, ClassVar

from pydantic import PrivateAttr

from flink_agents.api.memoryobject import MemoryObject

class _ObjMarker:
    """
    Internal marker for an object node.

    children : set[str] keeps all subfield names
    """
    __slots__ = ("children",)

    def __init__(self):
        self.children: set[str] = set()

    def __repr__(self) -> str:  # debug friendly
        return f"_ObjMarker({sorted(self.children)})"

class LocalMemoryObject(MemoryObject):
    """
    LocalMemoryObject: Flattened hierarchical key-value store for local python execution.

    Each object keeps a prefix to represent its path.
    """
    ROOT_KEY: ClassVar[str] = ""
    NESTED_MARK: ClassVar[str] = "NestedObject"

    _store: Dict[str, Any] = PrivateAttr()
    _prefix: str = PrivateAttr()

    def __init__(self, store: Dict[str, Any] | None = None, prefix: str = ""):
        """
        Initialize a memory object with the shared store and prefix.
        """
        super().__init__()
        self._store = store if store is not None else {} # shared flattened map
        self._prefix = prefix # current object prefix path

        # make sure root exists and is an object
        if self.ROOT_KEY not in self._store:
            self._store[self.ROOT_KEY] = _ObjMarker()

    # def __init__(self, store: dict, prefix: str = ""):
    #     """
    #     Initialize a memory object with the shared store and prefix.
    #     """
    #     self._store = store  # shared flattened map
    #     self._prefix = prefix  # current object prefix path

    def get(self, path: str) -> Any:
        """
        Get a value by relative path.
        If the field is an object, return a new LocalMemoryObject.
        """
        abs_path = self._full_path(path)
        if abs_path in self._store:
            value = self._store[abs_path]
            if self._is_nested_object(value):
                return LocalMemoryObject(self._store, abs_path)
            return value
        return None

    def set(self, path: str, value: Any):
        if isinstance(value, LocalMemoryObject):
            raise ValueError("Do not set a MemoryObject instance directly; use new_object().")

        abs_path = self._full_path(path)
        parts = abs_path.split(".")

        self._fill_parents(parts)

        parent_path = ".".join(parts[:-1]) if len(parts) > 1 else self.ROOT_KEY
        self._add_child(parent_path, parts[-1])

        if abs_path in self._store and self._is_nested_object(self._store[abs_path]):
            raise ValueError(f"Cannot overwrite object field '{abs_path}' with primitive.")

        self._store[abs_path] = value

    def new_object(self, path: str, overwrite: bool = False) -> 'LocalMemoryObject':
        abs_path = self._full_path(path)
        parts = abs_path.split(".")

        self._fill_parents(parts)

        parent_path = ".".join(parts[:-1]) if len(parts) > 1 else self.ROOT_KEY
        self._add_child(parent_path, parts[-1])

        # 2. Conflict checks
        if abs_path in self._store and not self._is_nested_object(self._store[abs_path]):
            if not overwrite:
                raise ValueError(f"Field '{abs_path}' exists but is not object.")

        # 3. Create / overwrite as object
        self._store[abs_path] = _ObjMarker()
        return LocalMemoryObject(self._store, abs_path)

    def is_exist(self, path: str) -> bool:
        """
        Check if a path exists.
        """
        return self._full_path(path) in self._store

    def get_field_names(self) -> List[str]:
        """
        Get all direct field names of the current object.
        """
        marker = self._store.get(self._prefix)
        if self._is_nested_object(marker):
            return sorted(marker.children)
        return []

    def get_fields(self) -> Dict[str, Any]:
        """
        Get all direct fields and their values.
        If a field is an object, return a placeholder with its children.
        """
        result = {}
        for name in self.get_field_names():
            abs_path = self._full_path(name)
            value = self._store[abs_path]
            result[name] = self.NESTED_MARK if self._is_nested_object(value) else value
        return result

    # ---- path helpers --------------------------------------------------
    def _full_path(self, rel: str) -> str:
        return f"{self._prefix}.{rel}".strip(".") if rel else self._prefix

    @staticmethod
    def _is_nested_object(value: Any) -> bool:
        return isinstance(value, _ObjMarker)

    # ---- object-node helpers ------------------------------------------
    def _ensure_object_node(self, path: str) -> '_ObjMarker':
        """
        Ensure the given path exists in store *as an object* and return marker.
        """
        if path not in self._store or not self._is_nested_object(self._store[path]):
            self._store[path] = _ObjMarker()
        return self._store[path]

    def _add_child(self, parent: str, child: str):
        """
        Register `child` to parent's children-set. Parent becomes object if needed.
        """
        self._ensure_object_node(parent).children.add(child)

    def _fill_parents(self, parts: List[str]):
        """
        Ensure every ancestor (except leaf) exists and children sets contain the path.
        """
        for i in range(1, len(parts)):
            parent_path = ".".join(parts[:i - 1]) if i > 1 else self.ROOT_KEY
            cur_path = ".".join(parts[:i])
            # create / ensure object node for current path
            self._ensure_object_node(cur_path)
            # register current name in parent's children list
            self._add_child(parent_path, parts[i - 1])

