document.addEventListener('DOMContentLoaded', function() {
    // Check if the user is logged in by checking for the token
    const token = getCookie('token');
    console.log(document.cookie)
    if (!token) {
        window.location.href = '../landing_page.html'; // Redirect to login page if not logged in
    } else {
        loadUserItems(token);
    }


    // create game popup
    const createGameBtn = document.getElementById('create-game-btn');
    const createGameModal = document.getElementById('create-game-modal');
    const closeBtn = document.getElementsByClassName('close')[0];
    const menuIcon = document.querySelector('.menu-icon');
    const menuContent = document.querySelector('.menu-content');
    const logoutLink = document.getElementById('logout');
    const homeLink = document.getElementById('home');


    createGameBtn.addEventListener('click', function() {
        createGameModal.style.display = 'block';
        console.log('Create a new game clicked');
    });

    closeBtn.addEventListener('click', function() {
        createGameModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target == createGameModal) {
            createGameModal.style.display = 'none';
        }
        if (!menuIcon.contains(event.target) && !menuContent.contains(event.target)) {
            menuContent.classList.remove('show');
        }
    });

    document.getElementById('create-game-form').addEventListener('submit', async function(event) {
        event.preventDefault();

        const gameName = document.getElementById('game-name').value;
        const gamePassword = document.getElementById('game-password').value;
        const tax = document.getElementById('tax').value;
        const paycheckAmount = document.getElementById('paycheck-amount').value;
        const paycheckFrequency = document.getElementById('paycheck-frequency').value;
        const startCapital = document.getElementById('start-capital').value;
        

        if (isNaN(startCapital) || isNaN(tax) || isNaN(paycheckAmount) || isNaN(paycheckFrequency)) {
            alert('Please enter valid numerical values.');
            return;
        }

        const createGameRequest = {
            user_token: token,
            name: gameName,
            password: gamePassword,
            start_capital: parseFloat(startCapital),
            tax: parseFloat(tax),
            paycheck_amount: parseFloat(paycheckAmount),
            paycheck_frequency: parseFloat(paycheckFrequency)
        };

        try {
            const response = await fetch('http://192.168.178.85:8000/create-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(createGameRequest)
            });

            if (!response.ok) {
                if (response.status == 409) {
                    console.log(' Game with identical name already registered');
                    window.alert('Your entered name of the game is already registered. Please choose another name.');
                    document.querySelectorAll('input').forEach(input => input.value = '');
                    return;
                }
                if (response.status == 500) {
                    window.alert('Something went wrong creating your game. Please try again.');
                    document.querySelectorAll('input').forEach(input => input.value = '');
                    return; 
                }
                
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Game created:', data);

            // Close the modal and reset the form
            createGameModal.style.display = 'none';
            document.getElementById('create-game-form').reset();

            window.location.href = `../html/dashboard.html?Game=${encodeURIComponent(gameName)}`;

        } catch (error) {
            console.error('Error creating game:', error);
        }
    });


    // join game popup 
    const joinGameBtn = document.getElementById('join-game-btn');
    const joinGameModal = document.getElementById('join-game-modal');
    const joinCloseBtn = document.getElementsByClassName('join-close')[0];

    joinGameBtn.addEventListener('click', function() {
        joinGameModal.style.display = 'block';
    });

    joinCloseBtn.addEventListener('click', function() {
        joinGameModal.style.display = 'none';
    });

    document.getElementById('join-game-form').addEventListener('submit', async function(event) {
        event.preventDefault();

        const gameName = document.getElementById('join-game-name').value;
        const gamePassword = document.getElementById('join-game-password').value;
        
        const joinGameRequest = {
            user_token: token,
            name: gameName,
            password: gamePassword
        };

        try {
            const response = await fetch('http://192.168.178.85:8000/join-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(joinGameRequest)
            });

            if (!response.ok) {
                if (response.status == 404) {
                    console.log('Game not found');
                    window.alert('The specified game was not found. Please check the game name.');
                } else if (response.status == 403) {
                    console.log('Incorrect password for game');
                    window.alert('The password you entered is incorrect. Please try again.');
                } else if (response.status == 409) {
                    console.log('User already joined to game');
                    window.alert('You have already joined this game.');
                } else {
                    console.log('Error joining game');
                    window.alert('Something went wrong joining the game. Please try again.');
                }
                document.querySelectorAll('input').forEach(input => input.value = '');
                return;
            }

            const data = await response.json();
            console.log('Game join:', data);

            // Close the modal and reset the form
            joinGameModal.style.display = 'none';
            document.getElementById('join-game-form').reset();
            
            window.location.href = `../html/dashboard.html?Game=${encodeURIComponent(gameName)}`;


        } catch (error) {
            console.error('Error creating game:', error);
        }
    });


    document.getElementById('select-item-btn').addEventListener('click', function() {
        const dropdown = document.getElementById('dropdown');
        const selectedItem = dropdown.options[dropdown.selectedIndex].textContent;

        window.location.href = `../html/dashboard.html?Game=${encodeURIComponent(selectedItem)}`;
        console.log('Selected item:', selectedItem);
    });




    menuIcon.addEventListener('click', function() {
        menuContent.classList.toggle('show');
    });

    homeLink.addEventListener('click', function(event) {
        event.preventDefault();
        window.location.href = '../landing_page.html'; // Redirect to the home page
    });

    logoutLink.addEventListener('click', function(event) {
        event.preventDefault();
        document.cookie = 'token=; path=/;';
        window.location.href = '../landing_page.html';
    });
});



function loadUserItems(token) {
    fetch('http://192.168.178.85:8000/user-items', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status == 401) {
                console.log('Unauthorized access');
                window.alert('Unauthorized access, either your token or the user is unvalid');
                return;
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Data received:', data); // Log the data to check its format
        const dropdown = document.getElementById('dropdown');
        dropdown.innerHTML = ''; // Clear existing options
        if (data.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No games found';
            option.className = 'gray-option'; // Apply the CSS class
            dropdown.appendChild(option);
        } else {
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = item.name;
                dropdown.appendChild(option);
            });
        }
    })
    .catch(error => {
        console.error('Error fetching user items:', error);
    });
}

function getCookie(name) {
    const value = `${document.cookie}`;
    const parts = value.split(`${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
