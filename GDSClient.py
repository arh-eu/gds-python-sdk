#!/usr/bin/env python

import msgpack
import websockets
import uuid
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
    def __init__(self, url):
        self.url = url

    async def send(self, data, reply_expected=True):
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
    def create_header(header_type,
                             username="user", msgid=None, create_time=None, request_time=None,
                             fragmented=False, first_fragment=None, last_fragment=None, offset=None,
                             full_data_size=None):
        now = int(datetime.now().timestamp())

        if(create_time == None):
            create_time = now

        if(request_time == None):
            request_time = now

        if(msgid == None):
            # message ID has to follow the UUID format
            msgid = str(uuid.uuid4())

        return [username, msgid, create_time, request_time, fragmented, first_fragment, last_fragment, offset, full_data_size, header_type.value]

    @staticmethod
    def create_message_from_header_and_data(header, data):
        msg = [] + header
        msg.append(data)
        return msg

    @staticmethod
    def create_login_data(serve_on_same=False, version=1, fragment_support=False, fragment_unit=None, reserved=[None]):
        return [serve_on_same, version, fragment_support, fragment_unit, reserved]

    @staticmethod
    def create_select_query_data(querystr, consistency="PAGES", timeout=60000):
        return [querystr, consistency, timeout]

    @staticmethod
    def create_next_query_data(context, timeout=60000):
        return [context, timeout]

    @staticmethod
    def create_event_data(eventstr, binary_contents={}, priority_levels=[]):
        return [eventstr, binary_contents, priority_levels]

    @staticmethod
    def create_attachment_request_data(attstr):
        return [attstr]

    @staticmethod
    def create_message_from_data(header_type, data):
        return MessageUtil.create_message_from_header_and_data(MessageUtil.create_header(header_type), data)


class Example:
    def connection_message(self):
        header = MessageUtil.create_header(DataType.CONNECTION)
        data = [False, 1, False, None]
        return MessageUtil.create_message_from_header_and_data(header, data)

    def event_message(self):
        header = MessageUtil.create_header(DataType.EVENT)
        data = ["INSERT INTO table('col1', col2') VALUES('a', 'b')"]
        return MessageUtil.create_message_from_header_and_data(header, data)

    def query_message(self):
        header = MessageUtil.create_header(DataType.QUERY_REQUEST)
        data = ["SELECT * FROM table WHERE id IS NOT NULL", "NONE", 60000]
        return MessageUtil.create_message_from_header_and_data(header, data)

    def next_query_message(self):
        header = MessageUtil.create_header(
            DataType.NEXT_QUERY_PAGE_REQUEST)
        data = [["query_context_str" for x in range(9)], 60000]
        return MessageUtil.create_message_from_header_and_data(header, data)
