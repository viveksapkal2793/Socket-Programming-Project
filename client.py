import socket
import sys
import threading
import client_utils

# Usage: ./client.py [PORT] [HOST]

if __name__ == "__main__":

    if len(sys.argv) == 1:
        HOST = ("localhost", 10000)
    elif len(sys.argv) == 2:
        HOST = ("localhost", int(sys.argv[1]))
    else:
        HOST = (sys.argv[2], int(sys.argv[1]))

    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        main_socket.connect(HOST)
        sys.stdout.write("Connected to " + HOST[0] + ":" + str(HOST[1]) + '\n')
        sys.stdout.flush()
    except:
        sys.stdout.write("Could not connect to " + HOST[0] + ":" + str(HOST[1]) + '\n')
        sys.stdout.flush()
        exit(2)

    if client_utils.authenticate(main_socket):

        receive_thread = threading.Thread(target=client_utils.receive_messages, args=(main_socket,))
        # receive_thread.daemon_threads = True  # Set the thread as daemon    
        receive_thread.start()
    
    else:
        sys.stdout.write("Could not connect to " + HOST[0] + ":" + str(HOST[1]) + '\n')
        sys.stdout.flush()
        exit(2)

    while True:
        try:
            msg = input()
            if ':' not in msg:
                continue
            header, message = msg.split(":", 1)
            encoded_message = client_utils.encode_message(header, message)
            main_socket.sendall(encoded_message)

            if header == 'cmd' and message == 'disconnect':
                break

            elif header == 'file_transfer' and message.startswith('file_to_server'):

                client_utils.send_file(filename=message.split(":")[1], main_socket=main_socket)

            elif header == 'file_transfer' and message.startswith('file_to'):
                
                client_utils.send_file(filename=message.split(":")[2], main_socket=main_socket)
                
        except KeyboardInterrupt:
            encoded_message = client_utils.encode_message("cmd", "disconnect")
            main_socket.sendall(encoded_message)
            break
    
    receive_thread.join()
    main_socket.close()