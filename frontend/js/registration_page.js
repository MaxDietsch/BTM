async function sendRegistrationRequest(username, password) {
    const registrationRequest = {
        username: username,
        password: password
    };

    try {
        const response = await fetch('http://192.168.178.85:8000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(registrationRequest)
        });
    
        if (!response.ok) {
            if (response.status == 409) {
                console.log('Username already registered.');
                window.alert('Your entered username is already registered. Please choose another username.');
                document.querySelectorAll('input').forEach(input => input.value = '');
                return;
            }
            if (response.status == 500) {
                window.alert('Something went wrong creating your user. Please try again.');
                document.querySelectorAll('input').forEach(input => input.value = '');
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
    
        const data = await response.json();
        setSessionCookie(data.token);

        window.location.href = '../html/home_page.html';



        console.log('Response:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

function setSessionCookie(token) {
    document.cookie = `token=${token}; path=/; SameSite=Strict;`;
}


document.addEventListener('DOMContentLoaded', function () {

    const token = getCookie('token');
    if (token){
        window.location.href = '../landing_page.html';
    }

    const homeLink = document.getElementById('home');
    homeLink.addEventListener('click', function(event) {
        event.preventDefault();
        window.location.href = '../landing_page.html'; // Redirect to the home page
    });

    const registrationButton = document.getElementById('registration-button');
    registrationButton.addEventListener('click', async function (event) {
        event.preventDefault(); // Prevent default form submission
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (password !== confirmPassword) {
            window.alert('Passwords do not match. Please try again.');
            document.querySelectorAll('input').forEach(input => input.value = '');
            return;
        }

        await sendRegistrationRequest(username, password);
    });

    const menuIcon = document.querySelector('.menu-icon');
    const menuContent = document.querySelector('.menu-content');

    menuIcon.addEventListener('click', function() {
        menuContent.classList.toggle('show');
    });

    window.addEventListener('click', function(event) {
        if (!menuIcon.contains(event.target) && !menuContent.contains(event.target)) {
            menuContent.classList.remove('show');
        }
    });

});

function getCookie(name) {
    const value = `${document.cookie}`;
    const parts = value.split(`${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
