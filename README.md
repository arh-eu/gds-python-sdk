- [Installation](#installation)
- [Communication](#communication)
- [Login to the GDS](#login-to-the-gds)
  * [Console Client](#console-client)
    + [Easy mode](#easy-mode)
      - [URL, username, password, timeout](#url--username--password--timeout)
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

##### URL, username, password, timeout

By default, the username `"user"` and the url `"ws://127.0.0.1:8888/gate"` will be used (this assumes that your local computer has a GDS instance or the server simulator running on the port `8888`).

You probably want to specify the url and the username as well, so start the script like this:
```sh
$ python .\simple_client.py -url "ws://192.168.255.254:8080/gate/" -username "john_doe" -query "SELECT * FROM table"
```

The `-url` flag, and the corresponding `URL` value is optional, so is the `USERNAME`, specified by the `-username` flag.
The order of the parameters is not fixed, but you can only use one type of message to be sent from the console.

If you need to specify the password used at login to the GDS as well, the `-password` flag can be used for this.

```sh
$ python .\simple_client.py -url "ws://192.168.255.254:8080/gate/" -username "john_doe" -password "$ecretp4$$w0rD" -query "SELECT * FROM table"
```

Probably you do not want to wait for ever for your replies. You can have a timeout for the response ACK messages, which can be specified with the `-timeout` flag. By default, the value is `30` seconds.

A timeout where the server does not respond to your login request can be the following:

```sh
$ python .\simple_client.py -query "SELECT * FROM table" -timeout 10
Sending <login> message..
Waiting <login> reply..
The given timeout (10 seconds) has passed without any response from the server!
```


If you need help about the usage of the program, it can be printed by the `--help` flag.

##### INSERT
To insert into a table, you only have to specify your `INSERT` statement.
The client will print the reply.

```sh
$ python .\simple_client.py -insert "INSERT INTO table(column1, column2) VALUES('a', 42)"
```
##### UPDATE

A simple `UPDATE` statement can be specified by the following command:
```sh
$ python .\simple_client.py -update "UPDATE table SET column1 = 'b' WHERE column1='a'"
```

If you specify an update event, you _have to_ use an ID field in the `WHERE` condition, otherwise your request will not be accepted.

Just as at the `INSERT`, the ACK message will be displayed here as well.

##### MERGE

A simple `MERGE` statement can be specified by the following command:
```sh
$ python .\simple_client.py -merge "MERGE INTO events USING (SELECT 'EVNT202001010000000000' as id, 'ABC123' as numberplate, 100 as speed) I ON (events.id = I.id) WHEN MATCHED THEN UPDATE SET events.speed = I.speed WHEN NOT MATCHED THEN INSERT (id, numberplate) VALUES (I.id, I.numberplate)"
```
The reply will be printed to the console, just as above.

##### DELETE

You cannot specify `DELETE` statements in the GDS.

##### Sending Attachments with Events

The `INSERT`, `UPDATE` and `MERGE` messages are also known as _`EVENT`_ messages. Events can have attachments as well, and you can upload these to the GDS by sending them _with your event_.

The _event ID_ has to follow a format of `"EVNTyyMMddHHmmssSSS0"`, where the first 4 letters are the abbreviation of "event", while the rest specifies a timestamp code from. This will make `"EVNT2006241023125470"` a valid ID in an event table.

The _attachment ID_ has the same restriction, the difference is the prefix. Instead of the `EVNT` you should use `ATID`. The ID for the attachment can be `"ATID2006241023125470"`.

Since the format is these messages have to follow is very strict, you will have to use `hex` values in your event strings for the _binary  IDs_ of your attachments. These `hex` values are unique identifiers for your binaries. To get the `hex` value of a string you can use the console client with the `-hex` flag to print these values. You can also enter multiple names, separating them by semicolon (`;`):

```sh
$ python .\simple_client.py -hex "picture1.bmp;picture3.bmp"
The hex value of `picture1.bmp` is: 0x70696374757265312e626d70
The hex value of `picture3.bmp` is: 0x70696374757265332e626d70
```
These _binary IDs_ (with the `0x` prefix) have to be in your `EVENT` `SQL` string. 

To attach files to your events (named "binary contents") you should use the `-attachments` flag with your `EVENT`.
The attachments are the names of your files found in the `attachments` folder. These names are automatically converted into `hex` values, and the contents of these files will be sent with your message (see the [wiki](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2)).

```sh
#breaking lines only to make it easier to read.
$ python .\simple_client.py -event "INSERT INTO multi_event (id, images) \
VALUES('EVNT2006241023125470', array('ATID2006241023125470')); \
INSERT INTO \"multi_event-@attachment\" (id, meta, data) \
VALUES('ATID2006241023125470', 'image/bmp', 0x70696374757265312e626d70 )" \
-attachments "picture1.bmp"
```

If the file you specify is not present, the client will print an error message without sending the message.

##### SELECT query
A simple `SELECT` query statement can be specified by the following command:
```sh
$ python .\simple_client.py -query "SELECT * FROM table"
```

The rows returned by the GDS will be printed on your output, one record per line.

It is possible, that your query has more than one pages available. By default, only 300 rows will be returned by the GDS (if you do not specify the `LIMIT` in your SQL and the config does not sets another limit for this).
In these cases you have send a Next Query Page request, which will give you the next 300 records found.

If you do not want to bother by manually sending these requests, you can use the `-queryall` flag instead, that will automatically send these Next Query Page requests as long as there are additional pages with records available.

##### SELECT attachment

A simple `SELECT` attachment query statement can be specified by the following command:
```sh
$ python .\simple_client.py -attachment "SELECT * FROM \"events-@attachment\" WHERE id='ATID202001010000000000' and ownerid='EVNT202001010000000000' FOR UPDATE WAIT 86400"
```
Please be careful, as the table name in this examples should be in double quotes, so it should be escaped by backslash, otherwise the parameters will not be parsed right. The reason for this is that the `SQL` standard does not support hyphens in table names, therefore it should be treated differently.

### Detailed mode 

Messages consist two parts, a [header](https://github.com/arh-eu/gds/wiki/Message-Headers) and a [data](https://github.com/arh-eu/gds/wiki/Message-Data).

First you will read about the code structure so you will know how to modify it, then you will see how can you create the headers and data parts, after that you can read how to combine those for a whole message that can be sent.
The followings all assume that the login reply was successful.

#### Class structure

First you should understand the basics of the `WebsocketClient` class. Since the communication over the websocket protocol is asynchronous, most of our methods that send or await messages have to be defined as `async`.

The functions that are processing the replies do not have to be declared `async`, as it is not an asynchronous activity.

The `WebsocketClient` connects to the GDS on the given URL (that can be specified by command line arguments and is passed to the `__init()__` with the `**kwargs` pattern), and if the login was successful it will call the `client_code(..)` method of the class with the active websocket connection descriptor as the parameter. Should the login fail, the client exits with the error message displayed.

Business logic of the client should be implemented in the `client_code(..)` method. When the method returns, the client will close the active websocket connection and exit. Not overriding the `client_code(..)` will result in a `NotImplementedError()`.

The arguments passed (and parsed) to the client are always available through the `args` dictionary found in `self`. These keys will not have the hyphen (`-`) as their prefix, as it will get removed during parsing by the `argparse` module.

As the messages sent in the communication channels have to be packed and unpacked by the `msgpack` library, the `send(..)` and `recv(..)` methods will automatically do these conversions between the `Python` and `msgpack` types.

The `wait_for_reply(..)` method will call the `recv(..)` method, but if there is no response to be received by the timeout set in the client, it will raise a `TimeoutError` so you might want to use this instead of calling the `recv(..)` method itself.

##### Response handlers

The client has some predefined functions which you can override to use custom logic with the (ACK) responses the GDS gives you. These methods are the following:

```python
  def event_ack(self, response: list)

  def attachment_ack(self, response: list) -> bool

  def attachment_response(self, response: list)
  
  def query_ack(self, response: list)
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
    "INSERT INTO events (id, numberplate, speed, images) VALUES('EVNT202001010000000000', 'ABC123', 90, array('ATID202001010000000000'))",
    "INSERT INTO \"events-@attachment\" (id, meta, data) VALUES('ATID202001010000000000', 'some_meta', 0x62696e6172795f6964315f6578616d706c65)"
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
['INSERT INTO events (id, numberplate, speed, images) VALUES(\'EVNT202001010000000000\', \'ABC123\', 90, array(\'ATID202001010000000000\'));INSERT INTO "events-@attachment" (id, meta, data) VALUES(\'ATID202001010000000000\', \'some_meta\', 0x62696e6172795f6964315f6578616d706c65)', {'62696e6172795f69645f6578616d706c65': bytearray(b'\x7f\x7f\x00\x00')}, [[{1: True}]]]
```

##### SELECT query

For a select query, you should invoke the `create_select_query_data(..)` method with the select string you have:
```python
querystr = "SELECT * FROM table"
select_data = GDSClient.MessageUtil.create_select_query_data(querystr)
print(select_data)

#output will be:
["SELECT * FROM table", "PAGES", 60000]
```

There are two optional, named parameters here, one stands for the consistency type (by default set to `"PAGES"`), and one for the time-out.
It's default value is one minute (`60000` ms). These parameters are named `consistency` and `timeout`.

Details about their values can be found on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request---Data-Type-10).

Customized message can be created by:
```python
customquery = GDSClient.MessageUtil.create_select_query_data(querystr, consistency="NONE", timeout=100)
```

##### SELECT attachment
To select an attachment, you should invoke the `create_attachment_query_data(..)` method with the select string you have:

```python
attachmentstr = "SELECT * FROM \"events-@attachment\" WHERE id='ATID202001010000000000' and ownerid='EVNT202001010000000000' FOR UPDATE WAIT 86400")
attachment_data = GDSClient.MessageUtil.create_attachment_query_data(attachmentstr)
```
This method has no additional parameters, so additional details cannot be specified here.

#### Sending custom messages

Once you have a header and a data part, the next step is combining them to have the message which will be sent.

You probably want to send the message and wait for the reply (ACK) as well, so you should use the `send_and_wait_message` method as explained at the start. 

You can use this method by specifying passing the `ws` descriptor, and by giving the `header` and `data` fields the values you have created.

There is also a `callback` parameter, which will get called with the reply of the GDS. You can keep this `None`, in this scenario the response will be ignored.

Since this is an asynchronous call, you should not forget to `await` this response!

```python

  def client_code(self, ws):
    header = GDSClient.MessageUtil.create_header(GDSClient.DataType.QUERY_REQUEST)
    querydata = GDSClient.MessageUtil.create_select_query_data("SELECT * FROM table")

    await self.send_and_wait_message(ws, header=header, data=querydata, callback=self.query_ack)
```

If you do not want to wait for the reply you should invoke the `send_message(..)` instead, without any callbacks given. In this case you do not need to specify the parameters by name, the order of them is `(ws, header, data)`. The `await` keyword can not be omitted though, keep in mind.

```python

  def client_code(self, ws):
    header = GDSClient.MessageUtil.create_header(GDSClient.DataType.EVENT)
    insertdata = GDSClient.MessageUtil.create_select_query_data("INSERT INTO table(row1, row2) VALUES ('a', 'b')")

    await self.send_message(ws, header, insertdata)
```

The `ConsoleClient` is not made for embedded usage, as the sending and receiving methods are not outsourced to separate threads running endlessly with a possible queue behind them, sending messages and creating responses, and calling the appropriate callbacks. Therefore they will block the main thread until the timeout expires.

Sending many requests in a very short time frame could lead to unexpected behavior here, as the order of the replies is not fixed, a request sent later might be processed before the one you sent first, therefore the replies will not arrive in the order of the requests.

If you want to use the client in a bigger application as a module, you should inherit the `WebsocketClient` class and customize it for your needs.