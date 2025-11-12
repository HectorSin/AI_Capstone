document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorElement = document.getElementById('login-error');
    const successMessage = document.getElementById('success-message');

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('registered')) {
        successMessage.textContent = 'Registration successful! Please log in.';
        successMessage.style.display = 'block';
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorElement.style.display = 'none';

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const formData = new URLSearchParams();
                formData.append('username', email);
                formData.append('password', password);

                const response = await fetch('/auth/login/admin', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Login failed');
                }

                const data = await response.json();
                
                if (data.access_token) {
                    localStorage.setItem('admin_token', data.access_token);
                    window.location.href = 'index.html';
                } else {
                    throw new Error('Access token not found in response');
                }

            } catch (error) {
                errorElement.textContent = error.message;
                errorElement.style.display = 'block';
            }
        });
    }
});
