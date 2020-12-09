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
from OpenSSL import crypto
import tempfile
import os
from multiprocessing import Process, Pool, Value
import concurrent

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
    GONE = 410
    PRECONDITION_FAILED = 412
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BANDWIDTH_LIMIT_EXCEEDED = 509
    NOT_EXTENDED = 510

class GDSClient:
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

        if(self.url.startswith("wss") and kwargs.get('cert') and kwargs.get('secret')):
            self.initTLS(kwargs.get('cert'), kwargs.get('secret'))
        self.ws = None
        self.args = kwargs


    def initTLS(self, cert_path: str, password : str):
        try:
            with open(cert_path, 'rb') as provided_cert:
                cert_binary = provided_cert.read()
            p12 = crypto.load_pkcs12(cert_binary, password.encode('utf8'))
            privatekey = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
            cert = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())

            cert_file = tempfile.NamedTemporaryFile(delete=False)
            key_file = tempfile.NamedTemporaryFile(delete=False)
                
            cert_file.write(cert)
            key_file.write(privatekey)
            cert_file.close()
            key_file.close()
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.load_cert_chain(cert_file.name, key_file.name, password)

            os.unlink(cert_file.name)
            os.unlink(key_file.name)

            self.ssl = ssl_context
        except Exception as e:
            raise Exception("Could not initialize TLS connection!", e)


    async def send(self, data):
        await self.ws.send(MessageUtil.pack(data))

    async def recv(self):
        data = await self.ws.recv()
        return MessageUtil.unpack(data)

    async def wait_for_reply(self):
        try:
            return await asyncio.wait_for(self.recv(), self.timeout)
        except asyncio.TimeoutError as e:
            raise TimeoutError(
                f"The given timeout ({self.timeout} seconds) has passed without any response from the server!")
        except Exception as e:
            raise e

    async def __aenter__(self):
        self.ws = await websockets.connect(self.url, ssl=self.ssl)
        logindata = MessageUtil.create_message_from_header_and_data(
            MessageUtil.create_header(
                DataType.CONNECTION, username=self.username),
            MessageUtil.create_login_data(reserved=[self.password]))
        print("Sending <login> message..")
        await self.send(logindata)
        try:
            print("Waiting <login> reply..")
            login_reply = await self.wait_for_reply()
        except TimeoutError as e:
            print('Login message ACK timed out!')
            raise e
        else:
            if (self.is_ack_ok(login_reply)):
                print("The login was successful!")
                print(login_reply)
            else:
                print("Login unsuccessful!\nDetails:")
                print("-" + str(login_reply[10][1]))
                print("-" + str(login_reply[10][2]))
        return self


    async def __aexit__(self, exc_type, exc, tb):
        await self.ws.close()
        print("Client disconnected!")
        pass


    """
    Methods for sending data
    """
    async def send_message(self, header: list, data):
        msg = MessageUtil.create_message_from_header_and_data(header, data)
        await self.send(msg)
        return msg


    async def send_event2(self, **eventargs):
        if(eventargs.get('data')):
            if(eventargs.get('header')):
                event_reply = await self.send_and_wait_message(header=eventargs.get('header'), data = eventargs.get('data'))
            else:
                eventmsg = MessageUtil.create_message_from_data(
                    DataType.EVENT, username=self.args.get('username'), **eventargs)
                event_reply = await self.send_and_wait_message(message=eventmsg)
        elif(eventargs.get('eventstr')):
            eventdata = MessageUtil.create_event_data2(**eventargs, files=self.args.get('attachments'))
            eventmsg = MessageUtil.create_message_from_data(
                DataType.EVENT, data = eventdata, username=self.args.get('username'), **eventargs)
            event_reply = await self.send_and_wait_message(message=eventmsg)
        else:
            raise ValueError(
                "Neither the 'data' nor the 'eventstr' value were specified!")
        return await self.check_incoming_message_type(DataType.EVENT_ACK, event_reply)

    async def send_attachment_request4(self, **attachargs):
        if(attachargs.get('data')):
            if(attachargs.get('header')):
                response = await self.send_and_wait_message(header=attachargs.get('header'), data = attachargs.get('data'))
            else:
                attachmsg = MessageUtil.create_message_from_data(
                    DataType.ATTACHMENT_REQUEST, username=self.args.get('username'), **attachargs)
                response = await self.send_and_wait_message(message=attachmsg)
        elif(attachargs.get('attachstr')):
            attachdata = MessageUtil.create_attachment_request_data4(attachargs.get('attachstr'))
            attachmsg = MessageUtil.create_message_from_data(
                DataType.ATTACHMENT_REQUEST, data = attachdata, username=self.args.get('username'), **attachargs)
            response = await self.send_and_wait_message(message=attachmsg)
        else:
            raise ValueError(
                "Neither the 'data' nor the 'attachstr' value were specified!")
        response_body = response[10]
        if(not self.is_ack_ok(response, [200, 201, 202])):
            should_wait = False
        else:
            if(response_body[1][1].get('attachment')):
                should_wait = False
            else:
                should_wait = True
        if(should_wait):
            response = await self.wait_for_reply()
            await self.__send_attachment_response_ack7(
                requestids=response[10][0].get('requestids'),
                ownertable=response[10][0].get('ownertable'),
                attachmentid=response[10][0].get('attachmentid')
            )
            return await self.check_incoming_message_type(DataType.ATTACHMENT_RESPONSE, response)
        else:
            return await self.check_incoming_message_type(DataType.ATTACHMENT_REQUEST_ACK, response)

    async def __send_attachment_response_ack7(self, **kwargs):
        response_ack_data = MessageUtil.create_attachment_response_ack_data7(
            **kwargs)
        response_ack_message = MessageUtil.create_message_from_data(
            DataType.ATTACHMENT_RESPONSE_ACK, data=response_ack_data, username=self.args.get('username'), **kwargs)
        await self.send(response_ack_message)
        return response_ack_message

    async def send_event_document8(self, **eventdocargs):
        if(eventdocargs.get('data')):
            if(eventdocargs.get('header')):
                event_document_reply = await self.send_and_wait_message(header=eventdocargs.get('header'), data = eventdocargs.get('data'))
            else:
                msg = MessageUtil.create_message_from_data(DataType.EVENT_DOCUMENT, username = self.args.get('username'), **eventdocargs)
                event_document_reply = await self.send_and_wait_message(message=msg)
        else:
            event_document_data = MessageUtil.create_event_document_data8(**eventdocargs)
            msg = MessageUtil.create_message_from_data(DataType.EVENT_DOCUMENT, data=event_document_data, username = self.args.get('username'), **eventdocargs)
            event_document_reply = await self.send_and_wait_message(message=msg)
        return await self.check_incoming_message_type(DataType.EVENT_DOCUMENT_ACK, event_document_reply)

    async def send_query_request10(self, **queryargs):
        if(queryargs.get('data')):
            if(queryargs.get('header')):
                query_reply = await self.send_and_wait_message(header=queryargs.get('header'), data = queryargs.get('data'))
            else:
                querymsg = MessageUtil.create_message_from_data(
                    DataType.QUERY_REQUEST, username=self.args.get('username'), **queryargs)
                query_reply = await self.send_and_wait_message(message=querymsg)
        elif(queryargs.get('querystr')):
            querydata = MessageUtil.create_query_request_data10(**queryargs)
            querymsg = MessageUtil.create_message_from_data(
                DataType.QUERY_REQUEST, data=querydata, username=self.args.get('username'), **queryargs)
            query_reply = await self.send_and_wait_message(message=querymsg)
        else:
            raise ValueError(
                "Neither the 'data' nor the 'querystr' value were specified!")
        reply = await self.check_incoming_message_type(DataType.QUERY_REQUEST_ACK, query_reply)
        if(self.is_ack_ok(reply)):
            return reply, reply[10][1][2]
        else:
            return reply, None
       
    async def send_next_query_page12(self, **nextqueryargs):
        if(nextqueryargs.get('data')):
            if(nextqueryargs.get('header')):
                next_query_reply = await self.send_and_wait_message(header=nextqueryargs.get('header'), data = nextqueryargs.get('data'))
            else:
                msg = MessageUtil.create_message_from_data(
                    DataType.NEXT_QUERY_PAGE_REQUEST, username=self.args.get('username'), **nextqueryargs)
                next_query_reply = await self.send_and_wait_message(message=msg)
        elif(nextqueryargs.get('prev_page')):
            prev_page = nextqueryargs.get('prev_page')
            context = prev_page[10][1][3]
            nextquery = MessageUtil.create_next_query_page_data12(context, **nextqueryargs)
            msg = MessageUtil.create_message_from_data(
                DataType.NEXT_QUERY_PAGE_REQUEST, data=nextquery, username=self.args.get('username'), **nextqueryargs)
            next_query_reply = await self.send_and_wait_message(message=msg)
        else:
            raise ValueError(
                "Neither the 'data' nor the 'prev_page' value were specified!")
        reply = await self.check_incoming_message_type(DataType.QUERY_REQUEST_ACK, next_query_reply)
        if(self.is_ack_ok(reply)):
            return reply, reply[10][1][2]
        else:
            return reply, None


    """
    other utilities
    """

    def is_ack_ok(self, response: list, ok_statuses=[200]) -> bool:
        return (response[10] is not None) and (response[10][0] in ok_statuses)


    async def check_incoming_message_type(self, expected: DataType, response:list, **kwargs):
        message_type = DataType(response[9])
        if(message_type == expected):
            return response
        else:
            if(message_type == DataType.ATTACHMENT_RESPONSE):
                await self.__send_attachment_response_ack7(
                    requestids=response[10][0].get('requestids'),
                    ownertable=response[10][0].get('ownertable'),
                    attachmentid=response[10][0].get('attachmentid')
                )
            elif(message_type == DataType.EVENT_DOCUMENT):
                c = len(response[10][2])
                result = []
                for i in range(c):
                    result.append([201, "", {}])
                event_document_ack_data = MessageUtil.create_event_document_ack_data9(result = result)
                message = MessageUtil.create_message_from_data(DataType.EVENT_DOCUMENT_ACK, data=event_document_ack_data, **kwargs)
                await self.send(message)
            raise MessageException(
                    f"Unexpected MessageType found for the client: {message_type.name}, message: {response}")


    async def send_and_wait_message(self, **kwargs):
        if(kwargs.get('header') and kwargs.get('data')):
            await self.send_message(kwargs.get('header'), kwargs.get('data'))
        elif(kwargs.get('message')):
            await self.send(kwargs.get('message'))
        else:
            raise ValueError(
                "Neither the 'header' and 'data' nor the 'message' value were specified!")
        response = await self.wait_for_reply()
        return response


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

    
    
    def print_reply(self, message: any, **kwargs):
        if kwargs.get('print_simple'):
            print("Reply arrived!")
        else:
            print("Reply:\n: " + json.dumps(message, default=lambda x: "<" + str(sys.getsizeof(x)) + " bytes>", indent=4))

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
            #current GDS version is 5.1, therefore
            #the major version is set to 5 while the minor to 1.
            kwargs.get('version', (5 << 16 | 1)),
            kwargs.get('fragment_support', False),
            kwargs.get('fragment_unit', None),
            kwargs.get('reserved', [None])
        ]


    @staticmethod
    def create_event_data2(**kwargs):
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
            kwargs.get('eventstr'),
            binary_contents,
            kwargs.get('priority_levels', [])
        ]

    @staticmethod
    def create_attachment_request_data4(attstr: str):
        return attstr

    @staticmethod
    def create_attachment_response_ack_data7(**kwargs):
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
    def create_event_document_data8(**kwargs):
        return [
            kwargs.get('tablename'),
            kwargs.get('fielddescriptors'),
            kwargs.get('records'),
            kwargs.get('returningoptions', dict({}))
        ]


    @staticmethod
    def create_event_document_ack_data9(**kwargs):
        return [
            kwargs.get('globalstatus', 200),
            kwargs.get('result'),
            None
        ]

    @staticmethod
    def create_query_request_data10(**kwargs):
        return [
            kwargs.get('querystr'),
            kwargs.get('consistency', "PAGES"),
            kwargs.get('timeout', 60000)
        ]

    @staticmethod
    def create_next_query_page_data12(context: list, **kwargs):
        return [
            context,
            kwargs.get('timeout', 60000)
        ]

    @staticmethod
    def create_message_from_data(header_type: DataType, **kwargs):
        return MessageUtil.create_message_from_header_and_data(MessageUtil.create_header(header_type, **kwargs), kwargs.get('data'))

    @staticmethod
    def hex(text: str) -> str:
        return text.encode().hex()