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
                return None
        except sqlite3.Error as e:
            print(f"Error fetching user liquid cash: {e}")
            return None
    
    def get_user_stocks(self, token: str, game_id: int) -> List[tuple]:
        try:
            cursor = self.database_connection.cursor()
            query = '''
            SELECT s.name, s.bought, s.value
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