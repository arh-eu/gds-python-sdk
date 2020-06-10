#!/usr/bin/env python

import asyncio, concurrent.futures
import msgpack
import websockets
import uuid
try:
    import thread
except ImportError:
    import _thread as thread
import time

from datetime import datetime
from enum import Enum


class DataType(Enum):
    CONNECTION = 0
    CONNECTION_ACK = 1
    EVENT = 2
    EVENT_ACK = 3
    ATTACHMENT_REQUEST = 4
    ATTACHMENT_REQUEST_ACK = 5
    ATTACHMENT_RESPONSE = 6
    ATTACHMENT_RESPONSE_ACK = 7
    EVENT_DOCUMENT = 8
    EVENT_DOCUMENT_ACK = 9
    QUERY_REQUEST = 10
    QUERY_REQUEST_ACK = 11
    NEXT_QUERY_PAGE_REQUEST = 12

class WebsocketClient:
    def __init__(self, url="ws://127.0.0.1:8080/gate"):
        self.url = url

    async def send(self, data, reply_expected = True):
        async with websockets.connect(self.url) as ws:
            await ws.send(MessageUtil.pack(data))
            if(reply_expected):
                return MessageUtil.unpack(await ws.recv())

    async def recv(self, ws):
        return MessageUtil.unpack(await ws.recv())

class MessageUtil:
    @staticmethod
    def pack(data):
        return msgpack.packb(data)

    @staticmethod
    def unpack(data):
        return msgpack.unpackb(data, raw=False)

    @staticmethod
    def create_simple_header(type, username="user", msgid=None):
        now = int(datetime.now().timestamp())
        if(msgid == None):
            # message ID has to follow the UUID format
            msgid = str(uuid.uuid4())
        return [username, msgid, now, now, False, None, None, None, None, type.value]

    @staticmethod
    def create_message(header, data):
        msg = [] + header
        msg.append(data)
        return msg

    @staticmethod
    def create_simple_login():
        return [False, 1, False, None]

    @staticmethod
    def create_simple_select_query(querystr, cons="PAGES", timeout=60000):
        return [querystr, cons, timeout]
        
    @staticmethod
    def create_simple_next_query(context, timeout=60000):
        return [context, timeout]

    @staticmethod
    def create_simple_event(eventstr, binarycontents={}, prioritylevel=[]):
        return [eventstr, binarycontents, prioritylevel]

    @staticmethod
    def create_simple_attachment_request(attstr):
        return [attstr]

    @staticmethod
    def create_simple_message(type, data):
        return MessageUtil.create_message(MessageUtil.create_simple_header(type), data)


class Example:
    def connection_message(self):
        header = MessageUtil.create_simple_header(DataType.CONNECTION)
        data = [False, 1, False, None]
        return MessageUtil.create_message(header, data)

    def event_message(self):
        header = MessageUtil.create_simple_header(DataType.EVENT)
        data = ["INSERT INTO table('col1', col2') VALUES('a', 'b')"]
        return MessageUtil.create_message(header, data)

    def query_message(self):
        header = MessageUtil.create_simple_header(DataType.QUERY_REQUEST)
        data = ["SELECT * FROM table WHERE id IS NOT NULL", "NONE", 60000]
        return MessageUtil.create_message(header, data)

    def next_query_message(self):
        header = MessageUtil.create_simple_header(
            DataType.NEXT_QUERY_PAGE_REQUEST)
        data = [["query_context_str" for x in range(9)], 60000]
        return MessageUtil.create_message(header, data)
