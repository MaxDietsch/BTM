import http.server
import socketserver
import json
import sqlite3
from threading import Lock
import uuid
from typing import List
from datetime import datetime

PORT = 8000
DIRECTORY = "./frontend"  # The directory where your HTML and other static files are located
IP_ADDRESS = "192.168.178.85"
DB_NAME = "database/btm.db"

class DatabaseHandler:
    def __init__(self, db_name):
        self.database_connection = sqlite3.connect(db_name, check_same_thread = False)
    
    def get_user_games(self, user_id: int):
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('''
                SELECT Games.name
                FROM Games
                JOIN Portfolios ON Games.id = Portfolios.game_id
                WHERE Portfolios.user_id = ?
                ''', (user_id,))
            games = cursor.fetchall()
            games_list = [{"id": idx + 1, "name": game[0]} for idx, game in enumerate(games)]
            return games_list
        except sqlite3.Error as e:
            print(f"Error fetching games for user: {e}")
            return []
    
    def join_game(self, user_id: int, name: str, password: str) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT id, password FROM Games WHERE name = ?', (name,))
            result = cursor.fetchone()
            if not result:
                return 'Game not found'
            
            game_id, stored_password = result
            if stored_password != password:
                return 'Incorrect password'

            cursor.execute('SELECT id FROM Portfolios WHERE user_id = ? AND game_id = ?', (user_id, game_id))
            result = cursor.fetchone()
            if result:
                return 'Already joined'

            cursor.execute('INSERT INTO Portfolios (user_id, game_id, balance, current_balance) VALUES (?, ?, ?, ?)',
                           (user_id, game_id, 0, 0))
            self.database_connection.commit()
            return 'Joined successfully'
        except sqlite3.Error as e:
            print(f"Error joining game: {e}")
            return 'Error'

    def create_game(self, user_id: int, name: str, password: str, start_capital: float, tax: float, paycheck_amount: float, paycheck_frequency: str) -> str:
        if not (tax >= 0 and tax < 100 and start_capital >= 0 and paycheck_amount >= 0 and paycheck_frequency.isdigit()):
            return 'Invalid parameters'

        start_date = datetime.now().date()
        last_update = start_date

        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT id FROM Games WHERE name = ?', (name,))
            if cursor.fetchone():
                return 'Game already exists'

            cursor.execute('''INSERT INTO Games (name, password, start_date, last_update, start_capital, tax, paycheck_amount, paycheck_frequency)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                           (name, password, start_date, last_update, start_capital, tax, paycheck_amount, paycheck_frequency))
            self.database_connection.commit()

            game_id = cursor.lastrowid

            cursor.execute('''INSERT INTO Portfolios (user_id, game_id, balance, current_balance)
                              VALUES (?, ?, ?, ?)''',
                           (user_id, game_id, start_capital, start_capital))
            self.database_connection.commit()

            return 'Game created successfully'
        except sqlite3.Error as e:
            print(f"Error creating game: {e}")
            return 'Error creating game'


    def get_user_id(self, token: str) -> int:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT id FROM Users WHERE token = ?', (token,))
            id = cursor.fetchone()
            return id[0]
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return None

    
    def get_user_password(self, username: str) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT password FROM Users WHERE username = ?', (username,))
            password = cursor.fetchone()
            return password[0]
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return None


    def get_user_token(self, username: str) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT token FROM Users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return user[0]
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return None


    def store_user(self, username: str, password: str, token: str) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT id FROM Users WHERE username = ?', (username,))
            if cursor.fetchone():
                return 'User already exists'

            cursor.execute('INSERT INTO Users (username, password, token) VALUES (?, ?, ?)', (username, password, token))
            self.database_connection.commit()
            return 'User created successfully'
        except sqlite3.Error as e:
            print(f"Error storing user: {e}")
            return 'Error storing user'
    

    def get_all_users(self) -> List[str]:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT username FROM Users')
            users = cursor.fetchall()
            return users
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return []
    
    def get_all_games(self) -> List[str]:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT name FROM Games')
            games = cursor.fetchall()
            return games
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return []







class BTM_BackEnd(http.server.SimpleHTTPRequestHandler):
    lock = Lock()

    def __init__(self, *args, **kwargs):
        self.db_handler = DatabaseHandler(DB_NAME)
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = 'landing_page.html'
        elif self.path == '/user-items':
            self.handle_user_items()
            return 
        return super().do_GET()

    def do_POST(self) -> None:
        if self.path == '/register':
            self.handle_register()
        elif self.path == '/login':
            self.handle_login()
        elif self.path == '/create-game':
            self.handle_game_creation()
        elif self.path == '/join-game':
            self.handle_game_join()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_register(self) -> None:
        # Determine the length of the data
        content_length = int(self.headers['Content-Length'])
        # Read the POST data
        post_data = self.rfile.read(content_length)
        # Parse the JSON data
        data = json.loads(post_data)
        
        # Extract username and password
        username = data.get('username')
        password = data.get('password')
        token = str(uuid.uuid4())  # Generate a unique token

        print(f"Received registration: username = {username}, password = {password}")
        with self.lock:
            result = self.db_handler.store_user(username, password, token)
        if result == 'User created successfully':
            print(f"User created successfully: {username}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'message': 'User created successfully', 'token': token}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif result == 'User already exists':
            print(f"User already exists: {username}")
            self.send_response(409)
            self.end_headers()
            response = {'message': 'User already exists'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            print(f"Error creating user: {username}")
            self.send_response(500)
            self.end_headers()
            response = {'message': result}
            self.wfile.write(json.dumps(response).encode('utf-8'))


    def handle_login(self) -> None:
        # Determine the length of the data
        content_length = int(self.headers['Content-Length'])
        # Read the POST data
        post_data = self.rfile.read(content_length)
        # Parse the JSON data
        data = json.loads(post_data)
        
        # Extract username and password
        username = data.get('username')
        password = data.get('password')

        print(f"Received login: username = {username}, password = {password}")
        users = {user[0] for user in self.db_handler.get_all_users()}
        if username in users and password == self.db_handler.get_user_password(username):
            print("Username found.")
            self.send_response(200)  
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            token = self.db_handler.get_user_token(username)
            response = {'message': 'Login successful', 'token': token}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        else:
            print('Username not found')
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': 'Invalid username or password'}
            self.wfile.write(json.dumps(response).encode('utf-8'))


    def handle_user_items(self) -> None: 
        auth_header = self.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split("Bearer ")[-1]

        print(f"Get user items of {token}")

        if not token:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        user_id = self.db_handler.get_user_id(token)
        if user_id is None:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        games_list = self.db_handler.get_user_games(user_id)
        print(f"User items: {games_list}")
        response = {'items': games_list}
        response = json.dumps(games_list)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))


    def handle_game_join(self) -> None: 
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        user_token = data.get('user_token')
        print(user_token)
        user_id = self.db_handler.get_user_id(user_token)
        name = data.get('name')
        password = data.get('password')

        print(f'Received game join: user = {user_id}, name = {name}, password = {password}')
        with self.lock:
            result = self.db_handler.join_game(user_id, name, password)
        if result == 'Joined successfully':
            print(f"Joined to game {name}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'message': 'Joined game successfully'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif result == 'Game not found':
            print(f"Game not found: {name}")
            self.send_response(404)
            self.end_headers()
            response = {'message': 'Game not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif result == 'Incorrect password':
            print(f"Incorrect password for game: {name}")
            self.send_response(403)
            self.end_headers()
            response = {'message': 'Incorrect password'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif result == 'Already joined':
            print(f"User already joined to game: {name}")
            self.send_response(409)
            self.end_headers()
            response = {'message': 'Already joined'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            print(f"Error joining game: {name}")
            self.send_response(500)
            self.end_headers()
            response = {'message': 'Error joining game'}
            self.wfile.write(json.dumps(response).encode('utf-8'))


    def handle_game_creation(self) -> None:
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        user_token = data.get('user_token')
        print(user_token)
        user_id = self.db_handler.get_user_id(user_token)
        name = data.get('name')
        password = data.get('password')
        tax = data.get('tax')
        paycheck_amount = data.get('paycheck_amount')
        paycheck_frequency = data.get('paycheck_frequency')
        start_capital = data.get('start_capital')

        print(f"Received game creation: user = {user_id}, name = {name}, password = {password}, start_capital = {start_capital}, tax = {tax}, paycheck_amount = {paycheck_amount}, paycheck_frequency = {paycheck_frequency}")

        games = {game[0] for game in self.db_handler.get_all_games()}
        if name in games:
            print("Game with identical name already exists")
            self.send_response(409)  # HTTP 409 Conflict status code
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': 'Game with identical name already registered'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        with self.lock:
            result = self.db_handler.create_game(user_id, name, password, start_capital, tax, paycheck_amount, paycheck_frequency)
        if result == 'Game created successfully':
            print(f"Game created successfully: {name}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'message': 'Game created successfully'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif result == 'Game already exists':
            print(f"Game already exists: {name}")
            self.send_response(409)
            self.end_headers()
            response = {'message': 'Game already exists'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            print(f"Error creating game: {name}")
            self.send_response(500)
            self.end_headers()
            response = {'message': result}
            self.wfile.write(json.dumps(response).encode('utf-8'))



    



Handler = BTM_BackEnd

with socketserver.TCPServer((IP_ADDRESS, PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
