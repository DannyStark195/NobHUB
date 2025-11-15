import eventlet
eventlet.monkey_patch()  # MUST run before other imports
import os

from App import create_app, socketio
#Run the flask application
app = create_app()

if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app,  host='0.0.0.0', port=port)