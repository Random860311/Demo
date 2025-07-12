import servomotor
from web import app


if __name__ == '__main__':
    cert_path = "web/certs/cert.pem"
    key_path = "web/certs/key.pem"
    app.app.run(
        host="0.0.0.0",
        port=8443, #8000
        ssl_context=(cert_path, key_path),
        debug=True
    )