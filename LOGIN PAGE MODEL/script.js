function submitForm() {
    let name = document.getElementById("name").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let dob = document.getElementById("dob").value;
    let mobile = document.getElementById("mobile").value;

    // Validation
    if (name === "" || email === "" || password === "" || dob === "" || mobile === "") {
        alert("Please fill all the fields");
        return false;
    }

    alert("Form submitted successfully");


    window.location.href = "https://www.tutorialspoint.com/html/index.htm";

    return false;
}