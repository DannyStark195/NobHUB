from App import create_app, socketio
#Run the flask application
app = create_app()

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app)