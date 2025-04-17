from app import app
import routes  # noqa: F401
import logging

if __name__ == "__main__":
    # Set up logging for better debugging
    logging.basicConfig(level=logging.DEBUG)
    # Run the application on 0.0.0.0 to make it externally accessible
    app.run(host="0.0.0.0", port=5000, debug=True)
