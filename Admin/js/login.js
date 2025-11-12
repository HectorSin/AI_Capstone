document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorElement = document.getElementById('login-error');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorElement.style.display = 'none';

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/auth/login/local', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
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
