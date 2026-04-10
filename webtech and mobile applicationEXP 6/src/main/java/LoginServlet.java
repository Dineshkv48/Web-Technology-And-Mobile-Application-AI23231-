import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.*;

@WebServlet("/LoginServlet")
public class LoginServlet extends HttpServlet {

protected void doPost(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException {

    String username = request.getParameter("username").trim();
    String password = request.getParameter("password").trim();

    if(username.equals("admin") && password.equals("1234"))
    {
        HttpSession session = request.getSession();

        session.setAttribute("username", username);

        session.setMaxInactiveInterval(300);

        response.sendRedirect("dashboard.jsp");
    }

    else
    {
        response.setContentType("text/html");

        PrintWriter out = response.getWriter();

        out.println("<html>");
        out.println("<head>");
        out.println("<title>Login Failed</title>");

        out.println("<style>");
        out.println("body{font-family:Arial;background:#f2f2f2;text-align:center;padding-top:150px;}");
        out.println(".box{background:white;padding:40px;width:350px;margin:auto;border-radius:10px;box-shadow:0 5px 20px rgba(0,0,0,0.2);}");
        out.println("h3{color:red;}");
        out.println("a{display:inline-block;margin-top:20px;padding:10px 20px;background:#4facfe;color:white;text-decoration:none;border-radius:5px;}");
        out.println("</style>");

        out.println("</head>");
        out.println("<body>");

        out.println("<div class='box'>");
        out.println("<h3>Invalid Username or Password</h3>");
        out.println("<a href='login.html'>Try Again</a>");
        out.println("</div>");

        out.println("</body>");
        out.println("</html>");
    }

}
}