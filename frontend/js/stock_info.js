import { IP_ADDRESS } from './IP_ADDRESS.js';

const logoutLink = document.getElementById('logout');
const homeLink = document.getElementById('home');
const buyBtn = document.getElementById('buy-btn');
const buyModal = document.getElementById('buy-modal');
const buyClose = document.getElementById('buy-close');
const buyNowForm = document.getElementById('buy-now-form');
const buyNowAmount = document.getElementById('buy-now-amount');
const buyPriceForm = document.getElementById('buy-at-price-form');
const buyPriceAmount = document.getElementById('buy-at-price-amount');
const buyPricePrice = document.getElementById('buy-price');
const sellBtn = document.getElementById('sell-btn');
const sellModal = document.getElementById('sell-modal');
const sellClose = document.getElementById('sell-close');
const sellNowForm = document.getElementById('sell-now-form');
const sellNowAmount = document.getElementById('sell-now-amount');
const sellPriceForm = document.getElementById('sell-at-price-form');
const sellPriceAmount = document.getElementById('sell-at-price-amount');
const sellPricePrice = document.getElementById('sell-price');
const searchBtn = document.getElementById('search-btn');
const searchModal = document.getElementById('search-modal');
const searchClose = document.getElementById('search-close');
const searchForm = document.getElementById('search-stock-form');


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

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function fetchStockData(interval) {
    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = getUrlParameter('Symbol');

    if (!token || !gameName || !stockSymbol) {
        alert('Missing token, game name, or stock symbol. Reload the whole Webpage');
        return;
    }

    const requestData = {
        game_name: gameName,
        stock_name: stockSymbol,
        interval: interval,
    };

    return fetch(`http://${IP_ADDRESS}:8000/stock-info`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    });
}

function updatePageWithStockData(data) {
    document.querySelector('.username').textContent = `Hello, ${data.username} in Game ${getUrlParameter('Game')}`;
    document.getElementById('liquid-cash').textContent = `$${data.liquid_cash}`;
    document.getElementById('invested-amount').textContent = `$${data.current_investment}`;
    document.getElementById('stock_value').textContent = `$${data.current_price}`;
    document.querySelector('.stock-name').textContent = `${data.stock_name}`;

    // Format chart data
    const formattedChartData = data.history

    // Update chart
    const ctx = document.getElementById('stock-chart').getContext('2d');

    if (window.myChart) {
        window.myChart.destroy();
    }

    window.myChart = new Chart(ctx, {
        type: 'line',
        data: formattedChartData,
        options: {}
    });
}

function initializeIntervalButtons() {
    const buttons = document.querySelectorAll('.interval-buttons .btn');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const interval = button.getAttribute('data-interval');
            fetchStockData(interval)
            .then(data => updatePageWithStockData(data))
            .catch(error => {
                console.error('Error fetching stock data:', error);
                alert('An error occurred while fetching stock data. Please try again.');
            });
        });
    });
}

function handleBuyFormSubmit(event) {
    event.preventDefault();

    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = getUrlParameter('Symbol');
    const amountToInvest = buyNowAmount.value;

    if (!token || !gameName || !stockSymbol || !amountToInvest) {
        alert('Missing token, game name, stock symbol, or amount to invest.');
        return;
    }

    const requestData = {
        game_name: gameName,
        stock_name: stockSymbol,
        amount: amountToInvest
    };

    fetch(`http://${IP_ADDRESS}:8000/buy-stock`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            fetchStockData(getUrlParameter('interval') || '1y')
            .then(data => {
                updatePageWithStockData(data);
                buyModal.style.display = 'none'; // Close the modal
            });
        } else {
            alert('Failed to buy stock: ' + data.msg);
        }
    })
    .catch(error => {
        console.error('Error buying stock:', error);
        alert('An error occurred while buying stock. Please try again.');
    });
}



function handleSellFormSubmit(event) {
    event.preventDefault();

    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = getUrlParameter('Symbol');
    const amountToSell = sellNowAmount.value; 

    if (!token || !gameName || !stockSymbol || !amountToSell) {
        alert('Missing token, game name, stock symbol, or amount to sell.');
        return;
    }

    const requestData = {
        game_name: gameName,
        stock_name: stockSymbol,
        amount: amountToSell
    };

    fetch(`http://${IP_ADDRESS}:8000/sell-stock`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            fetchStockData(getUrlParameter('interval') || '1y')
            .then(data => {
                updatePageWithStockData(data);
                sellModal.style.display = 'none'; // Close the modal
            });
        } else {
            alert('Failed to sell stock: ' + data.msg);
        }
    })
    .catch(error => {
        console.error('Error selling stock:', error);
        alert('An error occurred while selling stock. Please try again.');
    });
}





function handleBuyPriceFormSubmit(event) {
    event.preventDefault();

    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = getUrlParameter('Symbol');
    const amountToInvest = buyPriceAmount.value;
    const price = buyPricePrice.value;

    if (!token || !gameName || !stockSymbol || !amountToInvest || !price) {
        alert('Missing token, game name, stock symbol, or amount to invest.');
        return;
    }

    const requestData = {
        game_name: gameName,
        stock_name: stockSymbol,
        amount: amountToInvest,
        price: price
    };

    fetch(`http://${IP_ADDRESS}:8000/buy-stock-limit`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            fetchStockData(getUrlParameter('interval') || '1y')
            .then(data => {
                updatePageWithStockData(data);
                buyModal.style.display = 'none'; // Close the modal
            });
            alert('Your transaction is stored and will be executed as soon as the stock price drops below your limit.');

        } else {
            alert('Failed to buy stock: ' + data.msg + 'Please try again.');
        }
    })
    .catch(error => {
        console.error('Error buying stock:', error);
        alert('An error occurred while buying stock. Please try again.');
    });
}


function handleSellPriceFormSubmit(event) {
    event.preventDefault();

    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = getUrlParameter('Symbol');
    const amountToSell = sellPriceAmount.value;
    const sellPrice = sellPricePrice.value;

    if (!token || !gameName || !stockSymbol || !amountToSell || !sellPrice) {
        alert('Missing token, game name, stock symbol, amount to sell, or sell price.');
        return;
    }

    const requestData = {
        game_name: gameName,
        stock_name: stockSymbol,
        amount: amountToSell,
        price: sellPrice
    };

    fetch(`http://${IP_ADDRESS}:8000/sell-stock-limit`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            fetchStockData(getUrlParameter('interval') || '1y')
            .then(data => {
                updatePageWithStockData(data);
                sellModal.style.display = 'none'; // Close the modal
            });
            alert('Your sell limit order is stored and will be executed as soon as the stock price reaches your limit.');
        } else {
            alert('Failed to sell stock: ' + data.msg + ' Please try again.');
        }
    })
    .catch(error => {
        console.error('Error selling stock:', error);
        alert('An error occurred while selling stock. Please try again.');
    });
}




function handleSearchFormSubmit(event) {
    event.preventDefault();

    const token = getCookie('token');
    const gameName = getUrlParameter('Game');
    const stockSymbol = document.getElementById('stock-symbol').value;

    if (!token || !gameName || !stockSymbol) {
        alert('Missing token, game name, or stock symbol.');
        return;
    }

    fetch(`http://${IP_ADDRESS}:8000/find-stock`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ game_name: gameName, stock_name: stockSymbol })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.valid) {
            window.location.href = `../html/stock_info.html?Game=${encodeURIComponent(gameName)}&Symbol=${encodeURIComponent(stockSymbol)}`;
        } else {
            alert('This stock does not exist. Please enter a valid stock symbol.');
            searchForm.reset();
        }
    })
    .catch(error => {
        console.error('Error finding stock:', error);
        alert('An error occurred while searching for the stock. Please try again.');
    });

    searchModal.style.display = 'none';
    searchForm.reset();
}


document.addEventListener('DOMContentLoaded', function () {

    document.getElementById('defaultOpenBuy').click();
    document.getElementById('defaultOpenSell').click();

    fetchStockData('1y')
    .then(data => {
        updatePageWithStockData(data);
        initializeIntervalButtons();
    })
    .catch(error => {
        console.error('Error initializing chart:', error);
        alert('An error occurred while initializing the chart. Please try again.');
    });

    // HANDLE BUY
    buyBtn.addEventListener('click', () => {
        buyModal.style.display = 'block';
    });
    buyClose.addEventListener('click', () => {
        buyModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target === buyModal) {
            buyModal.style.display = 'none';
        }
    });
    buyNowForm.addEventListener('submit', handleBuyFormSubmit);
    buyPriceForm.addEventListener('submit', handleBuyPriceFormSubmit);

    
    sellBtn.addEventListener('click', () => {
        sellModal.style.display = 'block';
    });
    sellClose.addEventListener('click', () => {
        sellModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target === sellModal) {
            sellModal.style.display = 'none';
        }
    });
    sellNowForm.addEventListener('submit', handleSellFormSubmit);
    sellPriceForm.addEventListener('submit', handleSellPriceFormSubmit);

    // Search functionality
    searchBtn.addEventListener('click', () => {
        searchModal.style.display = 'block';
    });

    searchClose.addEventListener('click', () => {
        searchModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === searchModal) {
            searchModal.style.display = 'none';
        }
    });

    searchForm.addEventListener('submit', handleSearchFormSubmit);
});
