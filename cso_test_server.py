import bottle
import waitress

app = bottle.app()

@app.route('/', 'GET')
def get_file():
    return bottle.static_file('cso_test_data.csv', root='.')

waitress.serve(app, host='0.0.0.0', port=8080)
