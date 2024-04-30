import time
import sys
import socket
import tkinter
import traceback
from tkinter import ttk
import tkinter.messagebox
import tkinter.font
import tkinter.filedialog
from PIL import ImageTk, Image
import threading
import base64
from protocols.double_ratchet import KeyStore, Ratchet
import os
import pickle
import transport
import websockets.sync.client
import requests
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
import base64
from io import BytesIO

RECV_BUFFER = 10000000
users = {}
messages = {}
global contacts
with open('server_ip.txt', 'r') as file:
    ip_address = file.read().strip()

class Application(tkinter.Tk):
    def load_user_keys(self, folder_path):

        for file_name in os.listdir(folder_path):
            if file_name.endswith(".dat"):
                file_path = os.path.join(folder_path, file_name)
                username = os.path.splitext(file_name)[0]

                with open(file_path, 'rb') as file:
                    ratchet_key = pickle.load(file)

                users[username] = ratchet_key


    def launch_app(self):
        dat_file_path = "./store/kb.dat" 
        dat_dir = os.path.dirname(dat_file_path)
        os.makedirs(dat_dir, exist_ok=True)

        if os.path.exists(dat_file_path):
            with open(dat_file_path, 'rb') as file:
                self.bob = pickle.load(file)
                print("Pickle file exists. Unpickled data:", self.bob)

        users_folder_path = "./store/users"

        self.load_user_keys(users_folder_path)
        print(users)

        self.title('Yet Another Signal Clone')

        self.frame = ttk.Frame(self)

        self.frame.style = ttk.Style()

        ttk.Style().configure("TButton", padding=6, relief="flat")
        self.reg_btn = ttk.Button(self.frame, text='New user?  Sign Up here!', command=self.reg_menu, takefocus=True)
        self.reg_btn.grid(row=2, column=2, padx=40, pady=30)
        self.client_button = ttk.Button(self.frame, text='Log In', command=self.client_menu, takefocus=True)
        self.client_button.grid(row=2, column=0, padx=40, pady=30)
        self.try_again_bool = False
        self.try_again_bool2 = False
        self.frame.pack(fill=tkinter.BOTH, expand=True)

        self.theme_use = 'classic'

        self.frame.style.theme_use(self.theme_use)

        self.mainloop()

    def reg_menu(self):
        if self.try_again_bool2:
            self.try_again2.destroy()
            self.un_error.destroy()
            self.try_again_bool2 = False
        self.client_button.destroy()
        self.reg_btn.destroy()
        self.host = ip_address 
        self.port = 9000
        self.reg_name_label = ttk.Label(self.frame, text='Username', justify=tkinter.RIGHT)
        self.reg_name_entry = ttk.Entry(self.frame)
        self.reg_pwd_label = ttk.Label(self.frame, text="Password", justify=tkinter.RIGHT)
        self.reg_pwd_entry = ttk.Entry(self.frame, show='*')

        self.register_btn = ttk.Button(self.frame, text='Sign Up', command=self.reg_user, takefocus=True)

        self.frame.pack_forget()

        self.title('Registration')
        self.reg_name_label.grid(row=2, column=0, pady=10, padx=5, sticky=tkinter.E)
        self.reg_name_entry.grid(row=2, column=1, pady=10, padx=5)
        self.reg_pwd_label.grid(row=3, column=0, pady=10, padx=5, sticky=tkinter.E)
        self.reg_pwd_entry.grid(row=3, column=1, pady=10, padx=5)
        self.register_btn.grid(row=4, column=2, pady=10, padx=5)
        self.frame.pack(fill=tkinter.BOTH, expand=True)

    def reg_user(self):

        self.username = self.reg_name_entry.get().rstrip()
        self.password = self.reg_pwd_entry.get().rstrip()
        self.reg_name_label.destroy()
        self.reg_name_entry.destroy()
        self.reg_pwd_label.destroy()
        self.reg_pwd_entry.destroy()
        self.register_btn.destroy()
        self.frame.pack_forget()

        try:
            url = f'http://{ip_address}:8000/registration'
            var = requests.post(url,
                                data='username=' + self.username + '&password=' + self.password,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
            var = var.status_code
            if var == 201:
                print("Success")
                self.bob = KeyStore()
                ltk_pk, spk_pk, otpks = self.bob.get_key_bundle()
                spk_sig = self.bob.sign_spk()
                msg = ltk_pk + spk_pk + spk_sig
                b = b''
                for byte in otpks:
                    b += byte
                msg += b
                var = requests.post(f'http://{ip_address}:8000/keybundle/' + self.username,
                                    json={
                                        "key_bundle": base64.encodebytes(msg).decode()
                                    },
                                    headers={'Content-Type': 'application/json'})
                if var.status_code != 201:
                    self.reg_menu()
            else:
                print("Failure")
                self.reg_menu()

        except Exception as e:
            print(traceback.format_exc())
            self.reg_menu()
        self.client_menu()

    def client_menu(self):
        self.client_button.destroy()
        self.reg_btn.destroy()
        if self.try_again_bool:
            self.try_again.destroy()
            self.wp_error.destroy()
            self.try_again_bool = False

        self.title('Log In')
        self.name_entry_label = ttk.Label(self.frame, text='User name', anchor=tkinter.W, justify=tkinter.LEFT)
        self.name_entry = ttk.Entry(self.frame)
        self.pwd_entry_label = ttk.Label(self.frame, text='Password', anchor=tkinter.W, justify=tkinter.LEFT)
        self.pwd_entry = ttk.Entry(self.frame, show='*')
        self.launch_button = ttk.Button(self.frame, text='Log In', command=self.launch_client)
        self.name_entry_label.grid(row=2, column=0, pady=10, padx=5)
        self.name_entry.grid(row=2, column=1, pady=10, padx=5)
        self.pwd_entry_label.grid(row=3, column=0, pady=10, padx=5)
        self.pwd_entry.grid(row=3, column=1, pady=10, padx=5)
        self.launch_button.grid(row=5, column=1, pady=10, padx=5)

        self.frame.pack(fill=tkinter.BOTH, expand=True)

    def launch_client(self):

        self.host = ip_address 
        self.port = 9000
        self.name = self.name_entry.get()
        self.pwd = self.pwd_entry.get()
        self.name_entry_label.destroy()
        self.name_entry.destroy()
        self.pwd_entry_label.destroy()
        self.pwd_entry.destroy()

        self.launch_button.destroy()
        self.frame.pack_forget()
        f = 0
        var = requests.post(f'http://{ip_address}:8000/authentication',
                            data='username=' + self.name + '&password=' + self.pwd,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if var.status_code == 200:
            print("Successful login")
        else:
            print("Failure to login")
            self.launch_client()
        self.flag = 0
        self.conn = websockets.sync.client.connect(f"ws://{ip_address}:9000")
        self.conn.send(self.name)
        print('sent name to server')

        self.title('Yet Another Signal Clone')
        self.should_quit = False
        self.protocol('WM_DELETE_WINDOW', self.client_quit)
        var = requests.get(f'http://{ip_address}:8000/messages/' + self.name,
                           headers={'Content-Type': 'application/json'})
        print('################################', var.json()['messages'])

        for msg in var.json()['messages']:
            if msg['type'] == 'x3dh':
                sender = msg['by']
                content = base64.decodebytes(msg['content'].encode())
                (sk_bob, msg, ratchet_pub) = self.bob.x3dh_w_header(content[:128], content[128:])
                if msg == sender + ' is requesting permission to chat':
                    print("success")
                    users[sender] = Ratchet(sk_bob, dh_pub_key=ratchet_pub)
                    print('Ratchet created')
                    self.conn.send(sender)
                    self.conn.send('msg')
                    hdr, cph = users[sender].encrypt(self.name + ' has accepted your request to chat')
                    self.conn.send(hdr)
                    self.conn.send(cph)
            else:
                sender = msg['by']
                content = base64.decodebytes(msg['content'].encode())
                if sender not in messages.keys():
                    messages[sender] = []
                messages[sender].append(users[sender].decrypt(content[:128], content[128:]))

        s = ttk.Style()
        s.configure("TButton", background='burlywood3')
        s.configure('my.TFrame', background='old lace')
        s.configure('new.TFrame', background='navajo white')
        s.configure('new1.TFrame', background='ivory2')
        s.configure("TLabelframe", background='old lace', highlightbackground='old lace')

        self.chat_frame = ttk.Frame(self.frame, borderwidth=5, style='my.TFrame')
        self.clients_frame = ttk.Frame(self.frame, style='my.TFrame')
        self.entry_frame = ttk.Frame(self, style='my.TFrame')
        self.button_frame = ttk.Frame(self.entry_frame, style='my.TFrame')

        fonte = tkinter.font.Font(family='Arial', size=16, weight=tkinter.font.BOLD)
        s.configure('.', font=fonte)
        font1 = tkinter.font.Font(family="Comic Sans MS", size=16, weight=tkinter.font.BOLD)
        font2 = tkinter.font.Font(family="Arial", size=16, weight=tkinter.font.BOLD)
        self.font3 = tkinter.font.Font(family="Courier New", size=16, weight=tkinter.font.BOLD)
        self.chat_font = tkinter.font.Font(family="Helvetica", size=18, weight=tkinter.font.BOLD)
        self.chat_text = tkinter.Text(self.chat_frame, state=tkinter.DISABLED)
        self.scroll = tkinter.Scrollbar(self.chat_frame)
        self.scroll.configure(command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.scroll.set)

        self.img = ImageTk.PhotoImage(Image.open('Images/send2.png'))
        self.img1 = ImageTk.PhotoImage(Image.open('Images/file.png'))
        self.img2 = ImageTk.PhotoImage(Image.open('Images/user.png'))

        self.chat_entry = ttk.Entry(self.entry_frame, font=font2)
        self.scroll1 = tkinter.Scrollbar(self.entry_frame, orient=tkinter.HORIZONTAL)
        self.scroll1.configure(command=self.chat_entry.xview)
        self.chat_entry.configure(xscrollcommand=self.scroll1.set)
        self.send_button = ttk.Button(self.button_frame, image=self.img)
        self.browsebutton = ttk.Button(self.button_frame, image=self.img1,
                                       command=self.browse)
        self.send_button.bind('<Button-1>', self.send)
        self.chat_entry.bind('<Return>', self.send)

        self.user_icon = ttk.Label(self.clients_frame, image=self.img2, background='light blue', text=self.name,
                                   compound="top", font=self.font3, anchor=tkinter.E)
        self.frame.pack(side=tkinter.TOP, fill=tkinter.BOTH,
                        expand=True)
        self.user_icon.pack(side=tkinter.TOP)
        s.configure('TNotebook', background='old lace', borderwidth=1)
        self.tabs = ttk.Notebook(self.clients_frame, height=20, padding=10)
        self.tabs.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        self.f2 = ttk.Frame(self.clients_frame, style="new1.TFrame")
        self.tabs.add(self.f2, text="Contacts")
        self.contact_label = [];
        self.selected_contact = tkinter.StringVar()
        self.contact_combobox = ttk.Combobox(self.f2, textvariable=self.selected_contact, font=self.font3,
                                             foreground='gray49', background='old lace')
        self.contact_combobox.grid(row=0, column=0, sticky=tkinter.W)
        var = requests.get(f'http://{ip_address}:8000/users',
                           headers={'Content-Type': 'application/json'})
        var = var.json()['users']
        self.contacts = []
        self.contacts_with_status = []
        for user in var:
            if self.name == user['user']:
                continue
            self.contacts.append(user['user'])
            if user['active']:
                self.contacts_with_status.append(user['user'] + ' *')
            else:
                self.contacts_with_status.append(user['user'])
        self.num_contacts = len(var) - 1

        self.contact_combobox['values'] = self.contacts_with_status
        self.contact_combobox.bind("<<ComboboxSelected>>", self.handle_contact_selection)
        self.clients_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.chat_frame.pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=True)
        self.send_button.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.browsebutton.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.button_frame.pack(side=tkinter.RIGHT)
        self.scroll1.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.chat_entry.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self.entry_frame.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        self.scroll.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.chat_text.pack(fill=tkinter.BOTH, expand=True)
        self.chat_entry.focus_set()
        self.clientchat_thread = threading.Thread(name='clientchat',
                                                  target=self.clientchat)
        self.clientchat_thread.start()

    def handle_contact_selection(self, event):
        selected_contact = self.selected_contact.get()
        if '*' in selected_contact:
            selected_contact = selected_contact[:-2]

        if selected_contact not in users:
            var = requests.get(f'http://{ip_address}:8000/keybundle/' + selected_contact,
                               headers={'Content-Type': 'application/x-www-form-urlencoded'})
            bundle = base64.decodebytes(var.json()['key_bundle'].encode())
            ltk = bundle[:32]
            spk = bundle[32:64]
            sig = bundle[64:128]
            arr = []
            _sum = 128
            while _sum + 32 >= len(bundle):
                arr.append(bundle[_sum:_sum + 32])
                _sum = _sum + 32
            arr = arr[0] if len(arr) else None
            (sk_alice, header, cipher, ratchet_pair) = self.bob.x3dh_w_key_bundle(
                self.name + ' is requesting permission to chat', (ltk, spk, sig, arr))
            users[selected_contact] = Ratchet(sk_alice, ratchet_pair)
            print('Ratchet generated')
            print(users.keys())
            self.conn.send(selected_contact)
            self.conn.send('x3dh')
            self.conn.send(header)
            self.conn.send(cipher)
            print('sending ratchet message')
            self.chat_text.config(state=tkinter.NORMAL)
            self.chat_text.insert(tkinter.END,
                                  'Waiting for ' + selected_contact + 'to accept request to chat...' + '\n',
                                  ('tag{0}'.format(2)))
            self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                      font=self.chat_font)
            self.chat_text.config(state=tkinter.DISABLED)
            self.chat_text.see(tkinter.END)

        print(messages)
        if selected_contact in messages:
            for msg in messages[selected_contact]:
                self.chat_text.config(state=tkinter.NORMAL)
                self.chat_text.insert(tkinter.END, msg + '\n', ('tag{0}'.format(2)))
                self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                          font=self.chat_font)
                self.chat_text.config(state=tkinter.DISABLED)
                self.chat_text.see(tkinter.END)

    def user_selection(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("User Selection")
        frame = tkinter.Frame(self.root)
        frame1 = tkinter.Frame(frame)
        label1 = tkinter.Label(frame1, text="Select the users you want to connect to:", compound=tkinter.LEFT,
                               font=('Helvetica', '20'), justify=tkinter.CENTER)
        label1.pack(side=tkinter.TOP, fill=tkinter.X)
        frame1.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        frame2 = tkinter.Frame(self.root, borderwidth=10)
        i = 0
        for client in self.list_of_active_users:
            ch = tkinter.Checkbutton(frame2, text=client, variable=self.enable[client], borderwidth=0, pady=10,
                                     justify=tkinter.LEFT, font=('Courier New', 19), foreground='gray30')
            ch.grid(column=0, row=i, sticky=tkinter.W)
            i = i + 1
        frame3 = tkinter.Frame(frame2, borderwidth=10)
        b = tkinter.Button(frame3, text="Connect", justify=tkinter.CENTER, font=("Helvetica", '14'), padx=6, pady=6,
                           command=self.root.withdraw)
        b.pack()
        frame3.grid(row=i, column=1, columnspan=2, sticky=tkinter.S)
        frame2.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=True)
        frame.pack(fill=tkinter.BOTH, expand=True)

    def add_contact(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("Contact Addition")
        label1 = tkinter.Label(self.root, text="Enter the Contact Details:", font=('Helvetica', 20),
                               justify=tkinter.CENTER, pady=10)
        label1.grid(row=0, columnspan=2)
        label2 = tkinter.Label(self.root, text="Username", font=("Courier New", 14), justify=tkinter.RIGHT, pady=15)
        label2.grid(row=1, column=0)
        self.contact = tkinter.StringVar()
        self.contact.set("Type Username")
        entry1 = tkinter.Entry(self.root, textvariable=self.contact)
        entry1.grid(row=1, column=1)
        entry1.bind("<Return>", self.add)

    def add(self, event):
        if self.contact.get() in self.contacts:
            tkinter.messagebox.showwarning(title="Contact Exists", message="The Contact already exists")
            self.root.withdraw()
        with open("textfiles/contact.txt", "a") as file:
            file.write(" " + self.contact.get())
        l = ttk.Label(self.f2, padding=10, text=self.contact.get(), justify=tkinter.LEFT, font=self.font3,
                      foreground='gray49',
                      background='ivory2')
        l.grid(row=self.num_contacts, column=0, sticky=tkinter.W)
        self.contact_label.append(l)
        self.contacts.append(self.contact.get())
        self.num_contacts += 1
        self.root.withdraw()

    def del_contact(self):
        self.root = tkinter.Toplevel(self)
        self.root.title("Contact Deletion")
        label1 = tkinter.Label(self.root, text="Enter the Contact to be removed:", font=('Helvetica', 20),
                               justify=tkinter.CENTER, pady=10)
        label1.grid(row=0, columnspan=2, column=0)
        label2 = tkinter.Label(self.root, text="Username", font=("Courier New", 14), justify=tkinter.LEFT, pady=15)
        label2.grid(row=1, column=0)
        self.remove1 = tkinter.StringVar()
        self.remove1.set("Type Username")
        entry1 = tkinter.Entry(self.root, textvariable=self.remove1)
        entry1.grid(row=1, column=1)
        entry1.bind("<Return>", self.remove)

    def remove(self, event):
        try:
            self.contacts.remove(self.remove1.get())
        except:
            print(traceback.format_exc())
            tkinter.messagebox.showwarning(title="No Contact", message="No such contact exists")
            self.root.withdraw()
            return
        for i in self.contact_label:
            i.destroy()
        self.contact_label.clear()
        j = 0
        for i in self.contacts:
            l = ttk.Label(self.f2, padding=10, text=i, justify=tkinter.LEFT, font=self.font3, foreground='gray49',
                          background='ivory2')
            l.grid(row=j, column=0, sticky=tkinter.W)
            self.contact_label.append(l)
            j = j + 1
        self.num_contacts = j
        remove2 = ' '.join(self.contacts)
        self.root.withdraw()

    def browse(self):
        self.mmfilename = tkinter.filedialog.askopenfilename()
        self.multimedia_send()

    def send(self, event):
        message = self.chat_entry.get()
        contact = self.selected_contact.get()
        if '*' in contact:
            contact = contact[:-2]
        header, cipher = users[contact].encrypt(message)

        print('Sending encrypted message')
        self.conn.send(contact)
        self.conn.send('msg')
        self.conn.send(header)
        self.conn.send(cipher)
        print('Sent encrypted message')
        self.chat_entry.delete(0, tkinter.END)
        self.chat_text.config(state=tkinter.NORMAL)
        self.chat_text.insert(tkinter.END, self.name + ':' + message + '\n', ('tag{0}'.format(1)))
        self.chat_text.tag_config('tag{0}'.format(1), justify=tkinter.RIGHT, foreground='RoyalBlue3',
                                  font=self.chat_font)
        self.chat_text.config(
            state=tkinter.DISABLED)
        self.chat_text.see(tkinter.END)

    def multimedia_send(self):
        filename = self.mmfilename

        with open(filename, "rb") as file:
            encoded_string = (base64.b64encode(file.read())).decode()

        data = "^"
        for client in self.list_of_active_users:
            if self.enable[client].get() == 1:
                data = data + "@" + client + ' '

        data = data + ':'
        data = data + filename + ':'
        data_to_send = data + encoded_string
        self.chat_entry.delete(0, tkinter.END)

        self.chat_text.config(state=tkinter.NORMAL)
        self.chat_text.insert(tkinter.END, self.name + ':' + filename + '\n', ('tag{0}'.format(1)))
        self.chat_text.tag_config('tag{0}'.format(1), justify=tkinter.RIGHT, foreground='RoyalBlue3',
                                  font=self.chat_font)
        self.chat_text.config(
            state=tkinter.DISABLED)
        self.chat_text.see(tkinter.END)

    def clientchat(self):
        while not self.should_quit:
            try:
                sender = self.conn.recv()
                type = self.conn.recv()
                print('################# sender type #######################', sender, type)

                if sender == 'server' and type == 'add':
                    new_contact = self.conn.recv()
                    if new_contact not in self.contacts:
                        self.contacts.append(new_contact)
                    if new_contact + ' *' not in self.contacts_with_status and new_contact in self.contacts_with_status:
                        self.contacts_with_status.remove(new_contact)
                        self.contacts_with_status.append(new_contact + ' *')
                    elif new_contact not in self.contacts_with_status:
                        self.contacts_with_status.append(new_contact + ' *')

                    self.contact_combobox['values'] = self.contacts_with_status

                elif sender == 'server' and type == 'remove':
                    new_contact = self.conn.recv()
                    self.contacts_with_status.remove(new_contact + ' *')
                    self.contacts_with_status.append(new_contact)
                    self.contact_combobox['values'] = self.contacts_with_status

                elif type == 'x3dh':
                    header = self.conn.recv()
                    cipher = self.conn.recv()
                    print('############# header cipher #################', header, cipher)
                    (sk_bob, msg, ratchet_pub) = self.bob.x3dh_w_header(header, cipher)
                    if msg == sender + ' is requesting permission to chat':
                        print("success")
                        users[sender] = Ratchet(sk_bob, dh_pub_key=ratchet_pub)
                        print('Ratchet created')
                        self.conn.send(sender)
                        self.conn.send('msg')
                        hdr, cph = users[sender].encrypt(sender + ' has accepted your request to chat')
                        self.conn.send(hdr)
                        self.conn.send(cph)
                        continue

                else:
                    header = self.conn.recv()
                    cipher = self.conn.recv()
                    print('cipher ', cipher)
                    print('header ', header)
                    msg = users[sender].decrypt(header, cipher)
                    contact = self.selected_contact.get()
                    if '*' in contact:
                        contact = contact[:-2]
                    print('decrypted message ', msg)
                    print('sender and contact', sender, contact)
                    print(sender == contact, "abcd")
                    # if msg.startswith("Image:"):
                    #     image_data = msg[len("Image:"):]
                    #     self.display_message(sender, "", image_data)
                    # else:
                    #     self.display_message(sender,msg) 
                    if sender == contact:
                        print("BC")
                        # self.chat_text.config(state=tkinter.NORMAL)
                        # self.chat_text.insert(tkinter.END, msg + '\n', ('tag{0}'.format(2)))
                        # self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                        #                           font=self.chat_font)
                        # self.chat_text.config(state=tkinter.DISABLED)
                        # self.chat_text.see(tkinter.END)
                        if msg.startswith("Image"): 
                            print("THere") # Assuming you prefix image messages with "Image:"
                            # Extract the image data from the decrypted message
                            image_data = msg[len("Image"):]
                            # Display the image in the chat_text widget
                            self.display_image(image_data)
                        else:
                            print("Here")
                            # Display the text message in the chat_text widget
                            self.display_text_message(sender, msg)
                    else:
                        if sender not in messages.keys():
                            messages[sender] = []
                        messages[sender].append(msg)

            except Exception as e:
                print(traceback.format_exc())
                continue
    def display_text_message(self, sender, message):
        # Display text message in the chat_text widget
        # if sender == self.selected_contact.get():
        print("inside you")
        self.chat_text.config(state=tkinter.NORMAL)
        self.chat_text.insert(tkinter.END, message + '\n', ('tag{0}'.format(2)))
        self.chat_text.tag_config('tag{0}'.format(2), justify=tkinter.LEFT, foreground='gray30',
                                    font=self.chat_font)
        self.chat_text.config(state=tkinter.DISABLED)
        self.chat_text.see(tkinter.END)

    def display_image(self, image_data, max_width=300, max_height=300):
        # Decode the base64 string to binary image data
        binary_data = base64.b64decode(image_data)
        image_data = BytesIO(binary_data)
        image = Image.open(image_data)
        
        # Resize the image maintaining aspect ratio
        original_width, original_height = image.size
        ratio = min(max_width/original_width, max_height/original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        #image = image.resize((new_width, new_height), Image.ANTIALIAS)
        try:
            # Trying the newer method if available
            from PIL import ImageResampling
            image = image.resize((new_width, new_height), ImageResampling.LANCZOS)
        except ImportError:
            # Fallback to the older method if ImageResampling is not available
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert the PIL image object to a format that Tkinter can use
        photo = ImageTk.PhotoImage(image)
        
        # Ensure the text widget allows changes (is in NORMAL state)
        self.chat_text.config(state=tk.NORMAL)
        
        # Create an image window in the chat_text widget at the end of the text
        self.chat_text.image_create(tk.END, image=photo)
        
        # Append a newline after the image to ensure the next content starts from a new line
        self.chat_text.insert(tk.END, '\n')
        
        # Keep a reference to the image to prevent garbage collection
        self.chat_text.image = photo  # You might want to manage this differently if many images are expected
        
        # Disable the text widget to prevent user edits
        self.chat_text.config(state=tk.DISABLED)
        
        # Scroll to the end of the text widget to ensure the image is visible
        self.chat_text.see(tk.END)


    def client_quit(self):
        if tkinter.messagebox.askokcancel(title="Quit Window", message="Do you really want to quit?"):
            if self.bob:
                directory = './store'
                if not os.path.exists(directory):
                    os.makedirs(directory)
                file_path = os.path.join(directory, 'kb.dat')
                with open(file_path, 'wb') as file:
                    pickle.dump(self.bob, file)

            if len(users.keys()) != 0:
                if not os.path.exists('./store/users'):
                    os.makedirs('./store/users')
                for user in users.keys():
                    file_path = os.path.join('./store/users', user + '.dat')
                    with open(file_path, 'wb') as file:
                        pickle.dump(users[user], file)
            self.should_quit = True
            self.conn.close()
            self.clientchat_thread.join()
            self.destroy()
        else:
            pass


if __name__ == '__main__':
    app = Application()
    app.launch_app()

