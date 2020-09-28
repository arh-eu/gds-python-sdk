- [Installation](#installation)
- [Communication](#communication)
- [Login to the GDS](#login-to-the-gds)
  * [Console Client](#console-client)
    + [Easy mode](#easy-mode)
      - [Connection information](#connection-information)
        * [URL](#url)
        * [username](#username)
        * [password](#password)
        * [timeout](#timeout)
        * [TLS](#tls)
      - [INSERT](#insert)
      - [UPDATE](#update)
      - [MERGE](#merge)
      - [DELETE](#delete)
      - [Sending Attachments with Events](#sending-attachments-with-events)
      - [SELECT query](#select-query)
      - [SELECT attachment](#select-attachment)
  * [Detailed mode](#detailed-mode)
    + [Class structure](#class-structure)
      - [Response handlers](#response-handlers)
    + [Message Headers](#message-headers)
    + [Message Data](#message-data)
      - [INSERT, UPDATE, MERGE, DELETE](#insert--update--merge--delete)
      - [SELECT query](#select-query-1)
      - [SELECT attachment](#select-attachment-1)
    + [Sending custom messages](#sending-custom-messages)

## Installation

To install and use the `Python` library you have to install two components our classes depend on, the MessagePack wrappers for the messages and the WebSocket protocol for the communication.

The first one, the `msgpack` module can be installed by typing `$ pip install msgpack` into your terminal or command line (the github repo can be found [here](https://github.com/msgpack/msgpack-python)). The version used for this module was `0.6.2`.

For the `websockets` library, you need to enter the `$ pip install websockets` command (its official site is [here](https://websockets.readthedocs.io/en/stable/intro.html)). The client uses version `8.1` in its code.

For TLS connection you will also need the `pyOpenSSL` libraries, which can be installed by `pip install pyopenssl`. We used the version `19.1.0` at the time of this documentation.

Please keep in mind that you need to have `Python 3.6.1` or newer to install the dependencies (you can install it from [here](https://www.python.org/downloads/)).

## Communication

The communication is based on a request-response pattern. You send your request to the GDS, which will response with (usually) an acknowledgement message (ACK). Most of the time this ACK message will contain the data you were waiting for as well, so there are no extra messages sent around.

Before any other message can be sent, clients are required to send a _login_ message first. Once the authorization is complete, clients can send their messages and await the replies.

Messages have two parts, _headers_ and _data_. The header contains basic information about your message (like timestamps or message identifiers) but also define the structure and contents of the _data_ part. For example a message, where the header has the type of `0` means that this message is a `CONNECTION`, or _login_ message, so the data part (the rest of the message) should be treated as such.

If you want to send messages and receive answers the fastest way, you want to read the [Easy mode](#easy-mode) of the Console Client.

If you want full control over the sent and received messages, you should head to the [Detailed mode](#detailed-mode).

For the SQL support restrictions about the strings you can read the according [Wiki page](https://github.com/arh-eu/gds/wiki/SQL-support-and-restrictions).

## Login to the GDS

Login messages are automatically generated and sent when you run the program (when you instantiate a `GDSClient` object). The client waits for the login reply before executing any other command, so you do not have to bother with this. If the login is unsuccessful (timeout or invalid credentials) the client will exit.

### Console Client

#### Easy mode
If you go with the easy mode, you do not have to know or worry about how to write `Python` code in order to use the client.

The easy mode will send the message you specify, and will await for the corresponding ACK messages and print them to your console (see more about them [here](https://github.com/arh-eu/gds/wiki/Message-Data)).

##### Connection information

###### URL

By default, the username `"user"` and the url `"ws://127.0.0.1:8888/gate"` will be used (this assumes that your local computer has a GDS instance or the server simulator running on the port `8888`).

###### username

You probably want to specify the url and the username as well, so start the script like this:
```sh
python .\simple_client.py -url "ws://192.168.255.254:8888/gate" -username "john_doe" -query "SELECT * FROM multi_event"
```

The `-url` flag, and the corresponding `URL` value is optional, so is the `USERNAME`, specified by the `-username` flag.
The order of the parameters is not fixed, but you can only use one type of message to be sent from the console.

###### password

If you need to specify the password used at login to the GDS as well, the `-password` flag can be used for this.

```sh
python .\simple_client.py -url "ws://192.168.255.254:8888/gate" -username "john_doe" -password "$ecretp4$$w0rD" -query "SELECT * FROM multi_event"
```
###### timeout

Probably you do not want to wait for ever for your replies. You can have a timeout for the response ACK messages, which can be specified with the `-timeout` flag. By default, the value is `30` seconds.

A timeout where the server does not respond to your login request can be the following:

```sh
python .\simple_client.py -query "SELECT * FROM multi_event" -timeout 10
Sending <login> message..
Waiting <login> reply..
The given timeout (10 seconds) has passed without any response from the server!
```

###### TLS

For secured connections you also need to specify your PKCS12 formatted certificate file (`*.p12` format), which is set by the `-cert` flag. Since the file is password protected, this can be set with the `-secret` flag.

The GDS usually runs on a different port (and endpoint) for secure connection. You also have to use `wss` as the url scheme.


```sh
python .\simple_client.py -url "wss://127.0.0.1:8443/gates" -cert "my_cert_file.p12" -secret "My_$3CreT_TŁS_P4s$W0RĐ" -query "SELECT * FROM multi_event"
```

If you need help about the usage of the program, it can be printed by the `--help` flag.

##### Event Command

The `INSERT`, `UPDATE` and `MERGE` messages are also known as _`EVENT`_ messages. Events can have attachments as well, and you can upload these to the GDS by sending them _with your event_.

The _event ID_ has to follow a format of `"EVNTyyMMddHHmmssSSS0"`, where the first 4 letters are the abbreviation of "event", while the rest specifies a timestamp code from. This will make `"EVNT2006241023125470"` a valid ID in an event table.

The _attachment ID_ has the same restriction, the difference is the prefix. Instead of the `EVNT` you should use `ATID`. The ID for the attachment can be `"ATID2006241023125470"`.

Since the format these messages have to follow is very strict, you will have to use `hex` values in your event strings for the _binary  IDs_ of your attachments. These `hex` values are unique identifiers for your binaries. To get the `hex` value of a string you can use the console client with the `-hex` flag to print these values. The client will print the results without any connection to a GDS. You can also enter multiple names, separating them by semicolon (`;`):

```sh
python .\simple_client.py -hex "picture1.bmp;picture3.bmp"
The hex value of `picture1.bmp` is: 0x70696374757265312e626d70
The hex value of `picture3.bmp` is: 0x70696374757265332e626d70
```
These _binary IDs_ (with the `0x` prefix) have to be in your `EVENT` `SQL` string. 

To attach files to your events (named "binary contents") you should use the `-attachments` flag with your `EVENT`.
The attachments are the names of your files found in the `attachments` folder. These names are automatically converted into `hex` values, and the contents of these files will be sent with your message (see the [wiki](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2)).

##### INSERT

To insert into a table, you only have to specify your `INSERT` statement.
The client will print the reply.
```sh
#inserting one attachment to the table
python .\simple_client.py -event "INSERT INTO multi_event (id, images) VALUES('EVNT2006241023125470', array('ATID2006241023125470')); INSERT INTO \"multi_event-@attachment\" (id, meta, data) VALUES('ATID2006241023125470', 'image/bmp', 0x70696374757265312e626d70 )" -attachments "picture1.bmp"
```

If the file you specify is not present, the client will print an error message without sending the message.

##### UPDATE

A simple `UPDATE` statement can be specified by the following command:
```sh
python .\simple_client.py -update "UPDATE multi_event SET speed = 15 WHERE id='EVNT2006241023125470'"
```

If you specify an update event, you _have to_ use an ID field in the `WHERE` condition, otherwise your request will not be accepted.

Just as at the `INSERT`, the ACK message will be displayed here as well.

##### MERGE

A simple `MERGE` statement can be specified by the following command:
```sh
python .\simple_client.py -merge "MERGE INTO multi_event USING (SELECT 'EVNT2006241023125470' as id, 'ABC123' as plate, 100 as speed) I ON (multi_event.id = I.id) WHEN MATCHED THEN UPDATE SET multi_event.speed = I.speed WHEN NOT MATCHED THEN INSERT (id, plate) VALUES (I.id, I.plate)"
```
The reply will be printed to the console, just as above.

##### DELETE

You cannot specify `DELETE` statements in the GDS.

##### SELECT query
A simple `SELECT` query statement can be specified by the following command:
```sh
python .\simple_client.py -query "SELECT * FROM multi_event"
```

The rows returned by the GDS will be printed on your output in json format.

It is possible, that your query has more than one pages available. By default, only 300 rows will be returned by the GDS (if you do not specify the `LIMIT` in your SQL and the config does not set another limit for this, which is maximized in 300 result per page).

If you want all the pages, not just the first one, you can use the `-queryall` flag instead.

##### SELECT attachment

A simple `SELECT` attachment query statement can be specified by the following command:
```sh
python .\simple_client.py -attachment "SELECT * FROM \"multi_event-@attachment\" WHERE id='ATID2006241023125470' and ownerid='EVNT2006241023125470' FOR UPDATE WAIT 86400"
```
Please be careful, as the table name in this examples should be in double quotes, so it should be escaped by backslash, otherwise the parameters will not be parsed right. The reason for this is that the `SQL` standard does not support hyphens in table names, therefore it should be treated differently.

The GDS might not have the specified attachment stored, in this case it can take a while until it can send you back its response. In this case your client will send back an ACK message which means that you have successfully received the attachments.

Your attachments will be saved in the `attachments` folder with the messageID as their file name.

### Detailed mode 

Messages consist two parts, a [header](https://github.com/arh-eu/gds/wiki/Message-Headers) and a [data](https://github.com/arh-eu/gds/wiki/Message-Data).

First you will read about the code structure so you will know how to modify it, then you will see how can you create the headers and data parts, after that you can read how to combine those for a whole message that can be sent.
The followings all assume that the login reply was successful.

Please keep in mind that you should not send any messages until you have received the (positive) ACK for your login, otherwise the GDS will drop your connection as the authentication and authorization processes did not finish yet but your client is trying to send messages (which is invalid without a login ACK). The `WebsocketClient` will raise an error and will not call your client code on unsuccessful login, but if you implement your own wrapper class, do not forget it.

#### Class structure

First you should understand the basics of the `WebsocketClient` class. Since the communication over the websocket protocol is asynchronous, most of our methods that send or await messages have to be defined as `async`.

The functions that are processing the replies do not have to be declared `async`, as it is not an asynchronous activity.

The `WebsocketClient` connects to the GDS on the given URL (that can be specified by command line arguments and is passed to the `__init()__` with the `**kwargs` pattern), and if the login was successful it will call the `client_code(..)` method of the class with the active websocket connection descriptor as the parameter. Should the login fail, the client exits with the error message displayed.

The `kwargs` contain mapped parameters, that are used to set up the (WebSocket) connection. Using the ConsoleClient initializes them from the command line arguments by the `argparse` library. However, for custom clients you can specify them as well to override the default values. These parameters are:

  - `url` - the GDS url you wish to connect to. Default value is set to `ws://127.0.0.1:8888/gate`.
  - `username` - the username used for messages and login. Default is `user`.
  - `password` - the password used for password authentication. Set to `None` if not specified.
  - `timeout` - the timeout used for awaiting reply messages from the GDS in seconds. `30` is the default.

If the `url` scheme is `wss` you can use TLS for encrypted connection. For this you need to specify two parameters as well.

  - `cert` - the path to the file in PKCS12 format for the certificates (the `*.p12` file).
  - `secret` - The password used to generate and encrypt the `cert` file.

Any additional parameter you specify can be accessed by the `self.args` variable in the whole class.

Business logic of the client should be implemented in the `client_code(..)` method. When the method returns, the client will close the active websocket connection and exit. Not overriding the `client_code(..)` will result in a `NotImplementedError()`.

The minimal working client is the following:

```python

import GDSClient
import websockets

class CustomGDSClient(GDSClient.WebsocketClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def client_code(self, ws: websockets.WebSocketClientProtocol):
      pass
```

The arguments passed (and parsed) to the client are always available through the `args` dictionary found in `self`. These keys will not have the hyphen (`-`) as their prefix, as it will get removed during parsing by the `argparse` module.

As the messages sent in the communication channels have to be packed and unpacked by the `msgpack` library, the `send(..)` and `recv(..)` methods will automatically do these conversions between the `Python` and `msgpack` types.

The `wait_for_reply(..)` method will call the `recv(..)` method, but if there is no response to be received by the timeout set in the client, it will raise a `TimeoutError` so you might want to use this instead of calling the `recv(..)` method itself.

##### Response handlers

The client has some predefined functions which you can override to use custom logic with the (ACK) responses the GDS gives you. These methods are the following:

```python
  def event_ack(self, response: list, **kwargs)

  def attachment_ack(self, response: list, **kwargs) -> bool

  def attachment_response(self, response: list, **kwargs)
  
  def query_ack(self, response: list, **kwargs) -> Tuple[bool, list]
```

All of those will get the returned response as their parameter, which you can handle as you want.

For the default implementations check the `WebsocketClient` class. For the ACK message structure you should check out the [wiki](https://github.com/arh-eu/gds/wiki/ACK-Message-Format), as usual. Keep in mind that the wiki usually specifies the message 

#### Message Headers

To create a message header, you can use the `MessageUtil` class found in the `GDSClient` module, which has a static method named `create_header(..)`. It requires a parameter for the message type (`header_type`), which is an enum defined in this package named `DataType`.

Enum values are the following:
```python
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
```

 The `create_header(..)` method has the rest of the header fields listed as optional parameters. If you do not specify of them, the message header will have the following (default) values:

```python
header = GDSClient.MessageUtil.create_header(GDSClient.DataType.QUERY_REQUEST)
print(header)

# output is the following:
["user", "<msgid>", <now>, <now>, False, None, None, None, None, 10]
```
, where `"<msgid>"` is a randomly generated `UUID` string, and `<now>` stands for the current time in milliseconds. Keep in mind that message IDs should be unique, therefore using `UUID`s for them is a very convenient and easy way.


The creation of a header message with the username `"john_doe"` for a query message can be created like this:
```python
header = GDSClient.MessageUtil.create_header(GDSClient.DataType.QUERY_REQUEST, username="john_doe")
```

The possible parameter names for the values of the `create_header(..)` method are the followings:
```python
username, msgid, create_time, request_time, fragmented, first_fragment, last_fragment, offset, full_data_size
```

For the accepted values and restrictions on the format of the header do not forget to check the [GDS Wiki](https://github.com/arh-eu/gds/wiki/Message-Headers).

#### Message Data

The data part can be created by the `MessageUtil` class as well, based on what type of message you want to send.

Similar to the headers, these use default values to simplify the calls for the general usage.

##### INSERT, UPDATE, MERGE, DELETE

DELETE is not supported by the GDS, so even if you try to send an event message with a `DELETE` statement, you will receive an error message about it.

The INSERT, UPDATE and MERGE messages have the same format, since they are all _event_ messages. This means, all three can be created by the `create_event_data(..)` method.

The string of the operations should be separated by the semicolon character (`;`). If there is only one operation, you do not need to bother with it, otherwise use it as separator.

The binary contents are usually set automatically by reading the files passed to the client by the `-attachments` flag.

This will read the files, create the appropriate hex values of their names and store the contents in the `binary_contents` map.

If you want to customize this, you should omit the `-attachments` flag from the console, and use the `binary_contents` field of the `create_event_data(..)` method.

To add the `priority_levels`, you can specify this parameter as well.

Allowed fields became:
```python
eventstr, binary_contents, priority_levels
```

The `eventstr` parameter does not need to be specified by name, as it is a positional argument. The rest are named, you should use them by name.

The `binary_contents` and `priority_levels` are detailed on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2). The former is a dictionary (associative array or map) containing the mappings of the binary contents, the latter is an array of the priority levels.

An example with binary contents and priority levels can be the following:

```python
operations = ";".join([
    "INSERT INTO multi_event (id, plate, speed, images) VALUES('EVNT2006241023125470', 'ABC123', 90, array('ATID2006241023125470'))",
    "INSERT INTO \"multi_event-@attachment\" (id, meta, data) VALUES('ATID2006241023125470', 'some_meta', 0x62696e6172795f69645f6578616d706c65)"
])

contents = {
    "62696e6172795f69645f6578616d706c65" : bytearray([127, 127, 0, 0])
}

levels = [
    [
        {1:True}
    ]
]

event_data = GDSClient.MessageUtil.create_event_data(operations, binary_contents = contents, priority_levels = levels)
```

If you print the the `event_data`, you should see the following:

```python
print(event_data)

# output
['INSERT INTO multi_event (id, plate, speed, images) VALUES(\'EVNT2006241023125470\', \'ABC123\', 90, array(\'ATID2006241023125470\'));INSERT INTO "multi_event-@attachment" (id, meta, data) VALUES(\'ATID2006241023125470\', \'some_meta\', 0x62696e6172795f69645f6578616d706c65)', {'62696e6172795f69645f6578616d706c65': bytearray(b'\x7f\x7f\x00\x00')}, [[{1: True}]]]
```

##### SELECT query

For a select query, you should invoke the `create_select_query_data(..)` method with the select string you have:
```python
querystr = "SELECT * FROM multi_event"
select_data = GDSClient.MessageUtil.create_select_query_data(querystr)
print(select_data)

#output will be:
['SELECT * FROM multi_event', 'PAGES', 60000]
```

There are two optional, named parameters here, one stands for the consistency type (by default set to `"PAGES"`), and one for the time-out.
It's default value is one minute (`60000` ms). These parameters are named `consistency` and `timeout`.

Details about their values can be found on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request---Data-Type-10).

Customized message can be created by:
```python
customquery = GDSClient.MessageUtil.create_select_query_data(querystr, consistency="NONE", timeout=100)
```

##### SELECT attachment
To select an attachment, you should invoke the `create_attachment_request_data(..)` method with the select string you have:

```python
attachmentstr = "SELECT * FROM \"multi_event-@attachment\" WHERE id='ATID2006241023125470' and ownerid='EVNT2006241023125470' FOR UPDATE WAIT 86400"
attachment_data = GDSClient.MessageUtil.create_attachment_request_data(attachmentstr)
```
This method has no additional parameters, so additional details cannot be specified here.

#### Sending custom messages

Once you have a header and a data part, the next step is combining them to have the message which will be sent.

You probably want to send the message and wait for the reply (ACK) as well, so you should use the `send_and_wait_message` method as explained at the start. 

You can use this method by specifying passing the `ws` descriptor, and by giving the `header` and `data` fields the values you have created.

Since this is an asynchronous call, you should not forget to `await` it!

The client will wait for a response and call the proper handler for it. If you receive an `Event ACK`, then the `event_ack(self, response, **kwargs)` method will be called.

```python

  def client_code(self, ws):
    header = GDSClient.MessageUtil.create_header(GDSClient.DataType.QUERY_REQUEST)
    querydata = GDSClient.MessageUtil.create_select_query_data("SELECT * FROM multi_event")

    await self.send_and_wait_message(ws, header=header, data=querydata)
```

If you do not want to wait for or do not need the reply you should invoke the `send_message(..)` instead. In this case you do not need to specify the parameters by name, the order of them is `(ws, header, data)`. The `await` keyword can not be omitted in this case either, keep in mind.

```python

  def client_code(self, ws):
    header = GDSClient.MessageUtil.create_header(GDSClient.DataType.EVENT)
    insertdata = GDSClient.MessageUtil.create_event_data("INSERT INTO multi_event (id, speed) VALUES('EVNT2006241023125470', 80)")

    await self.send_message(ws, header, insertdata)
```

It is possible that you do not want to save the result as a `json` for some reason. In this case you can pass the `skip_export=True` parameter to your `send..` calls, and in this case the reply will not be dumped.

The `ConsoleClient` is not made for embedded usage, as the sending and receiving methods are not outsourced to separate threads running endlessly with a possible queue behind them, sending messages and creating responses, and calling the appropriate callbacks. Therefore they will block the main thread until the timeout expires.

Sending many requests in a very short time frame could lead to unexpected behavior here, as the order of the replies is not fixed, a request sent later might be processed before the one you sent first, therefore the replies will not arrive in the order of the requests.

If you want to use the client in a bigger application as a module, you should inherit the `WebsocketClient` class and customize it for your needs based on the SDK description.
