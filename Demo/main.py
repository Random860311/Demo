import eventlet
eventlet.monkey_patch()

from web import app as web_app
import ssl




if __name__ == '__main__':
    cert_path = "web/certs/cert.pem"
    key_path = "web/certs/key.pem"

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)

    web_app.db_config.initialize()

    print("SocketIO async_mode:", web_app.socketio.async_mode)
    web_app.socketio.run(
        web_app.app,
        host="0.0.0.0",
        port=8443,
        # certfile=cert_path,
        # keyfile=key_path,
        # ssl_context=(cert_path, key_path),
        debug=True
    )

    # app.app.run(
    #     host="0.0.0.0",
    #     port=8443, #8000
    #     ssl_context=(cert_path, key_path),
    #     debug=True
    # )