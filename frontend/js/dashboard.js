import { IP_ADDRESS } from './IP_ADDRESS.js';

document.addEventListener('DOMContentLoaded', function() {
    const token = getCookie('token');

    const urlParams = new URLSearchParams(window.location.search);
    const game_name = urlParams.get('Game');
    const tbody = document.getElementById('ranking-body');


    // Game ranking 
    fetch(`http://${IP_ADDRESS}:8000/game-ranking`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ game_name: game_name })
        })
        .then(response => response.json())
        .then(data => {

            var position = 1;
            data.table.forEach(function(user) {
                // Create a new row element
                var row = document.createElement('tr');

                var positionCell = document.createElement('td');
                positionCell.textContent = position++;
                row.appendChild(positionCell);

                // Create and add cells (td) for each property in the JSON object
                var nameCell = document.createElement('td');
                nameCell.textContent = user.user;
                row.appendChild(nameCell);

                var balanceCell = document.createElement('td');
                balanceCell.textContent = user.balance.toFixed(2);
                row.appendChild(balanceCell);

                // Append the row to the table body
                tbody.appendChild(row);
            });
            
        })
        .catch(error => {
        });




    if (!token) {
        window.location.href = '../landing_page.html'; // Redirect to login page if not logged in
        return;
    }

    const logoutLink = document.getElementById('logout');
    const homeLink = document.getElementById('home');

    homeLink.addEventListener('click', function(event) {
        event.preventDefault();
        window.location.href = '../landing_page.html'; // Redirect to the home page
    });

    logoutLink.addEventListener('click', function(event) {
        event.preventDefault();
        document.cookie = 'token=; path=/;';
        window.location.href = '../landing_page.html';
    });

    const menuIcon = document.querySelector('.menu-icon');
    const menuContent = document.querySelector('.menu-content');

    menuIcon.addEventListener('click', function() {
        menuContent.classList.toggle('show');
    });

    // Function to get cookie value by name
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    // Fetch user information from the server
    fetch(`http://${IP_ADDRESS}:8000/user-info`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ game_name: game_name })
    })
    .then(response => response.json())
    .then(data => {
        // Update welcome message with username
        if (data.username) {
            document.querySelector('.welcome-message').textContent = `Hello, ${data.username} \n in Game ${game_name}`;
        } else {
            console.error('Username not found in response');
        }
    
        // Update total balance
        if (data.total_balance !== undefined) {
            document.getElementById('total-balance').textContent = `$${data.total_balance.toFixed(2)}`;
        }
    
        // Update liquid cash
        if (data.liquid_cash !== undefined) {
            document.getElementById('liquid-cash').textContent = `$${data.liquid_cash.toFixed(2)}`;
        }
    
        // Update stock list
        if (data.stocklist && data.stocklist.length > 0) {
            const stockListContainer = document.getElementById('stock-list');
            stockListContainer.innerHTML = ''; // Clear existing content
    
            data.stocklist.forEach(stock => {
                const stockItem = document.createElement('div');
                stockItem.classList.add('stock-item');
                stockItem.innerHTML = `
                    <div class="stock-name">${stock.name}</div>
                    <div class="stock-details">
                        <div>Current Price: $${stock.current_price.toFixed(2)}</div>
                        <div>Performance: ${(stock.performance * 100).toFixed(2)}%</div>
                        <div>Current Value: $${stock.current_val.toFixed(2)}</div>
                        <div>Gain: $${stock.gain.toFixed(2)}</div>
                    </div>
                `;
                stockListContainer.appendChild(stockItem);
            });
        } else {
            console.log('Stocklist not found or empty in response');
        }
    })
    .catch(error => {
        console.error('Error fetching user information:', error);
    });


    document.getElementById('search-btn').addEventListener('click', function() {
        document.getElementById('search-modal').style.display = 'block';
    });
    
    // Function to handle the close button in the Buy modal
    document.getElementById('search-close').addEventListener('click', function() {
        document.getElementById('search-modal').style.display = 'none';
    });
    
    // Function to handle clicking outside the modal
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('search-modal');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
    
    // Function to handle Buy Stock form submission
    document.getElementById('search-stock-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const stockSymbol = document.getElementById('stock-symbol').value;
        console.log('Searching stock:', stockSymbol);
        
        
        fetch(`http://${IP_ADDRESS}:8000/find-stock`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ game_name: game_name, stock_name: stockSymbol })
        })
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                window.location.href = `../html/stock_info.html?Game=${encodeURIComponent(game_name)}&Symbol=${encodeURIComponent(stockSymbol)}`;
            } else {
                alert('This stock does not exist. Please enter a valid stock symbol.');
                document.getElementById('search-stock-form').reset();
            }
        })
        .catch(error => {
            console.error('Error fetching user information:', error);
        });
    
        document.getElementById('search-modal').style.display = 'none';
        document.getElementById('search-stock-form').reset();
    });
});
