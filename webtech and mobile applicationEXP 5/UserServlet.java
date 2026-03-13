import java.io.IOException;
import java.io.PrintWriter;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet("/UserServlet")
public class UserServlet extends HttpServlet {

    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        String name = request.getParameter("username");
        String email = request.getParameter("email");

        response.setContentType("text/html");
        PrintWriter out = response.getWriter();

        out.println("<html>");
        out.println("<head><title>GET Result</title></head>");
        out.println("<body style='background:linear-gradient(to right,#56ab2f,#a8e063);"
                + "font-family:Arial;text-align:center;padding-top:80px;'>");

        out.println("<div style='background:white;width:400px;margin:auto;"
                + "padding:30px;border-radius:10px;box-shadow:0 0 15px gray;'>");

        out.println("<h1 style='color:green;'>GET Method Response</h1>");
        out.println("<hr>");
        out.println("<h3>Name: " + name + "</h3>");
        out.println("<h3>Email: " + email + "</h3>");

        out.println("<p style='color:blue;font-weight:bold;'>"
                + "✔ Data is Visible in the URL (Query String)"
                + "</p>");

        out.println("<a href='https://www.geeksforgeeks.org/java/introduction-java-servlets/' "
                + "target='_blank' "
                + "style='display:inline-block;margin:10px;padding:8px 15px;"
                + "background:green;color:white;text-decoration:none;border-radius:5px;'>"
                + "Learn GET Method</a>");

        out.println("<br><br>");

        out.println("<a href='index.html' "
                + "style='padding:6px 12px;background:black;color:white;"
                + "text-decoration:none;border-radius:5px;'>"
                + "Back to Home</a>");

        out.println("</div>");
        out.println("</body></html>");
    }


    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        String name = request.getParameter("username");
        String email = request.getParameter("email");

        response.setContentType("text/html");
        PrintWriter out = response.getWriter();

        out.println("<html>");
        out.println("<head><title>POST Result</title></head>");
        out.println("<body style='background:linear-gradient(to right,#ff416c,#ff4b2b);"
                + "font-family:Arial;text-align:center;padding-top:80px;'>");

        out.println("<div style='background:white;width:400px;margin:auto;"
                + "padding:30px;border-radius:10px;box-shadow:0 0 15px gray;'>");

        out.println("<h1 style='color:red;'>POST Method Response</h1>");
        out.println("<hr>");
        out.println("<h3>Name: " + name + "</h3>");
        out.println("<h3>Email: " + email + "</h3>");


        out.println("<a href='https://www.geeksforgeeks.org/java/introduction-java-servlets/' "
                + "target='_blank' "
                + "style='display:inline-block;margin:10px;padding:8px 15px;"
                + "background:red;color:white;text-decoration:none;border-radius:5px;'>"
                + "Learn POST Method</a>");

        out.println("<br><br>");

        out.println("<a href='index.html' "
                + "style='padding:6px 12px;background:black;color:white;"
                + "text-decoration:none;border-radius:5px;'>"
                + "Back to Home</a>");

        out.println("</div>");
        out.println("</body></html>");
    }
}