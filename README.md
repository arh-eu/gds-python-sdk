## Installation

To install and use the `Python` library you have to install two components our classes depend on, the MessagePack wrappers for the messages and the WebSocket protocol for the communication.

The first one, the `msgpack` module can be installed by typing `$ pip install msgpack` into your terminal or command line.

For the `websockets` library, you need to enter the `$ pip install websocket_client` command.

Please keep in mind that you need to have `Python 3.4` or newer to install the dependencies.

## Login to the GDS

Login messages are automatically generated and sent when you instantiate the `GDSClient`. The client waits for the login reply, so you do not have to bother with this.

```python
    url = "ws://127.0.0.1:8080/gate" #or any other URL that's a valid GDS WS endpoint

    #keep in mind that the client will send and await the login reply, this will block
    client = ExampleClient(url)
```

## Creating messages

### Easy mode

If you do not want any customization on your messages but simply want to send and receive them, you can use the easy mode here.
The followings all assume that the login reply was successful and you have the `client` variable available for the communication.


In the easy mode will simplify the message creation, so you only have to specify the message data body - the message itself will be created by default values based on want you want to send by the client.

Since messages are sent and received async, we will use the `asnycio` module.

#### INSERT
#### UPDATE
#### MERGE
#### SELECT QUERY
To send a select query and parse and print the response you can use the following:

```python
    sqlstring = "SELECT * FROM table WHERE field<10"
    
    #asyncio will await the message
    wsreply = asyncio.get_event_loop().run_until_complete(client.query(sqlstring))
    reply = GDSClient.MessageUtil.unpack(wsreply)
    
    #this will print out the records we got back
    client.query_reply(reply)
    
    
    #or simply in one line:
    #client.query_reply(GDSClient.MessageUtil.unpack(asyncio.get_event_loop().run_until_complete(client.query(sqlstring))))
```

#### SELECT ATTACHMENT
#### Automatic pushing

### Detailed mode 

Messsages consist two parts, a header and a data.

For most of our cases, we will simplify the message creation, so you only have to specify the message data body - the message itself will be created by default values based on want you want to send by the client.

Since messages are sent and received async, we will use the `asnycio` module.



Messages consist of two parts, headers and data parts. You can read how to customize them here.

#### Message Headers

To create a message header, you can use the `MessageUtil` class found in the `GDSClient` module, which has a static method named `create_simple_header(..)`. It requires a parameter for the message type (`type`), which is an enum defined in this package named `DataType`.
It can also accept two optional string parameters, one for the username (`username`) and an other for the message ID (`msgid`).
Keep in mind that message IDs have to follow the UUID format to be accepted.

If you do not specify the extra parameters, the username `"user"` and a randomly generated UUID will be used.

The creation of a header message with the username `"john_doe"` for a query message can be created like this:

```python
query_header = GDSClient.MessageUtil.create_simple_header(GDSClient.DataType.QUERY_REQUEST, username="john_doe")
```

If you want to customize the information found in the header, check the format in the [GDS Wiki](https://github.com/arh-eu/gds/wiki/Message-Headers) and use it to create the list (array) you will send.

#### Message Data

The data part can be created by the `MessageUtils` class as well, based on what type of message you want to send.


##### Query
For a select query, you should invoke the `create_simple_select_query(..)` method with the select string you have:
```python
query_body = create_simple_select_query(querystr)
```

There are two, optional parameters here, one is the consistency type (by default set to `"PAGES"`), and one for the timeout.
It's default value is one minute (`60000` ms).

Additional infomation about this if you want to customize can be read [on the Wiki](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request---Data-Type-10)