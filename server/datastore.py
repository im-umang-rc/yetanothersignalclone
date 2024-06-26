import sqlite3
import time


def init_datastore():
    connection = get_connection()
    try:
        connection.execute('create table keybundle( user TEXT, keys BLOB);')
        connection.execute('create table messages(sender TEXT,receiver TEXT,message BLOB,type TEXT, timestamp INTEGER);')
        connection.execute('create table users(username TEXT,password TEXT);')
        connection.commit()
    finally:
        close_connection(connection)

def get_connection():
    return sqlite3.connect('server.db')


def authenticate(connection, username, password):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "SELECT 1 FROM users WHERE username = ? and password = ?"
        cursor.execute(query, (username, password,))
        result = cursor.fetchone()
        return result

    finally:
        if cursor is not None:
            cursor.close()


def register(connection, username, password):
    try:
        cursor = connection.cursor()
        query = "SELECT 1 FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if result:
            cursor.close()
            return False

        query = "INSERT INTO users (username, password) VALUES (?, ?)"
        cursor.execute(query, (username, password))
        connection.commit()
        cursor.close()
        return True

    finally:
        if cursor is not None:
            cursor.close()


def store_message(connection, sender, receiver, message, type):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "INSERT INTO messages (sender, receiver, message, timestamp, type) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(query, (sender, receiver, message, time.time_ns(), type, ))
        connection.commit()

    finally:
        if cursor is not None:
            cursor.close()


def fetch_all_messages(connection, receiver):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "SELECT message, sender, type, timestamp FROM messages WHERE receiver = ?"
        cursor.execute(query, (receiver,))
        result = cursor.fetchall()
        cursor.close()
        return result

    finally:
        if cursor is not None:
            cursor.close()

def delete_all_messages(connection, receiver):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "DELETE FROM messages WHERE receiver = ?"
        cursor.execute(query, (receiver,))
        cursor.close()

    finally:
        if cursor is not None:
            cursor.close()


def fetch_all_users(connection):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "SELECT username FROM users"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    finally:
        if cursor is not None:
            cursor.close()

def store_key_bundle(connection, user, key_bundle):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "INSERT INTO keybundle (user, keys) VALUES (?, ?)"
        cursor.execute(query, (user, key_bundle))
        connection.commit()

    finally:
        if cursor is not None:
            cursor.close()


def fetch_key_bundle(connection, user):
    cursor = None
    try:
        cursor = connection.cursor()
        query = "SELECT keys from keybundle WHERE user = ?"
        cursor.execute(query, (user,))
        result = cursor.fetchall()
        cursor.close()
        return result

    finally:
        if cursor is not None:
            cursor.close()


def close_connection(connection):
    if connection is not None:
        connection.close()

if __name__ == '__main__':
    import os
    c = get_connection()
    close_connection(c)