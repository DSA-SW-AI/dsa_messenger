// User Signup validation

const formRegister = document.getElementById('signupForm');

formRegister.addEventListener('submit', async function (e) {
    e.preventDefault(); // Prevent regular form submission

    const staffid = document.getElementById('staffid').value;
    const fname = document.getElementById('fname').value;
    const lname = document.getElementById('lname').value;
    const directorate = document.getElementById('group_id').value;
    const profile_picture = document.getElementById('profile_picture').files[0];
    const password = document.getElementById('password').value;
    const con_password = document.getElementById('con_password').value;
    const security_question = document.getElementById('security_question').value;
    const security_answer = document.getElementById('security_answer').value;

    // Error Text
    document.getElementById('staffidError').textContent = "";
    document.getElementById('fnameError').textContent = "";
    document.getElementById('lnameError').textContent = "";
    document.getElementById('directorateError').textContent = "";
    document.getElementById('profile_pictureError').textContent = "";
    document.getElementById('passwordError').textContent = "";
    document.getElementById('con_passwordError').textContent = "";
    document.getElementById('security_questionError').textContent = "";
    document.getElementById('security_answerError').textContent = "";

    let hasError = false;

    if (!staffid) {
        document.getElementById('staffidError').textContent = 'Staff ID cannot be empty';
        hasError = true;
    }
    if (!fname) {
        document.getElementById('fnameError').textContent = 'Firstname cannot be empty';
        hasError = true;
    }
    if (!lname) {
        document.getElementById('lnameError').textContent = 'Lastname cannot be empty';
        hasError = true;
    }
    if (!directorate) {
        document.getElementById('directorateError').textContent = 'Directorate cannot be empty';
        hasError = true;
    }
    if (!security_question) {
        document.getElementById('security_questionError').textContent = 'Choose your security question';
        hasError = true;
    }
    if (!security_answer) {
        document.getElementById('security_answerError').textContent = 'Security Answer cannot be empty';
        hasError = true;
    }
    if (!profile_picture) {
        document.getElementById('profile_pictureError').textContent = 'Profile Picture cannot be empty';
        hasError = true;
    } else {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!allowedTypes.includes(profile_picture.type)) {
            document.getElementById('profile_pictureError').textContent = 'Only JPG, PNG images are allowed';
            hasError = true;
        }

        // Validate file size (e.g., max 5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (profile_picture.size > maxSize) {
            document.getElementById('profile_pictureError').textContent = 'File size must be less than 5MB';
            hasError = true;
        }
    }

    if (!password) {
        document.getElementById('passwordError').textContent = 'Password cannot be empty';
        hasError = true;
    }
    if (password !== con_password) {
        document.getElementById('con_passwordError').textContent = 'Password not matched';
        hasError = true;
    }


    if (!hasError) {
        try {
            const formData = new FormData();
            formData.append('staffid', staffid);
            formData.append('fname', fname);
            formData.append('lname', lname);
            formData.append('group_id', directorate);
            formData.append('profile_picture', profile_picture); // File upload
            formData.append('password', password);
            formData.append('con_password', con_password);
            formData.append('security_question', security_question);
            formData.append('security_answer', security_answer);

            const response = await fetch('/submit_register', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();
            console.log("Server response:", result);

            // Display flash message
            if (result.success) {
                showFlashMessage(result.message, 'success');
                // Redirect to login after successful registration
                setTimeout(() => {
                    window.location.href = '/login'; // Redirect after 5 seconds (adjust if needed)
                }, 5000); // Wait for 5 seconds before redirecting
            } else {
                showFlashMessage(result.message, 'error');
            }

        } catch (error) {
            console.error('Fetch error:', error);
            showFlashMessage('An error occurred while submitting the form.', 'error');
        }
    }

    // Function to show flash message
    function showFlashMessage(message, type) {
        const flashContainer = document.getElementById('flash-messages');

        // Create the flash message element
        const flashMessage = document.createElement('div');
        flashMessage.classList.add('flash', type);
        flashMessage.textContent = message;

        // Append it to the container
        flashContainer.appendChild(flashMessage);

        // Fade out and remove the flash message after 5 seconds
        setTimeout(() => {
            flashMessage.style.opacity = '0';
            setTimeout(() => flashMessage.remove(), 500);
        }, 5000);
    }


});
