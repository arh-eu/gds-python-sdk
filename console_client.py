#!/usr/bin/env python

from GDSClient import GDSClient, MessageUtil, DataType
import asyncio

import argparse

def event_ack(client, response: list, **kwargs):
        client.print_reply(response, **kwargs)
        response_body = response[10]
        if(not client.is_ack_ok(response, [200, 201, 202])):
            print("Error during the event request!")
            client.printErrorInACK(response_body)
        else:
            print(
                f"Event returned {(len(response_body[1]))} results total.")
            if not kwargs.get('skip_export'):
                client.save_object_to_json(response[1], response)

def query_ack(client, response: list, **kwargs):
        client.print_reply(response, **kwargs)
        max_length = 12
        response_body = response[10]
        if(not client.is_ack_ok(response)):
            print("Error during the query!")
            client.printErrorInACK(response_body)
            return False, None
        else:
            print(
                f"Query was successful! Total of {response_body[1][0]} record(s) returned.")
            if not kwargs.get('skip_export'):
                client.save_object_to_json(response[1], response)

def attachment_ack(client, response: list, **kwargs) -> bool:
        client.print_reply(response, **kwargs)
        response_body = response[10]
        if(not client.is_ack_ok(response, [200, 201, 202])):
            print("Error during the attachment request!")
            client.printErrorInACK(response_body)
        else:
            if(response_body[1][1].get('attachment')):
                attachment = response_body[1][1].get('attachment')
                print(f"We got the attachment!")
                if not kwargs.get('skip_export'):
                    client.save_attachment(response_body[1][1].get(
                        'attachmentid'), attachment, format=response_body[1][1].get('meta'))
            else:
                print("This should never happen!")

async def console_client(**kwargs):
    async with GDSClient(**kwargs) as client:
        if(client.args.get('event')):
            event_reply = await client.send_event2(eventstr=kwargs.get('event'))
            message_type = DataType(event_reply[9])
            print(f"Incoming message of type {message_type.name}")
            event_ack(client, event_reply, **kwargs)
        elif(client.args.get('attachment')):
            attachment_reply = await client.send_attachment_request4(attachstr=kwargs.get('attachment'))
            message_type = DataType(attachment_reply[9])
            print(f"Incoming message of type {message_type.name}")
            attachment_ack(client, attachment_reply, **kwargs)
        elif(client.args.get('query')):
            query_reply, more_page = await client.send_query_request10(querystr=kwargs.get('query'))
            message_type = DataType(query_reply[9])
            print(f"Incoming message of type {message_type.name}")
            query_ack(client, query_reply, **kwargs)
        elif(client.args.get('queryall')):
            query_reply, more_page = await client.send_query_request10(querystr=kwargs.get('queryall'))
            message_type = DataType(query_reply[9])
            print(f"Incoming message of type {message_type.name}")
            query_ack(client, query_reply, **kwargs)
            while(more_page):
        	    query_reply, more_page = await client.send_next_query_page12(prev_page=query_reply)
	            message_type = DataType(query_reply[9])
	            print(f"Incoming message of type {message_type.name}")
        	    query_ack(client, query_reply, **kwargs)
        else:
            pass
        
        
    pass

def main():
    parser = argparse.ArgumentParser(
        description='GDS ConsoleClient implementation in Python')

    parser.add_argument("-username", default="user",
                        help="The username you would like to use for login to the GDS.")
    parser.add_argument(
        "-password", help="The password you would like to use when logging in to the GDS.")
    parser.add_argument("-timeout", default=30, type=int,
                        help="The timeout of your queries (in seconds) before the waiting for the response will be interrupted.")
    parser.add_argument("-url", default="ws://127.0.0.1:8888/gate",
                        help="The URL of the GDS instance you would like to connect to.")
    parser.add_argument("-cert", default=None,
                        help="The name of your PKCS12 certificate file ('*.p12') if you want to use secure connection.")
    parser.add_argument("-secret", default=None,
                        help="The password for your certificate ('*.p12') file.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-hex", help="Converts the given string to HEX format.")
    group.add_argument(
        '-attachment', help="The ATTACHMENT request string you would like to use.")
    group.add_argument(
        '-event', help="The EVENT string you would like to use.")
    group.add_argument(
        '-query', help="The SELECT string you would like to use.")
    group.add_argument(
        '-queryall', help="The SELECT string you would like to use. This will query all pages, not just the first one.")
    
    parser.add_argument(
        "-attachments", default="", help="List of your files you want to send from the `attachments` folder next to this script.")

    args = vars(parser.parse_args())
    if(args.get('hex')):
        for arg in args.get('hex').split(';'):
            hexvalue = MessageUtil.hex(arg)
            print(f"The hex value of `{arg}` is: 0x{hexvalue}")
        return

    asyncio.get_event_loop().run_until_complete(console_client(**args))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Some error happened during running, client is now closing! Details:")
        print(str(type(e)) + " - " + str(e))
