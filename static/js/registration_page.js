async function sendRegistrationRequest(username, password) {
    const registrationRequest = {
        username: username,
        password: password
    };

    try {
        const response = await fetch('http://192.168.178.30:8000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(registrationRequest)
        });
    
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
    
        const data = await response.json();
        console.log('Response:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const registrationButton = document.getElementById('registration-button');
    registrationButton.addEventListener('click', async function (event) {
        event.preventDefault(); // Prevent default form submission
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (password !== confirmPassword) {
            window.alert('Passwords do not match. Please try again.');
            return;
        }

        await sendRegistrationRequest(username, password);
    });
});
