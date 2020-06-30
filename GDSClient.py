#!/usr/bin/env python

import asyncio
import json
import msgpack
import pathlib
import ssl
import time
import uuid
import websockets

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
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', "ws://127.0.0.1:8888/gate")
        self.username = kwargs.get('username', "user")
        self.password = kwargs.get('password')
        self.timeout = kwargs.get('timeout', 30)
        self.ssl = None

        if(kwargs.get('tls')):
            self.ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            cert = pathlib.Path(__file__).with_name(kwargs.get('tls'))
            self.ssl.load_verify_locations(cert)

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
                if (self.is_ack_ok(login_reply)):
                    print("The login was successful!")
                    await self.client_code(ws)
                else:
                    print("Login unsuccessful!\nDetails:")
                    print("-" + str(login_reply[10][1]))
                    print("-" + str(login_reply[10][2]))

    async def client_code(self, ws: websockets.WebSocketClientProtocol):
        raise NotImplementedError()

    async def send(self, ws: websockets.WebSocketClientProtocol, data):
        await ws.send(MessageUtil.pack(data))

    async def recv(self, ws: websockets.WebSocketClientProtocol):
        return MessageUtil.unpack(await ws.recv())

    async def wait_for_reply(self, ws: websockets.WebSocketClientProtocol):
        try:
            return await asyncio.wait_for(self.recv(ws), self.timeout)
        except Exception as e:
            raise TimeoutError(
                f"The given timeout ({self.timeout} seconds) has passed without any response from the server!")

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

    """
    other utilities
    """

    def is_ack_ok(self, ack_mesage, ok_statuses=[200]):
        return (ack_mesage[10] is not None) and (ack_mesage[10][0] in ok_statuses)

    async def send_and_wait_event(self, ws: websockets.WebSocketClientProtocol, eventstr: str):
        await self.event(ws, eventstr)
        self.event_ack(await self.wait_for_reply(ws))

    async def send_and_wait_attachment(self, ws: websockets.WebSocketClientProtocol, attachstr: str):
        await self.attachment(ws, attachstr)
        should_wait = self.attachment_ack(await self.wait_for_reply(ws))
        if(should_wait):
            self.attachment_response(await self.wait_for_reply(ws))

    async def send_and_wait_query(self, ws: websockets.WebSocketClientProtocol, querystr: str, **kwargs):
        message = await self.query(ws, querystr)
        more_page, context = self.query_ack(await self.wait_for_reply(ws), original=message)
        if(kwargs.get('all')):
            while(more_page):
                await self.next_query(ws, context)
                more_page, context = self.query_ack(await self.wait_for_reply(ws))
    
    async def send_and_wait_message(self, ws: websockets.WebSocketClientProtocol, **kwargs):
        if(kwargs.get('header') and kwargs.get('data')):
            await self.send_message(ws, kwargs.get('header'), kwargs.get('data'))
        elif(kwargs.get('message')):
            await self.send(ws, kwargs.get('message'))
        else:
            raise ValueError("Neither the 'header' and 'body' nor the 'message' value were specified!")
        response = await self.wait_for_reply(ws)
        if(kwargs.get('callback') is not None):
            kwargs.get('callback')(response)


    def save_attachment(self, path: str, attachment: int, format="", use_timestamp=True):
        filepath = path
        if(use_timestamp):
            filepath += "_" + str(int(datetime.now().timestamp()))

        extension = "unknown"
        if (format == "image/bmp" ):
            extension = "bmp"
        elif (format == "image/png"):
            extension = "png"

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
            filepath = f"exports/{name}.json"
            print(f"Saving response as `{filepath}`..")
            with open(filepath, "x") as file:
                json.dump(obj, file, indent=4)
        except Exception as e:
            print(f"Could not save {filepath}! Details:")
            print(e)

    """
    default methods
    """

    def event_ack(self, response: list, **kwargs):
        response_body = response[10]
        if(not self.is_ack_ok(response, [200, 201, 202])):
            print("Error during the attachment request!")
            print("Details: " + response_body[2])
        else:
            print(
                f"Event returned {(len(response_body[1]))} results total.")
            print("Results:")
            for r in response_body[1]:
                print(r)

    def attachment_ack(self, response: list, **kwargs) -> bool:
        response_body = response[10]
        if(not self.is_ack_ok(response, [200, 201, 202])):
            print("Error during the attachment request!")
            print("Details: " + response_body[2])
            return False
        else:
            if(response_body[1][1].get('attachment')):
                attachment = response_body[1][1].get('attachment')
                print(f"We got the attachment!")
                self.save_attachment("attachments/" + response_body[1][1].get(
                    'attachmentid'), attachment, format=response_body[1][1].get('meta'))
                return False
            else:
                print("Attachment not yet received..")
                return True

    def attachment_response(self, response: list, **kwargs):
        response_body = response[10]
        attachment = response_body[0].get('attachment')
        print(f"We got the attachment!")
        self.save_attachment(
            "attachments/" + response_body[0].get('attachmentid'), attachment, format=response_body[0].get('meta'))

    def query_ack(self, response: list, **kwargs):
        max_length = 12
        response_body = response[10]
        if not self.is_ack_ok(response):
            print("Error during the query!")
            print("Details: " + response_body[2])
            return False, None
        else:
            print(
                f"Query was successful! Total of {response_body[1][0]} record(s) returned.")
            
            if(kwargs.get('original')):
                msgid = kwargs.get('original')[1]
                self.save_object_to_json(msgid, response_body)
            return response_body[1][2], response_body[1][3]


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
    def create_message_from_data(header_type: DataType, data):
        return MessageUtil.create_message_from_header_and_data(MessageUtil.create_header(header_type), data)

    @staticmethod
    def hex(text: str) -> str:
        return text.encode().hex()
