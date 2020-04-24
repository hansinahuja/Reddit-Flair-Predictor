# Reddit-Flair-Predictor

Creating a web app using Flask to predict flairs of Reddit posts from r/india. The progress has been described in 5 phases which have been detailed below. You can find the app hosted on Heroku [here.](https://flairpredict.herokuapp.com/)

## How to run

### How to use the API
There exists an endpoint for automated testing. You can send an automated POST request with a .txt file which contains a link of a r/india post in every line. Response of the request will be a json file in which key is the link to the post and value should be predicted flair.

```python
import requests 
import json

# Making the post request
url = "https://flairpredict.herokuapp.com/automated_testing"
files = {'upload_file': open('test.txt', 'rb')}
r = requests.post(url, files=files)

# The request library returns a Response object. You'll need to get the json file with this command
r = r.json()

# Save to a json file
with open('predictions.json', 'w') as f:
    json.dump(r, f, indent=4)
```

### How to use the web app
Using the web application is pretty straightforward. Visit [this link](https://flairpredict.herokuapp.com/) and enter the URL of a Reddit post from r/india, and click on 'Predict'. You'll be redirected to the prediction page, from which you can move back to the homepage.

<img src = "images/homescreen.png" width ="45%" /> <img src = "images/predicted.png" width ="45%" />

### How to locally host the app
Move into the `app` directory and run:
```
pip install -r requirements.txt
python main.py
```
The app will be hosted on the address that shows up on your command prompt.

## The five phases
