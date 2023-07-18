# NSCOM01 MACHINE PROJECT - PEREZ, JARAMILLO

# The following imports the necessary modules and defines some constants and dictionaries used in the TFTP client
import tkinter as tk
from tkinter import filedialog
from tkinter import scrolledtext
import socket
import datetime
import os


SERVER_PORT = 69
HEADER_SIZE = 4
DATA_SIZE = 512
BLK_SIZE = HEADER_SIZE + DATA_SIZE
BUFFER_SIZE = 600

TFTP_OPCODES = {
    'read': 1,
    'write': 2,
    'data': 3,
    'ack': 4,
    'error': 5
}

TFTP_MODES = {
    'netascii': 1,
    'octet': 2
}

server_error_msg = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

class TFTPClientGUI:

    # The __init__ method sets up the root window and initializes the GUI elements.
    def __init__(self, root):
        self.root = root
        self.root.title("TFTP Client") # Set the title of the root window to "TFTP Client"
        
        # Create and pack the title label
        self.title_label = tk.Label(root, text="｡･ﾟﾟ･ TFTP Client ･ﾟﾟ･｡", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=10)

        # Create and pack the IP address label and entry field
        self.ip_label = tk.Label(root, text="IP Address:")
        self.ip_label.pack()
        self.ip_entry = tk.Entry(root, width=30)
        self.ip_entry.pack()

        # Create and pack the file label, file entry field, and browse button
        self.file_label = tk.Label(root, text="File:")
        self.file_label.pack()
        self.file_frame = tk.Frame(root)
        self.file_frame.pack()
        self.file_entry = tk.Entry(self.file_frame)
        self.file_entry.pack(side=tk.LEFT)

        self.browse_button = tk.Button(self.file_frame, text="Browse", command=self.browse_command)
        self.browse_button.pack(side=tk.LEFT)

        # Create and pack the save as label and entry field
        self.save_as_label = tk.Label(root, text="Save As:")
        self.save_as_label.pack()
        self.save_as_entry = tk.Entry(root, width=30)
        self.save_as_entry.pack()

        # Create and pack the mode label, mode dropdown menu, block size label, and block size dropdown menu
        self.mode_label = tk.Label(root, text="Mode:")
        self.mode_label.pack()
        self.mode_var = tk.StringVar()
        self.mode_var.set('octet')
        self.mode_dropdown = tk.OptionMenu(root, self.mode_var, *TFTP_MODES.keys())
        self.mode_dropdown.pack()

        self.blocksize_label = tk.Label(root, text="Block Size (Bytes):")
        self.blocksize_label.pack()
        self.blocksize_var = tk.StringVar()
        self.blocksize_var.set('512')
        blocksize_options = ['128', '256', '512', '1024', '2048', '4096', '8192', '16384', '32768', '65536']
        self.blocksize_dropdown = tk.OptionMenu(root, self.blocksize_var, *blocksize_options)
        self.blocksize_dropdown.pack()

        # Create and pack the operation label, read button, and write button
        self.operation_label = tk.Label(root, text="Operation:", pady=3)
        self.operation_label.pack()

        self.operation_frame = tk.Frame(root)
        self.operation_frame.pack(pady=5)

        self.read_button = tk.Button(
            self.operation_frame,
            text="DOWNLOAD",
            width=10,
            command=self.read_command,
            font=("Helvetica", 12, "bold")
        ) 
        self.read_button.pack(side=tk.LEFT)

        self.write_button = tk.Button(
            self.operation_frame,
            text="UPLOAD",
            width=10,
            command=self.write_command,
            font=("Helvetica", 12, "bold")
        )  
        self.write_button.pack(side=tk.LEFT)

        # Create and pack the console label and console auto-bottom scrolled text field
        self.console_label = tk.Label(root, text="  Console:")
        self.console_label.pack(anchor=tk.W)

        self.console_frame = tk.Frame(root, borderwidth=2, relief="groove")
        self.console_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.console = scrolledtext.ScrolledText(self.console_frame, width=40, height=10)
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Call the scroll_to_bottom method after updating the console
        self.console.bind("<Configure>", self.scroll_to_bottom)

        # Create a UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def scroll_to_bottom(self, event=None):
        # This method scrolls the console to the bottom
        self.console.yview(tk.END)


    # This method is called when the user clicks the "Browse" button. It opens a file dialog and allows the user to select a file.
    def browse_command(self):
        filename = filedialog.askopenfilename()
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, filename)

    # This method is called when the user clicks the "DOWNLOAD" button. It retrieves the IP address, filename, and mode entered by the user.
    def read_command(self):
        ip = self.ip_entry.get()
        filename = self.file_entry.get()
        mode = self.mode_var.get()
        save_as = self.save_as_entry.get()  # Get the filename to save the downloaded file

        server = (ip, SERVER_PORT)

        if self.file_exists(filename):
            self.initiate_req('read', filename, mode, server)
            self.read(filename, save_as, mode)  # Pass the save_as filename to the read method
        else:
            self.console.insert(tk.END, 'File not found or access violation\n')

    # This method is called when the user clicks the "UPLOAD" button. It retrieves the IP address, filename, and mode entered by the user.
    def write_command(self):
        ip = self.ip_entry.get()
        filename = self.file_entry.get()
        mode = self.mode_var.get()
        save_as = self.save_as_entry.get()

        server = (ip, SERVER_PORT)

        if self.file_exists(filename):
            self.initiate_req('write', save_as, mode, server)  # Use the new file name for the write request
            self.write(filename, mode)
        else:
            self.console.insert(tk.END, 'File not found or access violation\n')

    # This method is used to initiate a TFTP request to the server. It builds a request packet based on the operation (read or write), filename, and mode provided, and sends it to the server.
    def initiate_req(self, operation, filename, mode, server):
        request = bytearray()

        request.append(0)
        request.append(TFTP_OPCODES[operation])

        file_name = filename.split('/')[-1]
        file_name = bytearray(file_name.encode('utf-8'))
        request += file_name

        request.append(0)

        mode = bytearray(bytes(mode, 'utf-8'))
        request += mode

        request.append(0)

        self.sock.sendto(request, server)
        self.console.insert(tk.END, f"Request: {request}\n")

    # This method is used to read data from the server in response to a read request. It saves the received data to a file specified by filename_saved.
    def read(self, filename_saved, save_as, mode):
        directory = os.getcwd()  # Get the current working directory
        client_directory = os.path.join(directory, "TFTP Client")  # Create the "client" folder path

        if not os.path.exists(client_directory):
            os.mkdir(client_directory)  # Create the "client" folder if it doesn't exist

        file_path = os.path.join(client_directory, save_as)  # Combine the "client" folder path and the filename to save the downloaded file

        if mode == 'netascii':
            file = open(file_path, "w")
        elif mode == 'octet':
            file = open(file_path, "wb")

        total_bytes = 0

        while True:
            self.sock.settimeout(5)
            try:
                # waits for DATA response from the server
                data, server = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                self.console.insert(tk.END, 'Timeout reached, unresponsive server\n')
                self.console.insert(tk.END, 'Terminating...\n')
                break

            if self.server_error(data):
                break

            # actual data starts with data[4]
            content = data[4:]

            if mode == 'netascii':
                # decode the data before writing
                content = content.decode("utf-8")

            try:
                file.write(content)
            except OSError:
                self.console.insert(tk.END, server_error_msg[3] + '\n')  # disk full errors
                break

            # opcode:   data[0] data[1]
            # block_no: data[2] data[3]
            self.send_ACK(data[0:4], server)

            # last DATA packet
            if len(data) < BLK_SIZE:
                self.console.insert(tk.END, 'File downloaded successfully.\n')
                break

            # Display console output in GUI
            block_no = int.from_bytes(data[2:4], byteorder='big')
            total_bytes += len(data) - 4
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            console_output = f"({timestamp}) - ACK Block #{block_no}: {len(data)} bytes downloaded (Total: {total_bytes} bytes)\n"
            self.console.insert(tk.END, console_output)
            self.console.see(tk.END)  # Scroll to the bottom of the console

        file.close()

    # This method is used to write data to the server in response to a write request. It reads data from a file specified by filename and sends it to the server.
    def write(self, filename, mode):
        if mode == 'netascii':
            file = open(filename, "r")
        elif mode == 'octet':
            file = open(filename, "rb")

        block_no = 0
        total_bytes = 0
        prev_blockno = -1

        file_name = filename.split('/')[-1]
        save_as = self.save_as_entry.get()  # Get the new file name entered by the user

        while True:
            self.sock.settimeout(5)
            try:
                ack, server = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                self.console.insert(tk.END, 'Timeout reached, unresponsive server\n')
                self.console.insert(tk.END, 'Terminating...\n')
                break

            if self.server_error(ack):
                break

            if prev_blockno != int.from_bytes(ack[2:4], byteorder='big'):
                block_no = int.from_bytes(ack[2:4], byteorder='big')
                prev_blockno = block_no
                block_no = block_no + 1

                data = file.read(512)

                if mode == 'netascii':
                    data = bytearray(bytes(data, 'utf-8'))

                self.send_DATA(block_no, data, server)

                total_bytes += len(data) - 4

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                console_output = f"({timestamp}) - ACK Block #{block_no}: {len(data)} bytes uploaded (Total: {total_bytes} bytes)\n"
                self.console.insert(tk.END, console_output)
                self.console.see(tk.END)  # Scroll to the bottom of the console

                if len(data) < DATA_SIZE:
                    ack, server = self.sock.recvfrom(BUFFER_SIZE)
                    self.console.insert(tk.END, 'File uploaded successfully.\n')
                    break

        file.close()

    # This method is used to send a DATA packet to the server. It builds a data packet containing the block number and the data to be sent and sends it to the server.
    def send_DATA(self, block_no, data, server):
        data_packet = bytearray()

        data_packet.append(0)
        data_packet.append(TFTP_OPCODES['data'])

        data_packet.append(0)
        data_packet.append(block_no)

        data_packet += data

        self.sock.sendto(data_packet, server)
        self.console.insert(tk.END, f"## Data ##: {data_packet[0:4]} : {len(data_packet)}\n")

    # This method is used to send an ACK packet to the server. It builds an ACK packet with the provided acknowledgment data and sends it to the server.
    def send_ACK(self, ack_data, server):
        ack = bytearray(ack_data)

        ack[0] = 0
        ack[1] = TFTP_OPCODES['ack']

        self.console.insert(tk.END, f"Ack packet: {ack}\n")
        self.sock.sendto(ack, server)

    # This method is used to send an ERROR packet to the server. It builds an ERROR packet with the provided error code and sends it to the server.
    def send_ERROR(self, error_code, server):
        error = bytearray()

        error.append(0)
        error.append(TFTP_OPCODES['error'])

        error.append(0)
        error.append(error_code)

        errMsg = server_error_msg[error_code]
        errMsg = bytearray(errMsg.encode('utf-8'))
        error += errMsg

        error.append(0)

        self.sock.sendto(error, server)
        self.console.insert(tk.END, f"Error {error}\n")

    # This method checks if the server response is an error packet. If it is, it displays the corresponding error message and returns True.
    def server_error(self, server_response):
        opcode = server_response[:2]
        error = (int.from_bytes(opcode, byteorder='big') == TFTP_OPCODES['error'])

        if error:
            error_code = int.from_bytes(server_response[2:4], byteorder='big')
            self.console.insert(tk.END, 'Error raised: ' + server_error_msg[error_code] + '\n')
            self.console.insert(tk.END, 'Terminating...\n')

        return error

    # These methods are utility methods for checking if a file exists (file_exists) and running the GUI application (run).
    def file_exists(self, filename):
        try:
            file = open(filename)
            file.close()
            return True
        except IOError:
            return False

    def run(self):
        self.root.mainloop()


root = tk.Tk()
app = TFTPClientGUI(root)
app.run()
