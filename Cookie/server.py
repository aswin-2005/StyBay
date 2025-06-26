from flask import Flask, request, jsonify
import subprocess

# try:
#     subprocess.run(["playwright", "install"], check=True)
#     print("✅ Playwright browsers are installed.")
# except subprocess.CalledProcessError as e:
#     print(f"❌ Failed to install Playwright browsers: {e}")

from harvester import create_cookies
from database import acquire_cookie
from database import refresh_cookies
from database import release_cookie
from database import add_cookie

app = Flask(__name__)





@app.route('/api/cookies', methods=['POST'])
def acquire_cookie_route():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    data = request.get_json()
    site = data.get('site') if data else None
    if not site:
        return jsonify({'error': 'Missing "site" parameter'}), 400

    session = acquire_cookie(site)
    
    if session is None:
        session = create_cookies(site)
        response = add_cookie(session, site)
        if session is None:
            return jsonify({'error': 'Could not create cookie'}), 500

    return jsonify({
        'message': 'Request successful',
        'session': session
    }), 200




@app.route('/api/cookies/<session_id>', methods=['DELETE'])
def release_cookie_route(session_id):
    if not session_id:
        return jsonify({'error': 'Missing "session_id" parameter'}), 400
    is_valid = request.args.get('valid')
    response = release_cookie(session_id, is_valid)
    if not response or len(response.data) == 0:
        return jsonify({'error': 'session inexistent'}), 404
    return jsonify({'message': 'Request successful, session released'}), 200



@app.route('/api/cookies/refresh', methods=['POST'])
def refresh_cookie_route():
    try:
        response = refresh_cookies()
        return jsonify({
            'message': 'Request successful, session refreshed',
            'response': response
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to refresh cookies', 'details': str(e)}), 500



@app.route('/api/ping', methods=['GET'])
def ping_check():
    return jsonify({'status': 'ok'}), 200




if __name__ == '__main__':
    app.run(debug=True, port=5050)
