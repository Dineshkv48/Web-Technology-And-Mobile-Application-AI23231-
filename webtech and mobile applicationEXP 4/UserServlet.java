import java.io.*;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import jakarta.servlet.annotation.WebServlet;

public class UserServlet extends HttpServlet {

    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
                          throws ServletException, IOException {

        response.setContentType("text/html");
        PrintWriter out = response.getWriter();

        String name = request.getParameter("name");
        String ageStr = request.getParameter("age");

        try {
            int age = Integer.parseInt(ageStr);

            out.println("<html><body>");
            out.println("<h2>Hello, " + name +
                        "! You are " + age + " years old.</h2>");
            out.println("</body></html>");

        } catch (NumberFormatException e) {
            out.println("<html><body>");
            out.println("<h2>Invalid age entered.</h2>");
            out.println("</body></html>");
        }
    }
}