# Installation

To install and use the `Python` library you have to install two components our classes depend on, the MessagePack wrappers for the messages and the WebSocket protocol for the communication.

The first one, the `msgpack` module can be installed by typing `$ pip install msgpack` into your terminal or command line (the github repo can be found [here](https://github.com/msgpack/msgpack-python)). The version used during creating this module was `0.6.2`, but the latest version (which at the time of writing is `1.0.3`) should work as well.

For the `websockets` library, you need to enter the `$ pip install websockets` command (its official site is [here](https://readthedocs.org/projects/websockets/)). The client used version `8.1` in its code, but `9.0.1` is already out as of Jan. 2022.

For TLS connection you will also need the `pyOpenSSL` libraries, which can be installed by `pip install pyopenssl`. We used the version `19.1.0` at the time of this documentation, but version `21.0.0` is available.

Please keep in mind that you need to have `Python 3.6.1` or newer to install the dependencies (you can install it from [here](https://www.python.org/downloads/)).

# Communication

The communication is based on a request-response pattern. You send your request to the GDS, which will response with (usually) an acknowledgement message (ACK). Most of the time this ACK message will contain the data you were waiting for as well, so there are no extra messages sent around.

Before any other message can be sent, clients are required to send a _login_ message first. Once the authorization is complete, clients can send their messages and await the replies.

Messages have two parts, _headers_ and _data_. The header contains basic information about your message (like timestamps or message identifiers) but also define the structure and contents of the _data_ part. For example a message, where the header has the type of `0` means that this message is a `CONNECTION`, or _login_ message, so the data part (the rest of the message) should be treated as such.

If you want to send requests and receive responses the fastest way, you want to read the [Console Client](#console-client).

If you want full control over the sent and received messages, you should head to the [Detailed mode](#detailed-mode).

For the SQL support restrictions about the strings you can read the according [Wiki page](https://github.com/arh-eu/gds/wiki/SQL-support-and-restrictions).

* [Console Client](#console-client)
  + [Arguments](#arguments)
    - [Options](#options)
      * [URL](#url)
      * [Username](#username)
      * [Password](#password)
      * [Timeout](#timeout)
      * [TLS](#tls)
    - [Commands](#commands)
      * [EVENT command](#event-command)
      * [ATTACHMENT-REQUEST command](#attachment-request-command)
      * [QUERY command](#query-command)
* [Detailed mode](#detailed-mode)
  + [Creating the client](#creating-the-client)
  + [Sending messages](#sending-messages)
    - [EVENT messages](#event-messages)
    - [ATTACHMENT-REQUEST message](#attachment-request-message)
    - [QUERY message](#query-message)
  + [Sending custom messages](#sending-custom-messages)

## Console Client

If you go with the console client, you do not have to know or worry about how to write `Python` code in order to use the client.

The console client will send the message you specify, and will await for the corresponding ACK messages and print them to your console (see more about them [here](https://github.com/arh-eu/gds/wiki/Message-Data)).

### Arguments

#### Options

##### URL

By default, the username `"user"` and the url `"ws://127.0.0.1:8888/gate"` will be used (this assumes that your local computer has a GDS instance or the server simulator running on the port `8888`). But you can specify the url with the `-url` flag.

```sh
python .\console_client.py -url "ws://192.168.255.254:8888/gate" -query "SELECT * FROM multi_event"
```

##### Username

You probably want to specify the url and the username as well, so start the script like this:
```sh
python .\console_client.py -url "ws://192.168.255.254:8888/gate" -username "john_doe" -query "SELECT * FROM multi_event"
```

The `-url` flag, and the corresponding `URL` value is optional, so is the `USERNAME`, specified by the `-username` flag.
The order of the parameters is not fixed, but you can only use one type of message to be sent from the console.

##### Password

If you need to specify the password used at login to the GDS as well, the `-password` flag can be used for this.

```sh
python .\simple_client.py -url "ws://192.168.255.254:8888/gate" -username "john_doe" -password "$ecretp4$$w0rD" -query "SELECT * FROM multi_event"
```
##### Timeout

Probably you do not want to wait for ever for your replies. You can have a timeout for the response ACK messages, which can be specified with the `-timeout` flag. By default, the value is `30` seconds.

A timeout where the server does not respond to your login request can be the following:

```sh
python .\simple_client.py -query "SELECT * FROM multi_event" -timeout 10
Sending <login> message..
Waiting <login> reply..
The given timeout (10 seconds) has passed without any response from the server!
```

##### TLS

For secured connections you also need to specify your PKCS12 formatted certificate file (`*.p12` format), which is set by the `-cert` flag. Since the file is password protected, this can be set with the `-secret` flag.

The GDS usually runs on a different port (and endpoint) for secure connection. You also have to use `wss` as the url scheme.


```sh
python .\simple_client.py -url "wss://127.0.0.1:8443/gates" -cert "my_cert_file.p12" -secret "My_$3CreT_TŁS_P4s$W0RĐ" -query "SELECT * FROM multi_event"
```

If you need help about the usage of the program, it can be printed by the `--help` flag.

#### Commands

##### EVENT command

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
The attachments are the names of your files found in the `attachments` folder. You can enter multiple names, separating them by semicolon (`;`). These names are automatically converted into `hex` values, and the contents of these files will be sent with your message (see the [wiki](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2)).

INSERT

To insert into a table, you only have to specify your `INSERT` statement.
The client will print the reply.
```sh
#inserting one attachment to the table
python .\simple_client.py -event "INSERT INTO multi_event (id, images) VALUES('EVNT2006241023125470', array('ATID2006241023125470')); INSERT INTO \"multi_event-@attachment\" (id, meta, data) VALUES('ATID2006241023125470', 'image/bmp', 0x70696374757265312e626d70 )" -attachments "picture1.bmp"
```

If the file you specify is not present, the client will print an error message without sending the message.

UPDATE

A simple `UPDATE` statement can be specified by the following command:
```sh
python .\simple_client.py -event "UPDATE multi_event SET speed = 15 WHERE id='EVNT2006241023125470'"
```

If you specify an update event, you _have to_ use an ID field in the `WHERE` condition, otherwise your request will not be accepted.

Just as at the `INSERT`, the ACK message will be displayed here as well.

MERGE

A simple `MERGE` statement can be specified by the following command:
```sh
python .\simple_client.py -event "MERGE INTO multi_event USING (SELECT 'EVNT2006241023125470' as id, 'ABC123' as plate, 100 as speed) I ON (multi_event.id = I.id) WHEN MATCHED THEN UPDATE SET multi_event.speed = I.speed WHEN NOT MATCHED THEN INSERT (id, plate) VALUES (I.id, I.plate)"
```
The reply will be printed to the console, just as above.

##### ATTACHMENT-REQUEST command

A simple `SELECT` attachment query statement can be specified by the following command:
```sh
python .\simple_client.py -attachment "SELECT * FROM \"multi_event-@attachment\" WHERE id='ATID2006241023125470' and ownerid='EVNT2006241023125470' FOR UPDATE WAIT 86400"
```
Please be careful, as the table name in this examples should be in double quotes, so it should be escaped by backslash, otherwise the parameters will not be parsed right. The reason for this is that the `SQL` standard does not support hyphens in table names, therefore it should be treated differently.

The GDS might not have the specified attachment stored, in this case it can take a while until it can send you back its response. In this case your client will send back an ACK message which means that you have successfully received the attachments.

Your attachments will be saved in the `attachments` folder with the Attachment id as their file name.

##### QUERY command
A simple `SELECT` query statement can be specified by the following command:
```sh
python .\simple_client.py -query "SELECT * FROM multi_event"
```

The rows returned by the GDS will be printed on your output in json format.

It is possible, that your query has more than one pages available. By default, only 300 rows will be returned by the GDS (if you do not specify the `LIMIT` in your SQL and the config does not set another limit for this, which is maximized in 300 result per page).

If you want all the pages, not just the first one, you can use the `-queryall` flag instead.

## Detailed mode 

GDSClient is an async Context Manager, so you should use it with an `async with` statement. Before running your code inside the `async with` statement, the GDSClient will connect to the GDS. If the login is unsuccessful, the GDSClient will raise an error and will not run your code. At the end of the `async with` statement the client will automatically close the connection to the GDS, so you can not use the client outside the statement.

### Creating the client

To create the client you should use the constructor of the GDSClient class. The parameters, you want to use to set up your websocket connection, you should pass to the constructor of the GDSClient. You should specify these parameters by name, because they are not positional arguments.

These are the parameters you can specify for your client to override the default values:

  - `url` - the GDS url you wish to connect to. Default value is set to `ws://127.0.0.1:8888/gate`.
  - `username` - the username used for messages and login. Default is `user`.
  - `password` - the password used for password authentication. Set to `None` if not specified.
  - `timeout` - the timeout used for awaiting reply messages from the GDS in seconds. `30` is the default.

If the `url` scheme is `wss` you can use TLS for encrypted connection. For this you need to specify two parameters as well.

  - `cert` - the path to the file in PKCS12 format for the certificates (the `*.p12` file).
  - `secret` - The password used to generate and encrypt the `cert` file.

Any additional parameter you specify can be accessed by the `args` variable in the client class.

You should start your code like this:


```python

from GDSClient import GDSClient, MessageUtil, DataType
import asyncio

async def as_main():
    async with GDSClient(username="user", url="ws://127.0.0.1:8888/gate") as client:
      pass

def main():
    asyncio.get_event_loop().run_until_complete(as_main())
```

Now your client is initialized and connected to the GDS, so you can use the client (inside the `async with` statement) to send and receive messages.

You should write your code inside the `async with` statement, but to make reading easier, in the rest of this guide examples will not contain the `async with` statement.

### Sending messages

Messages consists two parts, a [header](https://github.com/arh-eu/gds/wiki/Message-Headers) and a [data](https://github.com/arh-eu/gds/wiki/Message-Data). You can send messages without specifying the header part. In this case the header will created automatically. To see how to send a message by specifying the header part too, go to the [Sending custom messages](#sending-custom-messages) section.

The GDSClient `send...()` methods will wait for the response to the message they have sent and will return with the response. If the type of the response is not the expected type then the client will raise an error and will print the error to the console.

The `send...()` methods are async functions, so you have to write `await` before them.

#### &#x26A0; The replies you receive will follow the JSON (unpacked from MessagePack) format of the message specification. This means that there will be no extra classes introduced, as the compliance between JSON an Python objects is clear. Therefore the message structure and the Python object structure is the same.

#### EVENT messages

The INSERT, UPDATE and MERGE messages have the same format, since they are all _event_ messages. This means, all three can be created by the `create_event_data2(..)` method of the MessageUtil class.

The string of the operations should be separated by the semicolon character (`;`). If there is only one operation, you do not need to bother with it, otherwise use it as a separator.

You can use the `binary_contents` field of the `create_event_data2(..)` method to give the attachments to your event messages.

To add the `priority_levels`, you can specify this parameter as well.

You can omit the `binary_contents` and the `priority_levels` parameter, but not the `eventstr` parameter.

Allowed fields became:
```python
eventstr, binary_contents, priority_levels
```

The `eventstr`, `binary_contents` and `priority_levels` are detailed on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2). The `binary_contents` is a dictionary (associative array or map) containing the mappings of the binary contents, the `priority_levels` is an array of the priority levels.

You should specify all these parameters by name because they are not positional arguments.

After the creation of the event data, you can send the event message with the `send_event2(...)` method. You should pass the data as a parameter, and specify it by name.

An example with `binary_contents` and `priority_levels` can be the following:

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

event_data = MessageUtil.create_event_data2(eventstr=operations, binary_contents = contents, priority_levels = levels)
event_reply = await client.send_event2(data = event_data)
```

An other way to send event data is to pass the `eventstr`, `binary_contents` and the `priority_levels` as parameters to the `send_event2(...)` function. This method will create the data and send it to the GDS.

Here is an example:

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

event_reply = await client.send_event2(eventstr=operations, binary_contents = contents, priority_levels = levels)
```

In the `send_event2(...)` method you can omit the `binary_contents` and `priority levels` parameters, but you should specify either the `eventstr` or the `data` parameters or the methods will raise a ValueError.


#### ATTACHMENT-REQUEST message

To select an attachment you should invoke the `create_attachment_request_data4(...)` with the select string you have. This is a positional argument, so you do not need to specify it by name. This method has no additional parameters, so additional details cannot be specified here. After you have created the data, you can send it with the `send_attachment_request4(...)`.

```python
attachmentstr = "SELECT * FROM \"multi_event-@attachment\" WHERE id='ATID2006241023125470' and ownerid='EVNT2006241023125470' FOR UPDATE WAIT 86400"
attachment_data = MessageUtil.create_attachment_request_data4(attachmentstr)
attachment_reply = await client.send_attachment_request4(data = attachment_data)
```

An alternative way to send attachment request message is to pass the select string to the `send_attachment_request4(...)`. With the `send_attachment_request4(...)` method you should specify all parameters by name.

```python
attachmentstr = "SELECT * FROM \"multi_event-@attachment\" WHERE id='ATID2006241023125470' and ownerid='EVNT2006241023125470' FOR UPDATE WAIT 86400"
attachment_reply = await client.send_attachment_request4(attachstr = attachmentstr)
```

The `send_attachment_request4(...)` method will return with the response. The GDS will send you an attachment request ack message, and if it contains the attachment, the method will return with this message. But if the attachment request ack does not have the attachment, the method will wait for the attachment response message, and will return with that.

You should specify etiher the `data` or the `attachstr` parameters or the method will raise a ValueError.

#### QUERY message

For a select query, you should invoke the `create_query_request_data10(..)` method with the select string you have. There are two optional parameters, one stands for the consistency type (by default set to `"PAGES"`), and one for the time-out. Its default value is one minute (`60000` ms). You should specify all parameters by name: `querystr`, `consistency` and `timeout`.

Details about their values can be found on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request---Data-Type-10).

After you have created the data, you should send it with the `send_query_request10(...)` method.

```python
querystr = "SELECT * FROM multi_event"
query_data = MessageUtil.create_query_request_data10(querystr=querystr, consistency="NONE", timeout=100)
query_reply, more_page = await client.send_query_request10(data=query_data)
```

You can also send query request by invoking the `send_query_request10(...)` method and passing the `querystr`, `consistency` and `timeout` patameters to it. With the `send_query_request10(...)` and the `create_query_request_data10(...)` you should specify the parameters by name.

```python
querystr = "SELECT * FROM multi_event"
query_reply, more_page = await client.send_query_request10(querystr=querystr, consistency="NONE", timeout=100)
```

In the `send_query_request10(...)` method you can omit the `consistency` and `timeout` parameters, but you should specify either the `querystr` or the `data` parameters or the methods will raise a ValueError.

The GDS will return only one page (by default it means 300 records). If you want more page, not just the first one, you can send a `next_query_page_request`. Because of this, the `send_query_request10(...)` will return not just with the query request ack but with the `has_more_page` value as well.

You can create the next query page request data with the `create_next_query_page_data12(...)`  method. You should pass the query context descriptor to the method as a positional argument (for more details about that see the [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request-ACK---Data-Type-11)). Optionally you can pass the timeout parameter as well. But you should sepcify it by name. After creation of the data you can send it with the `send_next_query_page12(...)` method.

You do not have to bother with creating the data, you can pass the query request ack message to the `send_next_query_page12(...)` method. You should specify it by name: `prev_page`.

The `send_next_query_page12(...)` method will return with the query request ack message and the `has_more_page` value. So you can query all page like this:

```python
querystr = "SELECT * FROM multi_event"
query_reply, more_page = await client.send_query_request10(querystr=querystr, consistency="NONE", timeout=100)
print(query_reply)
while(more_page):
    query_reply, more_page = await client.send_next_query_page12(prev_page=query_reply)
    print(query_reply)
```

You should specify either the `data` or the `prev_page` parameters or the `send_next_query_page12(...)` method will raise a ValueError.

### Sending custom messages

If you want to send custom messages, first you should create the data part as you can see it above. After that you should create the header. You can do that with the `create_header(...)` method. The `create_header(...)` has one positional argument and you can specify many argument by name. The positional argument is the DataType of the message.

The DataTypes are the following:
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

There are many parameters you can specify by name:

  - 'username', by default: "user"
  - 'msgid', the id of the message.
  - 'create_time'
  - 'request_time'
  - 'fragmented', by default: False
  - 'first_fragment'
  - 'last_fragment'
  - 'offset'
  - 'full_data_size'

If you want more details about the header, see the [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Headers). Here is an example of the header creation:

```python
header = MessageUtil.create_header(DataType.QUERY_REQUEST, username="customuser")
```

After the creation of the data and the header you can send the message with the appropriate `send...` method:

```python
querystr = "SELECT * FROM multi_event"
query_data = MessageUtil.create_query_request_data10(querystr=querystr, consistency="NONE", timeout=100)
header = MessageUtil.create_header(DataType.QUERY_REQUEST, username="customuser")
query_reply, more_page = await client.send_query_request10(data = query_data, header = header)
```
