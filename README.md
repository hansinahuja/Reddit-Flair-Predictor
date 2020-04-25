# Reddit-Flair-Predictor

Creating a web app using Flask to predict flairs of Reddit posts from r/india. The progress has been described in 5 phases which have been detailed below. You can find the app hosted on Heroku [here.](https://flairpredict.herokuapp.com/)

## How to run

### How to use the API
There exists an endpoint for automated testing. You can send an automated POST request with a .txt file which contains a link of a r/india post in every line. Response of the request will be a json file in which key is the link to the post and value should be predicted flair.

**NOTE:** Heroku throws a timeout error for long POST requests, so the API can only handle a limited number of queries in one request. To handle larger queries, see the second code snippet below.

```python
import requests 
import json

# Making the POST request
url = "https://flairpredict.herokuapp.com/automated_testing"
files = {'upload_file': open('test.txt', 'rb')}
r = requests.post(url, files=files)

# The request library returns a Response object. You'll need to get the json file with this command
r = r.json()

# Save to a json file
with open('predictions.json', 'w') as f:
    json.dump(r, f, indent=4)
```

To handle larger queries, you can divide your queries up and send multiple POST requests. The following function can help you do it:

```python
import time
import json
import requests
import os

def use_api(test_file):
  f = open(test_file, "r")
  url = "https://flairpredict.herokuapp.com/automated_testing"
  count = 0
  tot_count = 0
  r = {}
  for line in f:
    line = line.strip()
    if line == "":
      continue
    if count==0:
      f1 = open('test_temp.txt', 'w')
      time.sleep(3.5)
    f1.write(line + "\n")
    count += 1
    tot_count += 1
    if count==150:
      f1.close()
      count = 0
      files = {'upload_file': open('test_temp.txt', 'rb')}
      r1 = requests.post(url, files=files)
      r1 = r1.json()
      r.update(r1)
      print('Queries handled = ', tot_count)
  f.close()
  if count>0:
    f1.close()
    files = {'upload_file': open('test_temp.txt', 'rb')}
    r1 = requests.post(url, files=files).json()
    r.update(r1)
  os.remove("test_temp.txt")
  return r
  
r = use_api('test.txt')
```

### How to locally host the app
Move into the `app` directory and run:
```
pip install -r requirements.txt
python main.py
```
The app will be hosted on the address that shows up on your command prompt.

## The five phases

### Part 1 - Data collection
We use the Praw API to fetch data from Reddit. One of the problems with the Praw API is that it only lets you access 1000 posts per request. To overcome this limitation, after every 1000 posts that we collect, we'll note the time stamp of the last post collected, and then collect the 1000 posts preceding that time, and so on. Install the required libraries and use `notebooks/Part1-Data-Collection.ipynb` to reproduce the results.

### Part 2 - Exploratory data analysis
Standard data analysis, where we plot various stats related to the data, and check for correlations between different words and flairs. Install the required libraries and use `notebooks/Part2-EDA.ipynb` to reproduce the results.

### Part 3 - Building a flair detector
We test the following models:
| Model       | Validation accuracy            |
| ---                | ---             |
| RandomForestClassifier             | 50.51%             |
| LinearSVC           | 52.10%            |
| MultinomialNB        | 51.35%             |
| LogisticRegression    | 52.88%             |
| SGDClassifier       | 52.26%             |
| XGBoost       | 48.72%             |
| ULMFit with AWD-LSTM       | 56.01%             |
| Attention with BiLSTM       | 55.70%             |

For deployment, the achitecture selected was Attention with BiLSTM, because Heroku's 500MB slug size was too small to deploy the AWD-LSTM architecture.

To reproduce the results, install the required libraries and run:
- `notebooks/Part3a-Building-a-Flair-Detector.ipynb`
- `notebooks/Part3b-Building-a-Flair-Detector.ipynb`
- `notebooks/Part3ac-Building-a-Flair-Detector.ipynb`

### Part 4 - Building a web application
We use Flask to create a simple web application with 3 endpoints:
- `/`: landing page
- `/predicted`: prediction page
- `/automated_testing`: to handle POST requests for API calls. Usage has been descibed above
A couple of screenshots from the app:

 Landing page                         |                      Prediction page    |
:-------------------------:|:-------------------------:|
![](images/homescreen.png?raw=True) |![](images/predicted.png?raw=true) |

### Part 5 - Deployment
The app has been deployed on Heroku [here.](https://flairpredict.herokuapp.com/) It might take a while to respond due to the large slug size of the app (498MB). Using the application is pretty straightforward. Visit [this link,](https://flairpredict.herokuapp.com/) enter the URL of a Reddit post from r/india, and click on 'Predict'. You'll be redirected to the prediction page, from which you can move back to the homepage.
