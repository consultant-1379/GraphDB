# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2018 "Neo4j,"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from unittest import TestCase
from neobolt.direct import Connection


class FakeSocket(object):
    def __init__(self, address):
        self.address = address

    def getpeername(self):
        return self.address

    def sendall(self, data):
        return

    def close(self):
        return


class ConnectionTestCase(TestCase):

    def test_conn_timedout(self):
        address = ("127.0.0.1", 7687)
        connection = Connection(1, address, FakeSocket(address),  max_connection_lifetime=0)
        self.assertEqual(connection.timedout(), True)

    def test_conn_not_timedout_if_not_enabled(self):
        address = ("127.0.0.1", 7687)
        connection = Connection(1, address, FakeSocket(address), max_connection_lifetime=-1)
        self.assertEqual(connection.timedout(), False)

    def test_conn_not_timedout(self):
        address = ("127.0.0.1", 7687)
        connection = Connection(1, address, FakeSocket(address), max_connection_lifetime=999999999)
        self.assertEqual(connection.timedout(), False)