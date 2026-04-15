from flask import Flask

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return "Flask server is running!", 200

if __name__ == '__main__':
    print("Starting test server...")
    app.run(host='0.0.0.0', port=5001, debug=True)