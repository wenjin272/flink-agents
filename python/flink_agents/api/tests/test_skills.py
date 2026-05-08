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
"""Tests for the Skills resource API."""

from flink_agents.api.skills import Skills


class TestSkillsFactories:
    def test_from_local_dir_paths_field(self) -> None:
        s = Skills.from_local_dir("/a", "/b.zip")
        assert s.paths == ["/a", "/b.zip"]
        assert s.urls == []
        assert s.packages == []

    def test_from_url_urls_field(self) -> None:
        s = Skills.from_url("https://example.com/x.zip")
        assert s.paths == []
        assert s.urls == ["https://example.com/x.zip"]
        assert s.packages == []

    def test_from_package_packages_field(self) -> None:
        s = Skills.from_package("my_pkg", "skills")
        assert s.paths == []
        assert s.urls == []
        assert s.packages == [("my_pkg", "skills")]

    def test_serialize_roundtrip(self) -> None:
        s = Skills(
            paths=["/a"],
            urls=["https://e.com/x.zip"],
            packages=[("p", "skills")],
        )
        dumped = s.model_dump()
        restored = Skills.model_validate(dumped)
        assert restored.paths == ["/a"]
        assert restored.urls == ["https://e.com/x.zip"]
        assert restored.packages == [("p", "skills")]

    def test_old_payload_without_new_fields_still_loads(self) -> None:
        # Ensures backward compatibility with serialized Skills from before
        # the new fields existed.
        s = Skills.model_validate({"paths": ["/x"]})
        assert s.paths == ["/x"]
        assert s.urls == []
        assert s.packages == []
