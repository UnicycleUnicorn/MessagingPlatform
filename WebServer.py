import eel

# Initialize Eel with your HTML file
eel.init('web')


# Define a Python function to be called from JavaScript
@eel.expose
def hello_world():
    print('Hello, world!')


# Start the Eel application
eel.start('index.html')
