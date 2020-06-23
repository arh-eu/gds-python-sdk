#!/usr/bin/env python

import GDSClient

import asyncio
import argparse
import os
import sys
import websockets

from datetime import datetime

class CustomGDSClient(GDSClient.WebsocketClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def client_code(self, ws: websockets.WebSocketClientProtocol):
        #your logic can go here
        pass



class ConsoleClient(GDSClient.WebsocketClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def client_code(self, ws: websockets.WebSocketClientProtocol):
        if(self.args.get('event')):
            await self.send_and_wait_event(ws, self.args.get('event'))
        elif(self.args.get('insert')):
            await self.send_and_wait_event(ws, self.args.get('insert'))
        elif(self.args.get('merge')):
            await self.send_and_wait_event(ws, self.args.get('merge'))
        elif(self.args.get('update')):
            await self.send_and_wait_event(ws, self.args.get('update'))
        elif(self.args.get('attachment')):
            await self.send_and_wait_attachment(ws, self.args.get('attachment'))
        elif(self.args.get('query')):
            await self.send_and_wait_query(ws, self.args.get('query'))
        elif(self.args.get('queryall')):
            await self.send_and_wait_query(ws, self.args.get('queryall'), all=True)
        else:
            pass

    # if you want custom logic with the response, you add your implementation here
    # by default, it will print all results returned.
    def event_ack(self, response: list):
        super().event_ack(response)

    # Returns whether the reply contained the attachment requested or not.
    # If there is no response, then you have to wait for one from the GDS.
    def attachment_ack(self, response: list) -> bool:
        return super().attachment_ack(response)

    # the attachment response if it was not present during the attachment ACK message
    def attachment_response(self, response: list):
        super().attachment_response(response)

    # if you want custom logic with the response, you add your implementation here
    # by default, it will print all records returned.
    # the super returns two values:
    # - a boolean whether the query can be continued or not
    # - The context holder of the query reply (if present, None otherwise)
    # This way you can use those to get all records by querying them in a while loop
    def query_ack(self, response: list):
        return super().query_ack(response)


def main():
    parser = argparse.ArgumentParser(
        description='GDS ConsoleClient implementation in Python')

    parser.add_argument("-username", default="user",
                        help="The username you would like to use for login to the GDS.")
    parser.add_argument(
        "-password", help="The password you would like to use when logging in to the GDS.")
    parser.add_argument("-timeout", default=30, type=int,
                        help="The timeout of your queries (in seconds) before the waiting for the response will be interrupted.")
    parser.add_argument("-url", default="ws://127.0.0.1:8080/gate",
                        help="The URL of the GDS instance you would like to connect to.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-hex", help="Converts the given string to HEX format.")
    group.add_argument(
        '-attachment', help="The ATTACHMENT request string you would like to use.")
    group.add_argument(
        '-insert', help="The INSERT string you would like to use.")
    group.add_argument(
        '-event', help="The EVENT string you would like to use.")
    group.add_argument(
        '-merge', help="The MERGE string you would like to use.")
    group.add_argument(
        '-query', help="The SELECT string you would like to use.")
    group.add_argument(
        '-queryall', help="The SELECT string you would like to use. This will query all pages, not just the first one.")
    group.add_argument(
        '-update', help="The UPDATE string you would like to use.")

    parser.add_argument(
        "-attachments", default="", help="List of your files you want to send from the `attachments` folder next to this script.")

    args = vars(parser.parse_args())
    if(args.get('hex')):
        for arg in args.get('hex').split(';'):
            hexvalue = GDSClient.MessageUtil.hex(arg)
            print(f"The hex value of `{arg}` is: 0x{hexvalue}")
        return

    client = ConsoleClient(**args)
    asyncio.get_event_loop().run_until_complete(client.run())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Some error happened during running, client is now closing! Details:")
        print(e)
