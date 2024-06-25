import http.server
import socketserver
import json
from threading import Lock
import uuid
from db_handler import DatabaseHandler
from  stock_api import StockAPI
from datetime import datetime

PORT = 8000
DIRECTORY = "./frontend"  # The directory where your HTML and other static files are located
IP_ADDRESS = "192.168.178.85"
#IP_ADDRESS = "192.168.178.30"
DB_NAME = "database/btm.db"


class BTM_BackEnd(http.server.SimpleHTTPRequestHandler):
    lock = Lock()

    def __init__(self, *args, **kwargs):
        self.db_handler = DatabaseHandler(DB_NAME)
        self.stock_market = StockAPI()
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        self.update_transactions()
        if self.path == '/':
            self.path = 'landing_page.html'
        elif self.path == '/user-items':
            self.handle_user_items()
            return 
        return super().do_GET()

    def do_POST(self) -> None:
        self.update_transactions()
        if self.path == '/register':
            self.handle_register()
        elif self.path == '/login':
            self.handle_login()
        elif self.path == '/create-game':
            self.handle_game_creation()
        elif self.path == '/join-game':
            self.handle_game_join()
        elif self.path == '/user-info':
            self.handle_user_info()
        elif self.path =='/find-stock':
            self.handle_find_stock()
        elif self.path == '/stock-info':
            self.handle_stock_info()
        elif self.path == '/buy-stock':
            self.handle_buy_stock()
        elif self.path == '/sell-stock':
            self.handle_sell_stock()
        elif self.path == '/buy-stock-limit':
            self.handle_stock_transaction(is_buy = True)
        elif self.path == '/sell-stock-limit':
            self.handle_stock_transaction(is_buy = False)
        elif self.path == '/game-ranking':
            self.handle_game_ranking()
        else:
            self.send_response(404)
            self.end_headers()
    
    def update_paychecks(self, game_id) -> None: 
        last_up = self.db_handler.get_last_update_for_game_id(game_id)
        paycheck_interval = self.db_handler.get_paycheck_interval(game_id)
        paycheck_amount = self.db_handler.get_paycheck_amount(game_id)
        last_up = datetime.strptime(last_up, '%Y-%m-%d').date()
        current_date = datetime.now().date()
        delta = (current_date - last_up).days
        if delta == 0:
            return 
        cash = paycheck_amount * (delta // int(paycheck_interval))
        with self.lock:
            self.db_handler.update_cash(game_id, cash )
            print("Paychecks released in game: {game_id}.")


    def handle_game_ranking(self) -> None: 
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        game_name = data.get('game_name')
        game_id = self.db_handler.get_game_id(game_name)
        self.update_paychecks(game_id)
        users = self.db_handler.get_users_in_game(game_id)
        table = []
        for user in users: 
            liquid = self.db_handler.get_user_liquid_cash(user[0])
            stocks = self.db_handler.get_user_stocks(user[0], game_id)
            portfolio = 0
            for stock in stocks: 
                portfolio += self.stock_market.get_stock_price(stock[0]) * stock[1]
            total = portfolio + liquid
            table.append({'user': user[1], 'balance': total})
        table.sort(key = lambda x: -x['balance'])
        
        response = {'table': table}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))        

    
    def update_transactions(self) -> None: 
        transactions = self.db_handler.get_transactions()
        for transaction in transactions: 
            hist = self.stock_market.get_stock_history_since_time(transaction[5], transaction[6])
            for stock_item in hist: 
                if transaction[7]:
                    if stock_item['Low'] <= transaction[3]:
                        shares = transaction[2] // transaction[3]
                        self.db_handler.buy_stock(transaction[1], transaction[4], transaction[5], transaction[3] * shares, shares)
                        self.db_handler.delete_transaction(transaction[0])
                        print("Buy transaction done for game: {transaction[4]}, user: {transaction[1]}, symbol: {transaction[5]}}")
                        break

                if not transaction[7]:
                    if stock_item['High'] >= transaction[3]:
                        shares = transaction[2] // transaction[3]
                        self.db_handler.sell_stock(transaction[1], transaction[4], transaction[5], transaction[3] * shares, shares)
                        self.db_handler.delete_transaction(transaction[0])
                        print("Sell transaction done for game: {transaction[4]}, user: {transaction[1]}, symbol: {transaction[5]}}")
                        break

    def handle_sell_stock(self) -> None:
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        symbol = data.get('stock_name')
        game = data.get('game_name')
        game_id = self.db_handler.get_game_id(game)
        token = self.handle_auth()
        amount = int(data.get('amount'))
        current_holdings = self.db_handler.get_user_investment_in_stock(token, game_id, symbol)
        current_price = self.stock_market.get_stock_price(symbol)
        share_holdings = current_holdings // current_price
        shares = amount // current_price
        sell_value = shares * current_price
        print(f'User {token} sells {shares} shares of {symbol} in game {game}.')

        if share_holdings < shares or share_holdings == 0:
            response = {'success': False, 'msg': 'You do not have enough shares to sell the entered amount.'}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
 
        with self.lock:
            result = self.db_handler.sell_stock(token, game_id, symbol, sell_value, shares)
        
        if result:
            response = {'success': True}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            response = {'success': False, 'msg': 'Something went wrong selling your stock. Please try again.'}
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))



    def handle_stock_transaction(self, is_buy: bool) -> None: 
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        symbol = data.get('stock_name')
        game = data.get('game_name')
        game_id = self.db_handler.get_game_id(game)
        token = self.handle_auth()
        amount = int(data.get('amount'))
        price = float(data.get('price'))

        print(f'User {token} stores transaction ({is_buy}) of {symbol} in game {game}.')


        with self.lock: 
            success = self.db_handler.store_transaction(
                is_buy = is_buy, 
                user = token,
                amount =  amount,
                price = price,
                game_id = game_id,
                symbol = symbol,
                timestamp = datetime.now().date().isoformat())
        if success: 
            response = {'success': True}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else: 
            response = {'success': False}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        
    def handle_buy_stock(self) -> None: 
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        symbol = data.get('stock_name')
        game = data.get('game_name')
        game_id = self.db_handler.get_game_id(game)
        token = self.handle_auth()
        amount = int(data.get('amount'))
        liquid_cash = self.db_handler.get_user_liquid_cash(token)
        current_price = self.stock_market.get_stock_price(symbol)
        shares = amount // current_price
        amount = shares * current_price
        print(f'User {token} buys {shares} shares of {symbol} in game {game}.')


        if liquid_cash < amount: 
            response = {'success': False, 'msg': 'You have not enough liquid money to invest the entered amount. '}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        if current_price > amount: 
            response = {'success': False, 'msg': 'You must invest an amount of money that is at least as valuable as 1 share of the stock.'}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        else:
            with self.lock:
                result = self.db_handler.buy_stock(token, game_id, symbol, amount, shares)
            if result:
                response = {'success': True}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else: 
                response = {'success': False, 'msg': 'Something went wrong buying your stock. Please try again.'}
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                


    def handle_auth(self) -> str: 
        auth_header = self.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split("Bearer ")[-1]
        
        if not token:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        if not self.db_handler.valid_token(token):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return

        return token 
    
    def handle_find_stock(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        symbol = data.get('stock_name')
        valid = self.stock_market.check_symbol(symbol)
        if valid: 
            response = { 'valid': True}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else: 
            response = {'valid': False}
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))


    
    def handle_stock_info(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        symbol = data.get('stock_name')
        game = data.get('game_name')
        game_id = self.db_handler.get_game_id(game)
        token = self.handle_auth()
        user_name = self.db_handler.get_user_name(token)
        interval = data.get('interval')

        print(f'Search {symbol} for game {game} of user {user_name}')

        info = self.stock_market.get_stock_history(symbol, interval)
        info = self.stock_market.format_chart_data(info)

        current_price = self.stock_market.get_stock_price(symbol)
        liquid_cash = self.db_handler.get_user_liquid_cash(token)
        investment = self.db_handler.get_user_investment_in_stock(token, game_id, symbol)

        response = {
                'username': user_name,
                'stock_name': symbol,
                'current_price': current_price,
                'history': info,
                'liquid_cash': liquid_cash,
                'current_investment': investment
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
        

    def handle_user_info(self) -> None:
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        token = self.handle_auth()
        user_id = self.db_handler.get_user_id(token)
        
        username = self.db_handler.get_user_name(token)
        game_name = data.get('game_name')
        game_id = self.db_handler.get_game_id(game_name)
        self.update_paychecks(game_id)
        liquid_balance = self.db_handler.get_user_liquid_cash(token)
        stocks = self.db_handler.get_user_stocks(token, game_id)
        print(f"Get user items of {token} and Game: {game_name}")

        stocklist = []
        for stock in stocks: 
            name, shares, value = stock
            current_price = self.stock_market.get_stock_price(name)
            if current_price is None:
                continue

            current_val = shares * current_price
            performance = current_val / value - 1
            gain = current_val - value
            stocklist.append({'name': name, 
                              'current_price': current_price,
                              'performance': performance,
                              'current_val': current_val,
                              'gain': gain})
            
        total_balance = sum(item['current_val'] for item in stocklist) + liquid_balance
        self.send_response(200)  
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'username': username,
                    'liquid_cash': liquid_balance,
                    'total_balance': total_balance,
                    'stocklist': stocklist}
        self.wfile.write(json.dumps(response).encode('utf-8'))


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
        token = self.handle_auth()
        print(f"Get user items of {token}")
        
        user_id = self.db_handler.get_user_id(token)
        
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


