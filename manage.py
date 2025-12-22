from app import create_app
from app.config import Config
from app.resources import initLogger

initLogger()

app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.FLASK_DEBBUG, host="0.0.0.0", port=int(Config.PORT))
    # app.run(host="0.0.0.0", port=8080)
