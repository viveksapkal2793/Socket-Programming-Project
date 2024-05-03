import socketserver
import sys
import threading
import hashlib
import sqlite3
import server_utils

# Usage: ./server.py [PORT] [HOST]

USERS = {}
ACTIVE_USERS = {}
CLIENTS = []
ANSWERS = []
quiz_score_file = None

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP Server class."""
    pass

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Threaded TCP Request Handler class."""
    
    def __init__(self, request, client_address, server):
        """Initialize with database connection."""
        self.db_connection = sqlite3.connect('users.db')
        super().__init__(request, client_address, server)

    def authenticate(self, client_socket):
        """Authenticate clients based on whether they are registered or not.
        
        Input Arguments:
        - client_socket (socket): The client socket.
        
        Output Arguments:
        - bool: True if authentication is successful, False otherwise.
        """
        client_socket.sendall(server_utils.encode_message("info", "Are you already registered? (yes/no):"))
        header, response = server_utils.decode_message(client_socket)

        if header != "info":
            return False
    
        if response.lower() == "no":

            while True:
                header, username = server_utils.decode_message(client_socket)

                if self.check_unique_username(username):
                    client_socket.sendall(server_utils.encode_message("info", "Username registered successfully."))  
                    break
                else:
                    client_socket.sendall(server_utils.encode_message("info", "Username already exists. Please choose another: "))
            
            header, password = server_utils.decode_message(client_socket)
            
            # Hash the password before storing it
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            self.add_user_to_database(username, hashed_password)
            USERS[username] = hashed_password
            ACTIVE_USERS[self.client_address] = username

            return True
        
        elif response.lower() == "yes":

            header, username = server_utils.decode_message(client_socket)
            header, password = server_utils.decode_message(client_socket)

            # Validate username and password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            if self.validate_user_credentials(username, hashed_password):
                ACTIVE_USERS[self.client_address] = username
                return True
            else:
                client_socket.sendall(server_utils.encode_message("info", "Invalid username or password."))
                return False
            
        else:
            client_socket.sendall(server_utils.encode_message("info", "Invalid response."))
            return False

    def check_unique_username(self, username):
        """Check if a username is unique.
        
        Input Arguments:
        - username (str): The username to check.
        
        Output Arguments:
        - bool: True if the username is unique, False otherwise.
        """
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        cursor.close()
        return result is None

    def add_user_to_database(self, username, hashed_password):
        """Add a new user to the database.
        
        Input Arguments:
        - username (str): The username of the new user.
        - hashed_password (str): The hashed password of the new user.
        
        Output Arguments:
        - None
        """
        cursor = self.db_connection.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        self.db_connection.commit()
        cursor.close()

    def validate_user_credentials(self, username, hashed_password):
        """Validate user credentials against the database.
        
        Input Arguments:
        - username (str): The username to validate.
        - hashed_password (str): The hashed password to validate.
        
        Output Arguments:
        - bool: True if the credentials are valid, False otherwise.
        """
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def handle_command(self, payload, client_socket):
        """Handle commands sent by the server to clients.
        
        Input Arguments:
        - payload (str): The command payload.
        - client_socket (socket): The client socket.
        
        Output Arguments:
        - None
        """
        if payload == "disconnect":
            client_socket.close()
            user = ACTIVE_USERS[self.client_address]

            ACTIVE_USERS.pop(self.client_address)
            CLIENTS.remove((client_socket, self.client_address))

            server_utils.broadcast_message("info", f"Server: Client {user} left the server.\n", CLIENTS)
            print(f"Client {user} disconnected.")
            print("=================")
            
            
    def handle_file_transfer(self, payload, client_socket, username):
        """Handle file transfer requests.
        
        Input Arguments:
        - payload (str): The file transfer payload.
        - client_socket (socket): The client socket.
        - username (str): The username of the sender.
        
        Output Arguments:
        - None
        """
        if payload.startswith("file_to_server"):
            server_utils.upload_file_from_client(payload.split(":")[1], username, client_socket, CLIENTS)

        elif payload.startswith("file_to"):
            recipient, filename = payload.split(":")[1:]
            server_utils.send_file_to_client(recipient, filename, client_socket, username, ACTIVE_USERS, CLIENTS)


    def handle(self):
        """Handle client requests.
        
        Input Arguments:
        - None
        
        Output Arguments:
        - None
        """
        client_socket = self.request
        CLIENTS.append((client_socket, self.client_address))

        if not self.authenticate(client_socket):
            CLIENTS.remove((client_socket, self.client_address))
            return
        
        welcome_msg = "Server: You joined the server.\n"
        client_socket.sendall(server_utils.encode_message("info", welcome_msg))
        
        server_utils.broadcast_message("info", f"Server: Client {ACTIVE_USERS[self.client_address]} joined the server.\n", CLIENTS, exclude_client=client_socket)
        
        while True:
            
            try:
                
                header, payload = server_utils.decode_message(client_socket)
                
                if server_utils.validate_message(header):
                    print("=================")

                    if header == "msg":
                        
                        server_utils.broadcast_message("msg", f"Client {ACTIVE_USERS[self.client_address]}: {payload}\n", CLIENTS, exclude_client=client_socket)
                        print(f"Client {ACTIVE_USERS[self.client_address]}: {payload}")

                    elif header == "cmd":
                        self.handle_command(payload, client_socket)
                        if payload == "disconnect":
                            break
                    
                    elif header == "file_transfer":
                        self.handle_file_transfer(payload, client_socket, ACTIVE_USERS[self.client_address])

                    elif header == "to":

                        recipient, message = payload.split(":", 1)
                        server_utils.send_message_to_client(recipient, message, ACTIVE_USERS[self.client_address], ACTIVE_USERS, CLIENTS)
                    
                    elif header == "quiz_answer":
                        server_utils.evaluate_quiz(payload, quiz_score_file, client_socket, ACTIVE_USERS[self.client_address], ANSWERS)
                        pass
                        
                    else:
                        print("Unknown header:", header)

                else:
                    invalid_message = "Server: Invalid message format. Please adhere to the message protocol.\n"
                    client_socket.sendall(server_utils.encode_message("error", invalid_message))

            except Exception as e:
                print("Error:", e)
                break

        # Close database connection when handler exits
        self.db_connection.close()

if __name__ == "__main__":

    # Create users table in the database if it doesn't exist
    db_connection = sqlite3.connect('users.db')
    cursor = db_connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
    db_connection.commit()
    cursor.close()

    if len(sys.argv) == 1:
        HOST = ("localhost", 10000)
    elif len(sys.argv) == 2:
        HOST = ("localhost", int(sys.argv[1]))
    else:
        HOST = (sys.argv[2], int(sys.argv[1]))

    server = ThreadedTCPServer(HOST, ThreadedTCPRequestHandler)
    server.daemon_threads = True

    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    print("Server is up.")
    print("=================")
    
    while True:
        try:
            message = input().strip()

            if message == "shutdown":
                for client, _ in CLIENTS:
                    encoded_message = server_utils.encode_message("info", "Server is shutting down.\n")
                    client.sendall(encoded_message)
                server.shutdown()
                server.server_close()
                print("Server is closed.")
                break

            elif message.startswith("send_file:"):

                _, recipient, directory_name, filename = message.split(":", 3)

                if recipient == "all":
                    # Send file to all clients
                    for client, recipient_addr in CLIENTS:

                        recipient_name = ACTIVE_USERS[recipient_addr]

                        encoded_message = server_utils.encode_message("file_transfer", f"file from server:{filename}\n")
                        client.sendall(encoded_message)

                        server_utils.send_files_from_server(recipient_name, filename, directory_name, ACTIVE_USERS, CLIENTS)

                else:
                    # Send file to a particular client
                    recipient_addr = list(ACTIVE_USERS.keys())[list(ACTIVE_USERS.values()).index(recipient)]
                    
                    for client, address in CLIENTS:
                        if address[0] == recipient_addr[0] and address[1] == recipient_addr[1]:

                            encoded_message = server_utils.encode_message("file_transfer", f"file from server:{filename}\n")
                            client.sendall(encoded_message)
                            
                            server_utils.send_files_from_server(recipient, filename, directory_name, ACTIVE_USERS, CLIENTS)
                            break
            
            elif message.startswith("Quiz"):
                directory_name, filename, answer_file, quiz_score_file = message.split(":")[1:]
                ANSWERS = server_utils.start_quiz(directory_name, filename, answer_file, CLIENTS)

            else:
                server_utils.broadcast_message("info", f"Server: {message}\n", CLIENTS)
                print(f"Server: {message}")

        except KeyboardInterrupt:

            for client, _ in CLIENTS:
                encoded_message = server_utils.encode_message("info", "Server is shutting down.\n")
                client.sendall(encoded_message)

            server.shutdown()
            server.server_close()
            print("Server is closed.")
            break
