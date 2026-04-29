from app import create_app

app = create_app()

if __name__ == "__main__":
    # VULN: Binding to all interfaces with debug mode
    app.run(host="0.0.0.0", port=5000, debug=True)
