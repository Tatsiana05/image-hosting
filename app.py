import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
import uuid

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    encoding="utf-8"
)


class ImageHostingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            with open("static/index.html", "r", encoding="utf-8") as file:
                html = file.read()

            self.wfile.write(html.encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            self.wfile.write(
                "<h1>404 - Page not found</h1>".encode("utf-8")
            )

    def do_POST(self):
        if self.path == "/upload":
            content_type = self.headers.get("Content-Type")

            if not content_type:
                logging.warning("UPLOAD_ERROR: Content-Type header is missing")
                self.send_error(400, "Content-Type header is missing")
                return

            content_length = int(self.headers.get("Content-Length", 0))

            body = self.rfile.read(content_length)

            message = BytesParser(policy=default).parsebytes(
                b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body
            )

            for part in message.iter_parts():
                if part.get_param("name", header="content-disposition") == "image":
                    filename = part.get_filename()

                    if not filename:
                        logging.warning("UPLOAD_ERROR: file was not selected")
                        self.send_error(400, "File was not selected")
                        return

                    extension = Path(filename).suffix.lower()

                    allowed_extensions = {".jpg", ".png", ".gif"}

                    if extension not in allowed_extensions:
                        logging.warning(
                            "UPLOAD_ERROR: unsupported file format %s",
                            extension
                        )
                        self.send_error(400, "Unsupported file format")
                        return

                    file_data = part.get_payload(decode=True)

                    max_size = 5 * 1024 * 1024

                    if len(file_data) > max_size:
                        logging.warning(
                            "UPLOAD_ERROR: file %s is larger than 5 MB",
                            filename
                        )
                        self.send_error(400, "File is larger than 5 MB")
                        return

                    unique_filename = f"{uuid.uuid4().hex}{extension}"

                    image_path = Path("images") / unique_filename
                    image_path.write_bytes(file_data)

                    logging.info(
                        "UPLOAD: image %s saved successfully",
                        unique_filename
                    )

                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "text/html; charset=utf-8"
                    )
                    self.end_headers()

                    image_url = f"http://localhost:8080/images/{unique_filename}"

                    response = (
                        "<h1>Image uploaded successfully</h1>"
                        f"<p>Saved as: {unique_filename}</p>"
                        f'<p>Image URL: <a href="{image_url}">{image_url}</a></p>'
                    )

                    self.wfile.write(response.encode("utf-8"))
                    return

        self.send_response(404)
        self.end_headers()


server = HTTPServer(("localhost", 8000), ImageHostingHandler)

print("Server started at http://localhost:8000")

server.serve_forever()