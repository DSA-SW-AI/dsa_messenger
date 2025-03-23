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

    // Error Text
    document.getElementById('staffidError').textContent = "";
    document.getElementById('fnameError').textContent = "";
    document.getElementById('lnameError').textContent = "";
    document.getElementById('directorateError').textContent = "";
    document.getElementById('profile_pictureError').textContent = "";
    document.getElementById('passwordError').textContent = "";
    document.getElementById('con_passwordError').textContent = "";

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

            // Create FormData object for file upload
            const formData = new FormData();
            formData.append('staffid', staffid);
            formData.append('fname', fname);
            formData.append('lname', lname);
            formData.append('group_id', directorate);
            formData.append('profile_picture', profile_picture); // File upload
            formData.append('password', password);
            formData.append('con_password', con_password);

            const response = await fetch('/submit_register', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();
            console.log("Server response:", result); // Log response for debugging

            if (result.success) {
                alert('Registration successful!');
                window.location.href = '/login';
            } else {
                alert('Registration failed: ' + result.error);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert('An error occurred while submitting the form.');
        }
    }

});
