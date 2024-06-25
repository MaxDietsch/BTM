import sqlite3
from datetime import datetime
from typing import List, Optional


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
            
            cursor.execute('SELECT start_capital FROM Games WHERE id = ?', (game_id,))
            start_capital = cursor.fetchone()
            cursor.execute("""
                INSERT INTO Portfolios (user_id, game_id, liquid_cash)
                VALUES (?, ?, ?)
            """, (user_id, game_id, start_capital[0]))
            self.database_connection.commit()
            return 'Joined successfully'
        except sqlite3.Error as e:
            print(f"Error joining game: {e}")
            return 'Error'

    def create_game(self, user_id: int, name: str, password: str, start_capital: float, tax: float, paycheck_amount: float, paycheck_frequency: str) -> str:
        if not (tax >= 0 and tax < 100 and start_capital >= 0 and paycheck_amount >= 0 and paycheck_frequency >= 0):
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

            cursor.execute('''INSERT INTO Portfolios (user_id, game_id, liquid_cash)
                              VALUES (?, ?, ?)''',
                           (user_id, game_id, start_capital))
            self.database_connection.commit()

            return 'Game created successfully'
        except sqlite3.Error as e:
            print(f"Error creating game: {e}")
            return 'Error creating game'


    def valid_token(self, token) -> bool: 
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT 1 FROM Users WHERE token = ?', (token,))
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            print(f"Error validating token: {e}")
            return False


    def get_user_id(self, token: str) -> int:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT id FROM Users WHERE token = ?', (token,))
            id = cursor.fetchone()
            return id[0]
        except sqlite3.Error as e:
            print(f"Error fetching users: {e}")
            return None
    
    def get_user_name(self, token: str) -> int:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT username FROM Users WHERE token = ?', (token,))
            username = cursor.fetchone()
            return username[0]
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
        
    def get_user_liquid_cash(self, token: str) -> float:
        try:
            cursor = self.database_connection.cursor()
            query = '''
            SELECT p.liquid_cash
            FROM Users u
            JOIN Portfolios p ON u.id = p.user_id
            WHERE u.token = ?;
            '''
            cursor.execute(query, (token,))
            result = cursor.fetchone()
            if result:
                liquid_cash = result[0]
                return liquid_cash
            else:
                return 0
        except sqlite3.Error as e:
            print(f"Error fetching user liquid cash: {e}")
            return None
    
    def get_user_stocks(self, token: str, game_id: int) -> List[tuple]:
        try:
            cursor = self.database_connection.cursor()
            query = '''
            SELECT s.name, s.shares, s.value
            FROM Users u
            JOIN Portfolios p ON u.id = p.user_id
            JOIN Stocks s ON p.id = s.portfolio_id
            WHERE u.token = ? AND p.game_id = ?;
            '''
            cursor.execute(query, (token, game_id))
            stocks = cursor.fetchall()
            return stocks
        except sqlite3.Error as e:
            print(f"Error fetching user stocks: {e}")
            return None
    
    def get_user_investment_in_stock(self, token: str, game_id: int, stock_name: str) -> float:
        try:
            cursor = self.database_connection.cursor()
            query = '''
            SELECT s.value
            FROM Users u
            JOIN Portfolios p ON u.id = p.user_id
            JOIN Stocks s ON p.id = s.portfolio_id
            WHERE u.token = ? AND p.game_id = ? AND s.name = ?;
            '''
            cursor.execute(query, (token, game_id, stock_name))
            total_investment = cursor.fetchone()
            return total_investment[0] if total_investment is not None else 0.0
        except sqlite3.Error as e:
            print(f"Error fetching user investment in stock: {e}")
            return None
        

    def buy_stock(self, token: str, game_id: int, stock_name: str, amount: int, shares: float) -> bool:
        try:
            cursor = self.database_connection.cursor()

            # Get the user ID based on the token
            user_id = self.get_user_id(token)

            # Get the user's current liquid cash
            current_liquid_cash = self.get_user_liquid_cash(token)

            if current_liquid_cash < amount:
                print("Insufficient funds to buy the stock.")
                return False

            # Update the user's liquid cash
            new_liquid_cash = current_liquid_cash - amount
            cursor.execute('UPDATE Portfolios SET liquid_cash = ? WHERE user_id = ? AND game_id = ?', (new_liquid_cash, user_id, game_id))

            # Insert or update the stock in the Stocks table
            cursor.execute('''
                INSERT INTO Stocks (portfolio_id, name, value, shares)
                SELECT p.id, ?, ?, ?
                FROM Portfolios p
                WHERE p.user_id = ? AND p.game_id = ?
                ON CONFLICT(portfolio_id, name)
                DO UPDATE SET value = value + excluded.value, shares = shares + excluded.shares;
                ''', (stock_name, amount, shares, user_id, game_id))

            self.database_connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error buying stock: {e}")
            self.database_connection.rollback()
            return False

    def sell_stock(self, token: str, game_id: int, stock_name: str, sell_value: float, sell_shares: int) -> bool:
        try:
            cursor = self.database_connection.cursor()

            # Get the user ID based on the token
            user_id = self.get_user_id(token)

            # Calculate new liquid cash after selling
            current_liquid_cash = self.get_user_liquid_cash(token)
            new_liquid_cash = current_liquid_cash + sell_value
            print(sell_value)

            # Update user's liquid cash in Portfolios table
            cursor.execute('UPDATE Portfolios SET liquid_cash = ? WHERE user_id = ? AND game_id = ?', (new_liquid_cash, user_id, game_id))

            # Update stocks in Stocks table
            cursor.execute('''
                UPDATE Stocks
                SET shares = shares - ?, value = value - ?
                WHERE portfolio_id IN (
                    SELECT p.id
                    FROM Portfolios p
                    WHERE p.user_id = ? AND p.game_id = ?
                ) AND name = ?
                ''', (sell_shares, sell_value, user_id, game_id, stock_name))

            self.database_connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error selling stock: {e}")
            self.database_connection.rollback()
            return False

    def get_transactions(self):
        try:
            cursor = self.database_connection.cursor()
            # Fetch all transactions
            cursor.execute('SELECT * FROM transactions')
            transactions = cursor.fetchall()

            return transactions

        except sqlite3.Error as e:
            print(f"Error fetching transactions: {e}")
            return []
        
    def delete_transaction(self, transaction_id):
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            self.database_connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting transaction: {e}")
            self.database_connection.rollback()
            return False

    
    def get_game_id(self, game_name: str) -> int:
        try:
            cursor = self.database_connection.cursor()
            query = 'SELECT id FROM Games WHERE name = ?'
            cursor.execute(query, (game_name,))
            result = cursor.fetchone()
            return result[0]
        except sqlite3.Error as e:
            print(f"Error fetching game ID: {e}")
            return None

    def store_transaction(self, is_buy: bool, user: str, amount: str, price: str, game_id: str, symbol: str, timestamp: str) -> bool:
        try: 
            cursor = self.database_connection.cursor()
            cursor.execute('''INSERT INTO transactions (user, amount, price, game_id, symbol, timestamp, is_buy)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (user, amount, price, game_id, symbol, timestamp, is_buy))
            
            self.database_connection.commit()  # Commit the transaction
            print("Transaction successfully stored.")
            return True 
        except sqlite3.Error as e:
            print(f"Error storing transaction: {e}")
            return False
    
    

    def get_game_start_capital(self, game_id: int) -> Optional[float]:
        try:
            cursor = self.database_connection.cursor()
            query = "SELECT start_capital FROM Games WHERE id = ?"
            cursor.execute(query, (game_id,))
            row = cursor.fetchone()
            if row:
                return float(row['start_capital'])
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error fetching game ID: {e}")
            return None
    
    def create_user_portfolio(self, user_id: int, game_id: int, start_capital: float) -> None:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute("""
                INSERT INTO Portfolios (user_id, game_id, liquid_cash)
                VALUES (?, ?, ?)
            """, (user_id, game_id, start_capital))
            print(f"Successfully created portfolio for user {user_id} in game {game_id} with start capital ${start_capital:.2f}")
        except sqlite3.Error as e:
            print(f"Error fetching game ID: {e}")
            return None
    
    def get_users_in_game(self, game_id: int) -> List[str]:
        try:
            cursor = self.database_connection.cursor()
            query = '''
                SELECT DISTINCT u.token, u.username
                FROM Users u
                INNER JOIN Portfolios p ON u.id = p.user_id
                WHERE p.game_id = ?
            '''

            cursor.execute(query, (game_id,))
            rows = cursor.fetchall()

            return rows

        except sqlite3.Error as e:
            print(f"Error retrieving users in game: {e}")
            return []
        
    
    def get_last_update_for_game_id(self, game_id: int) -> Optional[str]:
        try:
            cursor = self.database_connection.cursor()
            query = "SELECT last_update FROM Games WHERE id = ?"
            cursor.execute(query, (game_id,))
            result = cursor.fetchone()
            if result:
                return result[0]  # Return the first column value (last_update)
            else:
                return None
        except sqlite3.Error as e:
            print(f"Error retrieving last update for game_id {game_id}: {e}")
            return None
    
    def get_paycheck_interval(self, game_id: int) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT paycheck_frequency FROM Games WHERE id = ?', (game_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                raise ValueError(f"No game found with id {game_id}")

        except sqlite3.Error as e:
            print(f"SQLite error while fetching paycheck interval: {e}")
            return None

    def get_paycheck_amount(self, game_id: int) -> str:
        try:
            cursor = self.database_connection.cursor()
            cursor.execute('SELECT paycheck_amount FROM Games WHERE id = ?', (game_id,))
            result = cursor.fetchone()

            if result:
                return result[0]
            else:
                raise ValueError(f"No game found with id {game_id}")

        except sqlite3.Error as e:
            print(f"SQLite error while fetching paycheck interval: {e}")
            return None


    def update_cash(self, game_id: int, amount_to_add: float) -> bool:
        try:
            cursor = self.database_connection.cursor()
            
            # Retrieve all users in the specified game
            cursor.execute('''
                SELECT u.id AS user_id, p.id AS portfolio_id
                FROM Users u
                INNER JOIN Portfolios p ON u.id = p.user_id
                WHERE p.game_id = ?
            ''', (game_id,))
            
            rows = cursor.fetchall()
            
            if not rows:
                print(f"No users found for game with id {game_id}")
                return False
            
            # Update liquid cash for each user's portfolio
            for row in rows:
                user_id = row[0]  # Accessing user_id via index
                portfolio_id = row[1]  # Accessing portfolio_id via index
                
                # Update liquid cash
                cursor.execute('''
                    UPDATE Portfolios
                    SET liquid_cash = liquid_cash + ?
                    WHERE id = ?
                ''', (amount_to_add, portfolio_id))
            
            # Update last_update column of the game to current date
            current_date = datetime.now().date().isoformat()
            cursor.execute('''
                UPDATE Games
                SET last_update = ?
                WHERE id = ?
            ''', (current_date, game_id))
            self.database_connection.commit()

            return True
        
        except sqlite3.Error as e:
            print(f"SQLite error while updating cash: {e}")
            return False