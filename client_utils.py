import struct
import os


def receive_messages(main_socket):
    """Receive and process messages from the server.

    Input Arguments:
    - main_socket (socket): The main socket used for communication.

    Output Arguments:
    - None
    """
    while True:
        try:
            header, payload = decode_message(main_socket)

            if validate_message(header):
                print("=================")

                if header == "file_transfer" and (payload.startswith("file_to") or payload.startswith("file from server")):
                    print(payload, end="")

                    if payload.startswith("file_to"):
                        sender, filename = payload.split(":")[1:]
                    else:
                        filename = payload.split(":")[1]
                        sender = 'Server'

                    receive_file_from_server(filename, main_socket, sender)
        
                else:
                    print(payload, end="")

            else:
                print("Invalid message received:", payload)

        except Exception as e:
            print("Error:", e)
            break


def encode_message(header, message):
    """Encode a message for sending over the network.

    Input Arguments:
    - header (str): The header of the message.
    - message (str): The payload of the message.

    Output Arguments:
    - bytes: The encoded message.
    """
    header_length = len(header).to_bytes(2, byteorder="big")
    payload_length = len(message).to_bytes(4, byteorder="big")
    return header_length + header.encode() + payload_length + message.encode()


def decode_message(main_socket):
    """Decode a message received over the network.

    Input Arguments:
    - main_socket (socket): The main socket used for communication.

    Output Arguments:
    - tuple: A tuple containing the header and payload of the decoded message.
    """
    header_length = main_socket.recv(2)
    header_length = struct.unpack("!H", header_length)[0]
    header = main_socket.recv(header_length).decode()

    payload_length = main_socket.recv(4)
    payload_length = struct.unpack("!I", payload_length)[0]
    payload = main_socket.recv(payload_length).decode()

    return header, payload


def validate_message(header):
    """Validate the header of a received message.

    Input Arguments:
    - header (str): The header of the message.

    Output Arguments:
    - bool: True if the message is valid, False otherwise.
    """
    if header == "msg":
        return True
    elif header in ["info", "error", "file_transfer", "quiz_question", "quiz_answer"]:
        return True  # Allow these headers for system messages
    else:
        return False


def authenticate(main_socket):
    """Authenticate the client with the server.

    Input Arguments:
    - main_socket (socket): The main socket used for communication.

    Output Arguments:
    - bool: True if authentication is successful, False otherwise.
    """
    header, response = decode_message(main_socket)

    if header != "info":
        return False
    
    print(response)

    if response.endswith("(yes/no):"):

        choice = input().strip().lower()
        main_socket.sendall(encode_message("info", choice))

        if choice == "no":

            main_socket.sendall(encode_message("info", input("Enter a username: ").strip()))
            header, message = decode_message(main_socket)
            
            while message != "Username registered successfully.":
                
                main_socket.sendall(encode_message("info", input({message}).strip()))  
                header, message = decode_message(main_socket)

            main_socket.sendall(encode_message("info", input("Enter a password: ").strip()))

        elif choice == "yes":
            main_socket.sendall(encode_message("info", input("Enter your username: ").strip()))
            main_socket.sendall(encode_message("info", input("Enter your password: ").strip()))

        else:
            print("Invalid choice.")
            return False
    else:
        print("Invalid response.")
        return False
    
    return True


def receive_file_from_server(filename, main_socket, sender):
    """Receive a file from the server.

    Input Arguments:
    - filename (str): The name of the file.
    - main_socket (socket): The main socket used for communication.
    - sender (str): The sender of the file.

    Output Arguments:
    - None
    """
    with open(filename, "wb") as file:
        while True:
            data = main_socket.recv(1024)
            if not data:
                break
            if data.endswith(b'EOF'):  # Check for end of file marker
                file.write(data[:-3])  # Write all data except the EOF marker  
                break

            file.write(data)

    print(f"File '{filename}' received from {sender}.\n")


def send_file(filename, main_socket):
    """Send a file to the server.

    Input Arguments:
    - filename (str): The name of the file to send.
    - main_socket (socket): The main socket used for communication.

    Output Arguments:
    - None
    """
    file_path = os.path.join(os.getcwd(), filename)
    
    with open(file_path, "rb") as file:
        while True:
            data = file.read(1024)
            if not data:
                break
            if data.endswith(b'EOF'):  # Check for end of file marker
                main_socket.sendall(data) 
                break
            main_socket.sendall(data)
                    
        main_socket.sendall(b'EOF')  # Send end of file marker
       
    print(f"File '{filename}' sent to server.\n")