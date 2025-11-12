document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const errorElement = document.getElementById('register-error');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorElement.style.display = 'none';
            errorElement.textContent = '';

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const passwordConfirm = document.getElementById('password-confirm').value;

            if (password !== passwordConfirm) {
                errorElement.textContent = 'Passwords do not match.';
                errorElement.style.display = 'block';
                return;
            }

            try {
                const response = await fetch('/auth/register/admin', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Registration failed');
                }

                // On success, redirect to login page with a success message
                window.location.href = 'login.html?registered=true';

            } catch (error) {
                errorElement.textContent = error.message;
                errorElement.style.display = 'block';
            }
        });
    }
});
