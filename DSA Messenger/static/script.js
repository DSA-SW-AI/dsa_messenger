// User Signup validation

const formRegister = document.getElementById('signupForm');

formRegister.addEventListener('submit', async function (e) {
    e.preventDefault(); // Prevent regular form submission

    const staffid = document.getElementById('staffid').value;
    const fname = document.getElementById('fname').value;
    const lname = document.getElementById('lname').value;
    const directorate = document.getElementById('directorate').value;
    const password = document.getElementById('password').value;
    const con_password = document.getElementById('con_password').value;

    // Error Text
    document.getElementById('staffidError').textContent = "";
    document.getElementById('fnameError').textContent = "";
    document.getElementById('lnameError').textContent = "";
    document.getElementById('directorateError').textContent = "";
    document.getElementById('passwordError').textContent = "";
    document.getElementById('con_passwordError').textContent = "";

    let hasError = false;

    if (staffid === '') {
        document.getElementById('staffidError').textContent = 'Staff ID cannot be empty';
        hasError = true;
    } else if (fname === '') {
        document.getElementById('fnameError').textContent = 'Firstname cannot be empty';
        hasError = true;
    } else if (lname === '') {
        document.getElementById('lnameError').textContent = 'Lastname cannot be empty';
        hasError = true;
    } else if (directorate === '') {
        document.getElementById('directorateError').textContent = 'Directorate cannot be empty';
        hasError = true;
    } else if (password === '') {
        document.getElementById('passwordError').textContent = 'Password cannot be empty';
        hasError = true;
    } else if (password !== con_password) {
        document.getElementById('con_passwordError').textContent = 'Password not matched';
        hasError = true;
    }


    if (!hasError) {
        try {
            const response = await fetch('/submit_register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ staffid, fname, lname, directorate, password, con_password })
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
    

    // if (!hasError) {
    //     try {
    //         const response = await fetch('/submit_register', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json' // Set content type as JSON
    //             },
    //             body: JSON.stringify({
    //                 staffid,
    //                 fname,
    //                 lname,
    //                 directorate,
    //                 password,
    //                 con_password
    //             })
    //         });

    //         const result = await response.json();
    //         if (result.success) {
    //             alert('Registration successful!');
    //             window.location.href = '/login'; // Redirect to login page
    //         } else {
    //             alert('Registration failed: ' + result.error);
    //         }
    //     } catch (error) {
    //         console.error('Error:', error);
    //         alert('An error occurred while submitting the form.');
    //     }
    // }
});
