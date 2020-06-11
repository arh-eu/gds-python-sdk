#!/usr/bin/env python

import GDSClient

import asyncio
import sys
import websockets


class ExampleClient(GDSClient.WebsocketClient):
    def __init__(self, login_info = {
        "url": "ws://127.0.0.1:8080/gate",
        "username": "user",
        "password": None
    }):
        super().__init__(login_info.get('url'))
        self.loggedin = False
        loginreply = asyncio.get_event_loop().run_until_complete(self.login(login_info))
        self.login_reply(loginreply)

    async def login(self, login_info):
        print("Sending login message..")
        logindata = GDSClient.MessageUtil.create_message_from_header_and_data(
            GDSClient.MessageUtil.create_header(GDSClient.DataType.CONNECTION, username=login_info.get('username')),
            GDSClient.MessageUtil.create_login_data(reserved=[login_info.get('password')]))
        return await self.send(logindata)

    def login_reply(self, login_reply):
        loginStatusCode = login_reply[10][0]
        if (loginStatusCode == 200):
            print("The login was successful!")
            self.loggedin = True
        else:
            print("Login unsuccessful!\nDetails:")
            print("\t-" + login_reply[10][1])
            print("\t-" + login_reply[10][2])
            self.loggedin = False

    async def attachment_req(self, attachmentstr):
        insertdata = GDSClient.MessageUtil.create_attachment_request_data(
            attachmentstr)
        insertmsg = GDSClient.MessageUtil.create_message_from_header_and_data(
            GDSClient.DataType.ATTACHMENT_REQUEST, insertdata)
        return await self.send(insertmsg)

    def attachment_ack(self, response):
        pass

    async def event(self, eventstr):
        insertdata = GDSClient.MessageUtil.create_event_data(eventstr)
        insertmsg = GDSClient.MessageUtil.create_message_from_data(
            GDSClient.DataType.EVENT, insertdata)
        return await self.send(insertmsg)

    def event_ack(self, response):
        responseBody = response[10]
        print("Event result status is: " + str(responseBody[0]))
        print("Event returned " +
              str(len(responseBody[1][0])) + " records total.")
        print("Records: " + str(responseBody[1][0]))

    async def query(self, querystr):
        querydata = GDSClient.MessageUtil.create_select_query_data(querystr)
        querymsg = GDSClient.MessageUtil.create_message_from_data(
            GDSClient.DataType.QUERY_REQUEST, querydata)
        return await self.send(querymsg)

    async def next_query(self, contextdesc):
        querydata = GDSClient.MessageUtil.create_next_query_data(contextdesc)
        querymsg = GDSClient.MessageUtil.create_message_from_data(
            GDSClient.DataType.NEXT_QUERY_PAGE_REQUEST, querydata)
        return await self.send(querymsg)

    def query_reply(self, response):
        responseBody = response[10]
        print("Query result status is: " + str(responseBody[0]))
        print("Query returned " +
              str(responseBody[1][0]) + " records total.")
        print("Records: " + str(responseBody[1][5]))

    async def custom_message(self, header_type, data):
        msg = GDSClient.MessageUtil.create_message_from_data(header_type, data)
        return await self.send(msg)


def print_usage():
    print("Usage: python ./simple_client.py [-url <url>]" +
          " [-user <username>]" +
          " ( -attachment <attachSTR> | -query <querySTR> | -insert <insertSTR> | -merge <mergeSTR> | -update <updateSTR> )")


def main(args):
    mode = None
    nextquery = False
    sqlstring = ""

    login_info = {
        "url": "ws://127.0.0.1:8080/gate",
        "username": "user",
        "password": None
    }

    ii = 0
    try:
        while ii < len(args):
            currentParam = args[ii].lower()
            if(currentParam in ["-h", "--h", "-help", "--help"]):
                raise Exception
            if(currentParam == "-url"):
                ii += 1
                login_info["url"] = args[ii]
            elif(currentParam in ["-query", "-queryall"]):
                ii += 1
                if mode is not None:
                    print("Only one type of message can be sent this way!")
                    raise Exception
                mode = "q"
                sqlstring = args[ii]
                if(currentParam == "-nextquery"):
                    nextquery = True

            elif(currentParam in ["-event", "-insert", "-merge", "-update"]):
                ii += 1
                if mode is not None:
                    print("Only one type of message can be sent this way!")
                    raise Exception
                mode = "e"
                sqlstring = args[ii]
            elif(currentParam == "-attachment"):
                ii += 1
                if mode is not None:
                    print("Only one type of message can be sent this way!")
                    raise Exception
                mode = "a"
                sqlstring = args[ii]
            else:
                print("Unexpected argument: " + args[ii])
                raise Exception

            ii += 1
    except Exception:
        print_usage()
        return

    if(mode == None):
        print("Message missing!")
        print_usage()
        return

    client = ExampleClient(login_info)

    if(client.loggedin):
        if(mode == "q"):
            print("Sending query..")
            reply = asyncio.get_event_loop().run_until_complete(client.query(sqlstring))
            client.query_reply(reply)
            replybody = reply[10][1]
            if(nextquery):
                while (replybody[2]):
                    print("Sending next query page request..")
                    nextreply = asyncio.get_event_loop().run_until_complete(
                        client.next_query(replybody[3]))
                    replybody = nextreply[10][1]
                    client.query_reply(nextreply)

        elif(mode == "e"):
            print("Sending event..")
            reply = asyncio.get_event_loop().run_until_complete(client.event(sqlstring))
            client.event_ack(reply)

        elif(mode == "a"):
            print("Sending attachment request..")
            reply = asyncio.get_event_loop().run_until_complete(
                client.attachment_req(sqlstring))
            replybody = reply[10][1]
            if(replybody is None):
                pass
            client.attachment_ack(replybody)
        else:
            print("Could not login, skipping messages..")
    return 0


if __name__ == "__main__":
    main(sys.argv[1:])   

# TODO -user "username"
# TODO -password None
# TODO open attachment
# TODO print formatting