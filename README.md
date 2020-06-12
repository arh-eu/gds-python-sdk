- [Installation](#installation)
- [Login to the GDS](#login-to-the-gds)
- [Communication](#communication)
  * [Console Client](#console-client)
    + [Easy mode](#easy-mode)
      - [URL, username, password](#url--username--password)
      - [INSERT](#insert)
      - [UPDATE](#update)
      - [MERGE](#merge)
      - [SELECT query](#select-query)
      - [SELECT attachment](#select-attachment)
  * [Detailed mode](#detailed-mode)
    + [Message Headers](#message-headers)
    + [Message Data](#message-data)
      - [INSERT, UPDATE, MERGE](#insert--update--merge)
      - [SELECT query](#select-query-1)
      - [SELECT attachment](#select-attachment-1)
    + [Sending custom messages](#sending-custom-messages)


## Installation

To install and use the `Python` library you have to install two components our classes depend on, the MessagePack wrappers for the messages and the WebSocket protocol for the communication.

The first one, the `msgpack` module can be installed by typing `$ pip install msgpack` into your terminal or command line.

For the `websockets` library, you need to enter the `$ pip install websockets` command.

Please keep in mind that you need to have `Python 3.6.1` or newer to install the dependencies.

## Login to the GDS

Login messages are automatically generated and sent when you run the program (when you instantiate a `GDSClient` object). The client waits for the login reply before executing any other command, so you do not have to bother with this.

## Communication

If you want to send messages and receive answers the fastest way, you want to read the [Easy mode](#easy-mode) of the Console Client.

If you want full control over the sent and received messages, you should head to the [Detailed mode](#detailed-mode).

For the SQL support restrictions about the strings you can send read the according [Wiki page](https://github.com/arh-eu/gds/wiki/SQL-support-and-restrictions).
### Console Client

#### Easy mode
If you go with the easy mode, you do not have to know or worry about how to write `python` code in order to use the client.

The easy mode will send the message you specify, and will await for the corresponding ACK messages and print them to your console (see more about them [here](https://github.com/arh-eu/gds/wiki/Message-Data)).

##### URL, username, password

By default, the username `"user"` and the url `"ws://127.0.0.1:8080/gate"` will be used (this assumes that your local computer has a GDS instance or the server simulator running on the port `8080`).

You probably want to specify the url and the username as well, so start the script like this:
```sh
$ python .\simple_client.py -url "ws://192.168.255.254:8080/gate/" -username "john_doe" -query "SELECT * FROM table"
```

The `-url` flag, and the corresponding `URL` value is optional, so is the `USERNAME`, specified by the `-username` flag.
The order of the parameters is not fixed, but you can only use one type of message to be sent from the console.

If you need to specify the password used at login to the GDS as well, the `-password` flag can be used for this.

If you need help about the usage, the syntax can be printed by the `--help` flag.

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

Just as at the `INSERT`, the ACK message will be displayed here as well.

##### MERGE

A simple `MERGE` statement can be specified by the following command:
```sh
$ python .\simple_client.py -merge "MERGE INTO events USING (SELECT 'EVNT202001010000000000' as id, 'ABC123' as numberplate, 100 as speed) I ON (events.id = I.id) WHEN MATCHED THEN UPDATE SET events.speed = I.speed WHEN NOT MATCHED THEN INSERT (id, numberplate) VALUES (I.id, I.numberplate)"
```
The reply will be printed to the console, just as above.

##### SELECT query
A simple `SELECT` query statement can be specified by the following command:
```sh
$ python .\simple_client.py -query "SELECT * FROM table"
```

The rows returned by the GDS will be printed on your output, one record per line.

##### SELECT attachment

A simple `SELECT` attachment query statement can be specified by the following command:
```sh
$ python .\simple_client.py -attachment "SELECT * FROM \"events-@attachment\" WHERE id='ATID202001010000000000' and ownerid='EVNT202001010000000000' FOR UPDATE WAIT 86400"
```
Please be careful, as the table name in this examples should be in double quotes, so it should be escaped by backslash, otherwise the parameters will not be parsed right.

### Detailed mode 

Messsages consist two parts, a [header](https://github.com/arh-eu/gds/wiki/Message-Headers) and a [data](https://github.com/arh-eu/gds/wiki/Message-Data).

First you will see how can you create them, after that you can read how to combine those for a whole message that can be sent.

The followings all assume that the login reply was successful and you have the `client` variable available for the communication.

```python
    # these will be parsed from the command line arguments
    login_info = {
        "url": "ws://127.0.0.1:8080/gate",
        "username": "user",
        "password": None
    }

    # keep in mind that the client will send the login (connection) message,
    # and await the according reply (ACK), so this will block
    client = ExampleClient(login_info)
```

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
, where `"<msgid>"` is a randomly generated `UUID` string, and `<now>` stands for the current time in milliseconds. Keep in mind that message IDs have to follow the UUID format to be accepted.


The creation of a header message with the username `"john_doe"` for a query message can be created like this:
```python
header = GDSClient.MessageUtil.create_header(GDSClient.DataType.QUERY_REQUEST, username="john_doe")
```

The signature of the `create_header(..)` method can be read here:
```python
def create_header(header_type, username="user", msgid=None, create_time=None, request_time=None,
    fragmented=False, first_fragment=None, last_fragment=None, offset=None, full_data_size=None)
```

For the accepted values and restrictions on the format of the header do not forget to check the [GDS Wiki](https://github.com/arh-eu/gds/wiki/Message-Headers).

#### Message Data

The data part can be created by the `MessageUtil` class as well, based on what type of message you want to send.

Similar to the headers, these use default values to simplify the calls for the general usage.

##### INSERT, UPDATE, MERGE

The INSERT, UPDATE and MERGE messages have the same format, since they are all _event_ messages. This means, all three can be created by the `create_event_data(..)` method.

The string of the operations should be separated by the semicolon character (`;`). If there is only one operation, you do not need to bother with it, otherwise use it as separator.

The signature of this is:
```python
def create_event_data(eventstr, binary_contents={}, priority_levels=[])
```

The `binary_contents` and `priority_levels` are detailed on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Event---Data-Type-2). The former is a dictionary (associative array or map) containing the mappings of the binary contents, the latter is an array of the priority levels.

An example with binary contents and priority levels can be the following:

```python
operations = ";".join([
    "INSERT INTO events (id, numberplate, speed, images) VALUES('EVNT202001010000000000', 'ABC123', 90, array('ATID202001010000000000'))",
    "INSERT INTO \"events-@attachment\" (id, meta, data) VALUES('ATID202001010000000000', 'some_meta', 0x62696e6172795f6964315f6578616d706c65)"
])

binary_contents = {
    "62696e6172795f69645f6578616d706c65" : bytearray([127, 127, 0, 0])
}

priority_levels = [
    [
        {1:True}
    ]
]

event_data = GDSClient.MessageUtil.create_event_data(operations, binary_contents, priority_levels)
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

There are two, optional parameters here, one stands for the consistency type (by default set to `"PAGES"`), and one for the time-out.
It's default value is one minute (`60000` ms). These parameters are named `consistency` and `timeout`.

Details about their values can be found on their [Wiki page](https://github.com/arh-eu/gds/wiki/Message-Data#Query-Request---Data-Type-10).

Signature is:
```python
def create_select_query_data(querystr, consistency="PAGES", timeout=60000)
```

##### SELECT attachment
To select an attachment, you should invoke the `create_attachment_query_data(..)` method with the select string you have:

```python
attachmentstr = "SELECT * FROM \"events-@attachment\" WHERE id='ATID202001010000000000' and ownerid='EVNT202001010000000000' FOR UPDATE WAIT 86400")
attachment_data = GDSClient.MessageUtil.create_attachment_query_data(attachmentstr)
```
This method has no additional parameters, so additional details cannot be specified here.


The method signature therefore is:
```python
def create_attachment_query_data(attachmentstr)
```

#### Sending custom messages

Once you have a header and a data part, the next step is combining them to have the message which will be sent.

Just as until now, you should look for the `MessageUtil` class.

The method needed here is:
```python
def create_message_from_header_and_data(header, data)
```

This will combine the header and data parts and return the combined message.

If you only want to customize the data, without any additional information changed in the header, you can use a method for this as well.

The signature is:
```python
def create_message_from_data(header_type, data)
```