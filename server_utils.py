import struct
import os

def encode_message(header, message):
    """Encode a message with a header and payload length.

    Input Arguments:
    - header (str): The message header.
    - message (str): The message payload.

    Output Arguments:
    - bytes: Encoded message.
    """
    header_length = len(header).to_bytes(2, byteorder="big")
    payload_length = len(message).to_bytes(4, byteorder="big")
    return header_length + header.encode() + payload_length + message.encode()


def decode_message(client_socket):
    """Decode a message from a client socket.

    Input Arguments:
    - client_socket (socket): The client socket.

    Output Arguments:
    - tuple: A tuple containing header and payload.
    """
    header_length = client_socket.recv(2)
    header_length = struct.unpack("!H", header_length)[0]
    header = client_socket.recv(header_length).decode()

    payload_length = client_socket.recv(4)
    payload_length = struct.unpack("!I", payload_length)[0]
    payload = client_socket.recv(payload_length).decode()

    return header, payload


def validate_message(header):
    """Validate if a message header is valid.

    Input Arguments:
    - header (str): The message header.

    Output Arguments:
    - bool: True if the header is valid, False otherwise.
    """
    return header in ["msg", "cmd", "to", "info", "file_transfer", "quiz_answer", "quiz_question"]


def broadcast_message(header, message, CLIENTS, exclude_client=None):
    """Broadcast a message to all clients except the excluded one.

    Input Arguments:
    - header (str): The message header.
    - message (str): The message to broadcast.
    - CLIENTS (list): List of client sockets and addresses.
    - exclude_client (socket): The client socket to exclude from broadcasting.

    Output Arguments:
    - None
    """
    encoded_message = encode_message(header, message)
    for client, _ in CLIENTS:
        if client is not exclude_client:
            client.sendall(encoded_message)


def send_message_to_client(recipient_name, message, sender, ACTIVE_USERS, CLIENTS):
    """Send a message to a specific client.

    Input Arguments:
    - recipient_name (str): The username of the recipient.
    - message (str): The message to send.
    - sender (str): The username of the sender.
    - ACTIVE_USERS (dict): Dictionary of active users and their addresses.
    - CLIENTS (list): List of client sockets and addresses.

    Output Arguments:
    - None
    """
    recipient_addr = list(ACTIVE_USERS.keys())[list(ACTIVE_USERS.values()).index(recipient_name)]
    for client, address in CLIENTS:
        if address[0] == recipient_addr[0]:
            encoded_message = encode_message("info", f"{sender} (private): {message}\n")
            client.sendall(encoded_message)


def send_file_to_client(recipient_name, filename, sender_socket, username, ACTIVE_USERS, CLIENTS):
    """Send a file to a specific client.

    Input Arguments:
    - recipient_name (str): The username of the recipient.
    - filename (str): The name of the file to send.
    - sender_socket (socket): The socket of the sender.
    - username (str): The username of the sender.
    - ACTIVE_USERS (dict): Dictionary of active users and their addresses.
    - CLIENTS (list): List of client sockets and addresses.

    Output Arguments:
    - None
    """
    recipient_addr = list(ACTIVE_USERS.keys())[list(ACTIVE_USERS.values()).index(recipient_name)]

    for client, address in CLIENTS:

        if address[0] == recipient_addr[0] and address[1] == recipient_addr[1]:

            encoded_message = encode_message("file_transfer", f"file_to:{username}:{filename}\n")
            client.sendall(encoded_message)

            directory_name = username

            file_path = os.path.join(os.getcwd(), directory_name, filename)

            if not os.path.exists(directory_name):
                os.makedirs(directory_name)

            with open(file_path, "wb") as file:
                while True:
                    data = sender_socket.recv(1024)
                    if not data:
                        break
                    if data.endswith(b'EOF'):  # Check for end of file marker
                        file.write(data[:-3])  # Write all data except the EOF marker
                        break
                    file.write(data)

            with open(file_path, "rb") as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    if data.endswith(b'EOF'):  # Check for end of file marker
                        client.sendall(data)  
                        break
                    client.sendall(data)
                client.sendall(b'EOF')  # Send end of file marker

            encoded_message = encode_message("info", f"Server: File '{filename}' sent to {recipient_name}\n")
            sender_socket.sendall(encoded_message)


def send_files_from_server(recipient_name, filename, directory_name, ACTIVE_USERS, CLIENTS):
    """Send files from the server to a specific client.

    Input Arguments:
    - recipient_name (str): The username of the recipient.
    - filename (str): The name of the file to send.
    - directory_name (str): The name of the directory containing the file.
    - ACTIVE_USERS (dict): Dictionary of active users and their addresses.
    - CLIENTS (list): List of client sockets and addresses.

    Output Arguments:
    - None
    """
    recipient_addr = list(ACTIVE_USERS.keys())[list(ACTIVE_USERS.values()).index(recipient_name)]
    
    for client, address in CLIENTS:

        if address[0] == recipient_addr[0] and address[1] == recipient_addr[1]:

            directory_name = directory_name
            file_path = os.path.join(os.getcwd(), directory_name, filename)
            
            with open(file_path, "rb") as file:
                while True:
                    data = file.read(1024)
                    if not data:
                        break
                    if data.endswith(b'EOF'):  # Check for end of file marker
                        client.sendall(data)  
                        break
                    client.sendall(data)
                client.sendall(b'EOF')  # Send end of file marker

            print(f"Server: File '{filename}' sent to {recipient_name}\n")
            encoded_message = encode_message("info", f"Server: File '{filename}' sent to {recipient_name}\n")
            client.sendall(encoded_message)


def upload_file_from_client(filename, username, client_socket, CLIENTS):
    """Upload a file from a client to the server.

    Input Arguments:
    - filename (str): The name of the file to upload.
    - username (str): The username of the client uploading the file.
    - client_socket (socket): The socket of the client.
    - CLIENTS (list): List of client sockets and addresses.

    Output Arguments:
    - None
    """
    directory_name = username

    file_path = os.path.join(os.getcwd(), directory_name, filename)

    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

    with open(file_path, "wb") as file:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            if data.endswith(b'EOF'):  # Check for end of file marker
                    file.write(data[:-3])  # Write all data except the EOF marker
                    break
            file.write(data)

    broadcast_message("info", f"Server: File '{filename}' uploaded by {username}\n", CLIENTS)


def read_quiz_questions(directory_name, filename, answer_file):
    """Read quiz questions and answers from files.

    Input Arguments:
    - directory_name (str): The name of the directory containing the files.
    - filename (str): The name of the file containing quiz questions.
    - answer_file (str): The name of the file containing quiz answers.

    Output Arguments:
    - tuple: A tuple containing quiz questions, options, and answers.
    """
    quiz_questions = []
    quiz_options = []

    file_path = os.path.join(os.getcwd(), directory_name, filename)

    with open(file_path, 'r') as file:

        lines = file.readlines()
        question = ""
        options = []
        for line in lines:
            line = line.strip()
            if line:
                if line.startswith("a.") or line.startswith("b.") or line.startswith("c.") or line.startswith("d."):
                    options.append(line)
                else:
                    if question:
                        quiz_questions.append(question)
                        quiz_options.append(options)
                        question = ""
                        options = []
                    question = line
        if question:
            quiz_questions.append(question)
            quiz_options.append(options)

    file_path = os.path.join(os.getcwd(), directory_name, answer_file)

    with open(file_path, 'r') as file:
        answers = file.read().strip().split()

    return quiz_questions, quiz_options, answers


def start_quiz(directory_name, filename, answer_file, CLIENTS):
    """Start a quiz by sending questions to clients.

    Input Arguments:
    - directory_name (str): The name of the directory containing the quiz files.
    - filename (str): The name of the file containing quiz questions.
    - answer_file (str): The name of the file containing quiz answers.
    - CLIENTS (list): List of client sockets and addresses.

    Output Arguments:
    - list: List of correct answers.
    """
    quiz_questions, quiz_options, answers = read_quiz_questions(directory_name, filename, answer_file)

    # Concatenate all questions and options into a single message
    quiz_message = ""
    for i, question in enumerate(quiz_questions):
        question_message = f"Question {i+1}: {question}\n\nOptions: {' '.join(quiz_options[i])}\n\n-----------------------------\n\n"
        quiz_message += question_message

    # Send quiz message to all clients
    broadcast_message("quiz_question", quiz_message, CLIENTS)

    return answers


def evaluate_quiz(answer, filename, client_socket, client_name, ANSWERS):
    """Evaluate quiz answers and store scores.

    Input Arguments:
    - answer (str): The answers received from clients.
    - filename (str): The name of the file to store scores.
    - client_socket (socket object): client socket object.
    - client_name (string): username of client.
    - ANSWERS (list): List of correct answers.

    Output Arguments:
    - None
    """
    # Receive answers from clients and evaluate
    scores = {}
    scores[client_name] = 0
    answers = answer.split()  # Split the string into individual answers
    correct_answer = ANSWERS

    for i in range(len(ANSWERS)):
        if answers[i].lower() == correct_answer[i]:
           scores[client_name] += 1

    directory_name = "all_quiz_scores"
    file_path = os.path.join(os.getcwd(), directory_name, filename)
    
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
    
    # Store scores in CSV file
    with open(file_path, "a") as csv_file:
        
        for username, score in scores.items():
            csv_file.write(f"{username},{score}\n")

    # Inform clients that quiz is over
    encoded_message = encode_message("info", "Quiz is over. Thank you for participating!\n")
    client_socket.sendall(encoded_message)
