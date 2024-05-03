
# Networked Chat, File Transfer, and Quiz Application

This project repository contains a set of Python scripts that enable communication between clients and a server over a network. The application supports group chat functionality, file transfer capabilities, and the ability to conduct quizzes.

## Setup and Usage

### Prerequisites
- Python 3.x installed on your system.
- Basic understanding of Python programming and networking concepts.

### Installation
1. Clone this repository to your local machine:

```
git clone <repository_url>
```

2. Navigate to the directory containing the cloned repository:

```
cd <repository_directory>
```

### Server and Client setup

#### Server Setup
1. Open a terminal and navigate to the directory containing the server script (`server.py`).
2. Run the server script with the following command:

```
python server.py [PORT] [HOST]
```

   Replace `[PORT]` with the desired port number and `[HOST]` with the server's host address. If no arguments are provided, the default values are used (localhost and port 10000).

#### Client Setup
1. Open a terminal and navigate to the directory containing the client script (`client.py`).
2. Run the client script with the following command:

```
python client.py [PORT] [HOST]
```

   Replace `[PORT]` and `[HOST]` with the same values used for setting up the server.

### User Authentication

- Once the setup is done, the client will be prompted check if the user is already registered or not.
- Then the client will be prompted to enter a unique username and password.
- For already registered users, the server will validate user by password and only then let it use the application else disconnect that client.

### Group/Private Chat

#### Usage
- Once the client is connected to the server, you can send messages to the group chat by typing them into the terminal and pressing Enter.
- The format for sending messages is as follows:
-- from client to server:
```
msg:your message
```
--from client to another client:
```
to:recipient_name:your message
```
replace recipient name with name of the client you want to send message to.
-- from server to clients: simply type the message and press enter
```
your message
```
- To disconnect from the server, type `cmd:disconnect` and press Enter or use the keyboard interrupt (`Ctrl + C`).

### File Transfer

#### Server Setup
Follow the same steps as for setting up the server for group chat.

#### Client Setup
Follow the same steps as for setting up the client for group chat.

#### Usage
- For sending file from client to server ensure that the desired file is in the same directory as the `client.py` script.
- To send a file from the client to the server, use the following command format:

```
file_transfer:file_to_server:filename
```

   Replace `filename` with the name of the file you want to send.


- To send a file from a client to another client, use the following command format:

```
file_transfer:file_to:recipient_name:filename
```
Replace the filename with the name of file you want to send and the recipient_name with the name of client you want to send file to.
    

- To download a file sent by the client, the server will initiate the transfer by receiving the file with appropriate instructions and storing the files sent by each client in respective directory.

- To send a file from server to clients, use the following command format:

```
send_file:recipient:directory_name:file_name
```
Replace directory_name and file_name with appropriate directory and file names and the recipient field can either be all or username of particular client

### Quiz

#### Server Setup
Follow the same steps as for setting up the server for group chat.

#### Client Setup
Follow the same steps as for setting up the client for group chat.

#### Usage
- To conduct a quiz, initiate the quiz on the server terminal with the following command:

```
Quiz:quiz_files_dir:quiz_ques.txt:quiz_ans.txt:quiz_score_file.csv
```

   Replace `quiz_files_dir`, `quiz_ques.txt`, `quiz_ans.txt`, and `quiz_score_file.csv` with the appropriate directory and file names.

- Clients can submit their answers to the server using the following command format:

```
quiz_answer:<answer1> <answer2> <answer3>
```

   Replace `<answer1>`, `<answer2>`, and `<answer3>` with the answers to the quiz questions.

## Additional Notes
- Make sure the server is running before attempting to connect clients.
- Ensure that firewalls or network configurations allow communication over the specified port.
- The application is intended for educational purposes and may require modifications for production use.

## Contributors
- [Vivek Sapkal, B22AI066](https://github.com/viveksapkal2793)
