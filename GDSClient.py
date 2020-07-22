#!/usr/bin/env python

import asyncio
import json
import msgpack
import pathlib
import ssl
import sys
import time
import uuid
import websockets

from datetime import datetime
from enum import Enum


class MessageException(Exception):
    pass


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

class StatusCode(Enum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NOT_ACCEPTABLE_304 = 304
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    NOT_ACCEPTABLE_406 = 406
    TIMEOUT = 408
    CONFLICT = 409
    PRECONDITION_FAILED = 412
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BANDWIDTH_LIMIT_EXCEEDED = 509
    NOT_EXTENDED = 510

class WebsocketClient:
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', "ws://127.0.0.1:8888/gate")
        self.username = kwargs.get('username', "user")
        self.password = kwargs.get('password')
        self.timeout = kwargs.get('timeout', 30)
        self.ssl = None

        self.mime_extensions = dict({
            "image/bmp": "bmp",
            "image/png": "png",
            "image/jpg": "jpg",
            "image/jpeg": "jpg",
            "video/mp4": "mp4"
        })

        if(self.url.startswith("wss") and kwargs.get('tls')):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.check_hostname = False
            cert = pathlib.Path(__file__).with_name(kwargs.get('tls'))
            ssl_context.load_verify_locations(cert)
            self.ssl = ssl_context
        self.args = kwargs

    async def run(self):
        async with websockets.connect(self.url, ssl=self.ssl) as ws:
            logindata = MessageUtil.create_message_from_header_and_data(
                MessageUtil.create_header(
                    DataType.CONNECTION, username=self.username),
                MessageUtil.create_login_data(reserved=[self.password]))
            print("Sending <login> message..")
            await self.send(ws, logindata)
            try:
                print("Waiting <login> reply..")
                login_reply = await self.wait_for_reply(ws)
            except TimeoutError as e:
                print('Login message ACK timed out!')
                raise e
            else:
                self.connection_ack(login_reply)
                return await self.client_code(ws)

    async def client_code(self, ws: websockets.WebSocketClientProtocol):
        raise NotImplementedError(
            "GDSClient should be inherited from with an overridden 'client_code(..)' method!")

    async def send(self, ws: websockets.WebSocketClientProtocol, data):
        await ws.send(MessageUtil.pack(data))

    async def recv(self, ws: websockets.WebSocketClientProtocol):
        return MessageUtil.unpack(await ws.recv())

    async def wait_for_reply(self, ws: websockets.WebSocketClientProtocol):
        try:
            return await asyncio.wait_for(self.recv(ws), self.timeout)
        except asyncio.TimeoutError as e:
            raise TimeoutError(
                f"The given timeout ({self.timeout} seconds) has passed without any response from the server!")
        except Exception as e:
            raise e

    def process_incoming_message(self, response: list, **kwargs):
        if(len(response) < 11):
            raise MessageException(
                f"Invalid message format received!\nExpected an array of length 11, found {len(response)} instead!")
        else:
            message_type = DataType(response[9])
            print(f"Incoming message of type {message_type.name}")
            if message_type == DataType.CONNECTION_ACK:
                return self.connection_ack(response, **kwargs)
            elif message_type == DataType.EVENT_ACK:
                return self.event_ack(response, **kwargs)
            elif message_type == DataType.ATTACHMENT_REQUEST_ACK:
                return self.attachment_ack(response, **kwargs)
            elif message_type == DataType.ATTACHMENT_RESPONSE:
                return self.attachment_response(response, **kwargs)
            elif message_type == DataType.EVENT_DOCUMENT_ACK:
                return self.event_ack(response, **kwargs)
            elif message_type == DataType.QUERY_REQUEST_ACK:
                return self.query_ack(response, **kwargs)
            else:
                raise MessageException(
                    f"Invalid MessageType found for the client: {message_type}")

    """
    Methods for sending data
    """
    async def send_message(self, ws: websockets.WebSocketClientProtocol, header: list, data):
        msg = MessageUtil.create_message_from_header_and_data(header, data)
        await self.send(ws, msg)
        return msg

    async def query(self, ws: websockets.WebSocketClientProtocol, querystr: str, **queryargs):
        querydata = MessageUtil.create_select_query_data(querystr, **queryargs)
        querymsg = MessageUtil.create_message_from_data(
            DataType.QUERY_REQUEST, querydata)
        await self.send(ws, querymsg)
        return querymsg

    async def next_query(self, ws: websockets.WebSocketClientProtocol, context: list):
        nextquery = MessageUtil.create_next_query_data(context)
        msg = MessageUtil.create_message_from_data(
            DataType.NEXT_QUERY_PAGE_REQUEST, nextquery)
        await self.send(ws, msg)
        return msg

    async def event(self, ws: websockets.WebSocketClientProtocol, eventstr: str, **eventargs):
        eventdata = MessageUtil.create_event_data(
            eventstr, **eventargs, files=self.args.get('attachments'))
        eventmsg = MessageUtil.create_message_from_data(
            DataType.EVENT, eventdata)
        await self.send(ws, eventmsg)
        return eventmsg

    async def attachment(self, ws: websockets.WebSocketClientProtocol, attachstr: str, **attachargs):
        attachdata = MessageUtil.create_attachment_request_data(
            attachstr, **attachargs)
        attachmsg = MessageUtil.create_message_from_data(
            DataType.ATTACHMENT_REQUEST, attachdata)
        await self.send(ws, attachmsg)
        return attachmsg

    async def attachment_response_ack(self, ws: websockets.WebSocketClientProtocol, **kwargs):
        response_ack_data = MessageUtil.create_attachment_response_ack_data(
            **kwargs)
        response_ack_message = MessageUtil.create_message_from_data(
            DataType.ATTACHMENT_RESPONSE_ACK, response_ack_data)
        await self.send(ws, response_ack_message)
        return response_ack_message

    """
    other utilities
    """

    def is_ack_ok(self, ack_mesage: list, ok_statuses=[200]) -> bool:
        return (ack_mesage[10] is not None) and (ack_mesage[10][0] in ok_statuses)

    async def send_and_wait_event(self, ws: websockets.WebSocketClientProtocol, eventstr: str):
        message = await self.event(ws, eventstr)
        self.process_incoming_message(await self.wait_for_reply(ws), original=message)

    async def send_and_wait_attachment(self, ws: websockets.WebSocketClientProtocol, attachstr: str):
        await self.attachment(ws, attachstr)
        should_wait = self.process_incoming_message(await self.wait_for_reply(ws))
        if(should_wait):
            response = await self.wait_for_reply(ws)
            self.process_incoming_message(response)
            print("Sending the Attachment ACK back to the GDS..")
            await self.attachment_response_ack(
                ws,
                requestids=response[10][0].get('requestids'),
                ownertable=response[10][0].get('ownertable'),
                attachmentid=response[10][0].get('attachmentid')
            )

    async def send_and_wait_query(self, ws: websockets.WebSocketClientProtocol, querystr: str, **kwargs):
        message = await self.query(ws, querystr)
        more_page, context = self.process_incoming_message(await self.wait_for_reply(ws), original=message)
        if(kwargs.get('all')):
            while(more_page):
                await self.next_query(ws, context)
                more_page, context = self.process_incoming_message(await self.wait_for_reply(ws), original=message)

    async def send_and_wait_message(self, ws: websockets.WebSocketClientProtocol, **kwargs):
        if(kwargs.get('header') and kwargs.get('data')):
            await self.send_message(ws, kwargs.get('header'), kwargs.get('data'))
        elif(kwargs.get('message')):
            await self.send(ws, kwargs.get('message'))
        else:
            raise ValueError(
                "Neither the 'header' and 'body' nor the 'message' value were specified!")
        response = await self.wait_for_reply(ws)
        self.process_incoming_message(response, **kwargs)

    def save_attachment(self, name: str, attachment: int, format="unknown", use_timestamp=True):
        pathlib.Path("attachments").mkdir(parents=True, exist_ok=True)
        filepath = "attachments/" + name
        if(use_timestamp):
            filepath += "_" + str(int(datetime.now().timestamp()))

        extension = "unknown"
        if (self.mime_extensions.get(format)):
            extension = self.mime_extensions.get(format)

        filepath += "." + extension
        print(f"Saving attachment as `{filepath}`..")
        try:
            with open(filepath, "xb") as file:
                file.write(attachment)
            print("Attachment successfully saved!")
        except Exception as e:
            print("Saving was unsuccessful!")
            raise e

    def save_object_to_json(self, name: str, obj: any):
        try:
            pathlib.Path("exports").mkdir(parents=True, exist_ok=True)
            filepath = f"exports/{name}.json"
            print(f"Saving full response as `{filepath}`..")
            with open(filepath, "x") as file:
                json.dump(obj, file, indent=4)
        except Exception as e:
            print(f"Could not save {filepath}! Details:")
            print(e)

    """
    default methods
    """

    def connection_ack(self, response: list, **kwargs):
        if (self.is_ack_ok(response)):
            print("The login was successful!")
        else:
            print("Login unsuccessful!\nDetails:")
            print("-" + str(response[10][1]))
            print("-" + str(response[10][2]))
            raise

    def event_ack(self, response: list, **kwargs):
        print("Reply:\n: " + json.dumps(response, default=lambda x: "<" +
                                        str(sys.getsizeof(x)) + " bytes>", indent=4))
        response_body = response[10]
        if(not self.is_ack_ok(response, [200, 201, 202])):
            print("Error during the event request!")
            self.printErrorInACK(response_body)
        else:
            print(
                f"Event returned {(len(response_body[1]))} results total.")
            if(kwargs.get('original')):
                msgid = kwargs.get('original')[1]
                self.save_object_to_json(msgid, response)

    def attachment_ack(self, response: list, **kwargs) -> bool:
        print("Reply:\n" + json.dumps(response, default=lambda x: "<" +
                                      str(sys.getsizeof(x)) + " bytes>", indent=4))
        response_body = response[10]
        if(not self.is_ack_ok(response, [200, 201, 202])):
            print("Error during the attachment request!")
            self.printErrorInACK(response_body)
            return False
        else:
            if(response_body[1][1].get('attachment')):
                attachment = response_body[1][1].get('attachment')
                print(f"We got the attachment!")
                self.save_attachment(response_body[1][1].get(
                    'attachmentid'), attachment, format=response_body[1][1].get('meta'))
                return False
            else:
                print("Attachment not yet received..")
                return True

    def attachment_response(self, response: list, **kwargs):
        print("Reply:\n" + json.dumps(response, default=lambda x: "<" +
                                      str(sys.getsizeof(x)) + " bytes>", indent=4))
        response_body = response[10]
        attachment = response_body[0].get('attachment')
        print(f"We got the attachment!")
        self.save_attachment(response_body[0].get(
            'attachmentid'), attachment, format=response_body[0].get('meta'))

    def query_ack(self, response: list, **kwargs):
        print("Query reply:\n: " + json.dumps(response,
                                              default=lambda x: "<" + str(sys.getsizeof(x)) + " bytes>", indent=4))
        max_length = 12
        response_body = response[10]
        if not self.is_ack_ok(response):
            print("Error during the query!")
            self.printErrorInACK(response_body)
            return False, None
        else:
            print(
                f"Query was successful! Total of {response_body[1][0]} record(s) returned.")

            if(kwargs.get('original')):
                msgid = kwargs.get('original')[1]
                self.save_object_to_json(msgid, response)
            return response_body[1][2], response_body[1][3]

    def printErrorInACK(self, message: list):
        print(f"Error status code returned: {message[0]} ({StatusCode(message[0]).name})")
        if(len(message) > 2):
            print("Error message: " + message[2])
        else:
            print("Server did not specify any error messages!")


class MessageUtil:
    @staticmethod
    def pack(data):
        return msgpack.packb(data, use_bin_type=True)

    @staticmethod
    def unpack(data):
        return msgpack.unpackb(data, raw=False)

    @staticmethod
    def create_header(header_type: DataType, **kwargs):
        now = int(datetime.now().timestamp())
        return [
            kwargs.get('username', "user"),
            kwargs.get('msgid', str(uuid.uuid4())),
            kwargs.get('create_time', now),
            kwargs.get('request_time', now),
            kwargs.get('fragmented', False),
            kwargs.get('first_fragment'),
            kwargs.get('last_fragment'),
            kwargs.get('offset'),
            kwargs.get('full_data_size'),
            header_type.value
        ]

    @staticmethod
    def create_message_from_header_and_data(header: list, data: list):
        msg = [] + header
        msg.append(data)
        return msg

    @staticmethod
    def create_login_data(**kwargs):
        return [
            kwargs.get('serve_on_same', False),
            kwargs.get('version', 1),
            kwargs.get('fragment_support', False),
            kwargs.get('fragment_unit', None),
            kwargs.get('reserved', [None])
        ]

    @staticmethod
    def create_select_query_data(querystr: str, **kwargs):
        return [
            querystr,
            kwargs.get('consistency', "PAGES"),
            kwargs.get('timeout', 60000)
        ]

    @staticmethod
    def create_next_query_data(context: list, **kwargs):
        return [
            context,
            kwargs.get('timeout', 60000)
        ]

    @staticmethod
    def create_event_data(eventstr: str, **kwargs):
        binary_contents = kwargs.get('binary_contents', {})
        if(kwargs.get('files')):
            for fname in kwargs.get('files').split(';'):
                try:
                    with open("attachments/" + fname, "rb") as file:
                        hexname = MessageUtil.hex(fname)
                        binary_contents[hexname] = file.read()
                except Exception as e:
                    raise FileNotFoundError(
                        f"The file named '{fname}' does not exist or could not be opened!")

        return [
            eventstr,
            binary_contents,
            kwargs.get('priority_levels', [])
        ]

    @staticmethod
    def create_attachment_request_data(attstr: str):
        return attstr

    @staticmethod
    def create_attachment_response_ack_data(**kwargs):
        return [
            kwargs.get('globalstatus', 200),
            [
                kwargs.get('localstatus', 201),
                dict({
                    "requestids": kwargs.get('requestids'),
                    "ownertable": kwargs.get('ownertable'),
                    "attachmentid": kwargs.get('attachmentid')
                })
            ],
            None
        ]

    @staticmethod
    def create_message_from_data(header_type: DataType, data):
        return MessageUtil.create_message_from_header_and_data(MessageUtil.create_header(header_type), data)

    @staticmethod
    def hex(text: str) -> str:
        return text.encode().hex()
