document.addEventListener('DOMContentLoaded', function () {

    const token = getCookie('token');

    const homeLink = document.getElementById('home');
    homeLink.addEventListener('click', function(event) {
        event.preventDefault();
        window.location.href = 'landing_page.html'; // Redirect to the home page
    });
    const buttonsDiv = document.querySelector('.buttons');
    const loginButton = document.getElementById('login-button');
    const registerButton = document.getElementById('register-button');

    if (token) {
        // Remove existing buttons
        if (loginButton) loginButton.remove();
        if (registerButton) registerButton.remove();
        
        // Create a new button
        const newButton = document.createElement('button');
        newButton.id = 'new-button';
        newButton.className = 'btn';
        newButton.textContent = 'Go to Home';

        newButton.addEventListener('click', function() {
            window.location.href = '../html/home_page.html';
        });
        buttonsDiv.appendChild(newButton);

        const menuContent = document.querySelector('.menu-content');
        const logoutLink = document.createElement('a');
        logoutLink.href = '#';
        logoutLink.id = 'logout';
        logoutLink.textContent = 'Logout';
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            document.cookie = 'token=; path=/;';
            window.location.href = 'landing_page.html';
        });

        // Append the logout link to the menu content
        menuContent.appendChild(logoutLink);
    }
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