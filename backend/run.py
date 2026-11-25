import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables from .env file if present
load_dotenv()

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")
    app.run(host=host, port=port, debug=debug)
