<%
String user = (String)session.getAttribute("username");

if(user == null)
{
    response.sendRedirect("login.html");
}
%>

<html>
<head>
<title>Dashboard</title>

<style>

body{
    margin:0;
    font-family:Arial;
    background:#f5f5f5;
}

.header{
    background:#4facfe;
    color:white;
    padding:20px;
    text-align:center;
}

.container{
    text-align:center;
    margin-top:50px;
}

.logout{
    padding:12px 25px;
    background:red;
    color:white;
    text-decoration:none;
    border-radius:5px;
}

.logout:hover{
    background:darkred;
}

img{
    margin-top:20px;
    border-radius:10px;
}

iframe{
    margin-top:30px;
    border-radius:10px;
}

</style>

</head>

<body>

<div class="header">
<h2>Welcome <%= user %></h2>
</div>

<div class="container">

<h3>You have successfully logged in</h3>

<!-- IMAGE -->
<img src="images/admin.jpg" width="300">

<br><br>

<!-- IFRAME -->
<iframe src="https://www.wikipedia.org" width="600" height="300"></iframe>

<br><br>

<a class="logout" href="LogoutServlet">Logout</a>

</div>

</body>
</html>