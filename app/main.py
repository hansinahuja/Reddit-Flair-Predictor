import flask
import praw
import numpy as np
import pickle
import json
import tensorflow as tf
from tensorflow.python.keras.backend import set_session
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras import backend as K
from tensorflow.keras import initializers, regularizers, constraints

from tensorflow.keras.layers import Layer, Dense, Input, LSTM, Bidirectional
from tensorflow.keras.layers import Dropout, Embedding
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.models import Model

class Attention(Layer):
    def __init__(self, step_dim,
                 W_regularizer=None, b_regularizer=None,
                 W_constraint=None, b_constraint=None,
                 bias=True, **kwargs):
        self.supports_masking = True
        self.init = initializers.get('glorot_uniform')
        self.W_regularizer = regularizers.get(W_regularizer)
        self.b_regularizer = regularizers.get(b_regularizer)
        self.W_constraint = constraints.get(W_constraint)
        self.b_constraint = constraints.get(b_constraint)
        self.bias = bias
        self.step_dim = step_dim
        self.features_dim = 0
        super(Attention, self).__init__(**kwargs)

    def build(self, input_shape):
        assert len(input_shape) == 3
        self.W = self.add_weight(shape=(input_shape[-1],),
                                 initializer=self.init,
                                 name='{}_W'.format(self.name),
                                 regularizer=self.W_regularizer,
                                 constraint=self.W_constraint)
        self.features_dim = input_shape[-1]
        if self.bias:
            self.b = self.add_weight(shape=(input_shape[1],),
                                     initializer='zero',
                                     name='{}_b'.format(self.name),
                                     regularizer=self.b_regularizer,
                                     constraint=self.b_constraint)
        else:
            self.b = None
        self.built = True

    def compute_mask(self, input, input_mask=None):
        return None

    def call(self, x, mask=None):
        features_dim = self.features_dim
        step_dim = self.step_dim
        eij = K.reshape(K.dot(K.reshape(x, (-1, features_dim)), K.reshape(self.W, (features_dim, 1))), (-1, step_dim))
        if self.bias:
            eij += self.b
        eij = K.tanh(eij)
        a = K.exp(eij)
        if mask is not None:
            a *= K.cast(mask, K.floatx())
        a /= K.cast(K.sum(a, axis=1, keepdims=True) + K.epsilon(), K.floatx())
        a = K.expand_dims(a)
        weighted_input = x * a
        return K.sum(weighted_input, axis=1)

    def compute_output_shape(self, input_shape):
        return input_shape[0],  self.features_dim

def build(maxlen, len_word_index):
    inputs = Input(shape=(50,), dtype='int32')
    embedding_layer = Embedding(len_word_index+1, 100, input_length=maxlen, trainable=False)
    x = embedding_layer(inputs)
    x = Bidirectional(LSTM(512, dropout=0.3, recurrent_dropout=0.3, return_sequences=True))(x)
    x = Dropout(0.3)(x)
    x = Attention(50)(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = BatchNormalization()(x)
    outputs = Dense(14, activation='softmax')(x)
    
    model = Model(inputs, outputs)
    return model

# Enter Reddit credentials here
client_id = ###
client_secret = ###
user_agent = ###
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent=user_agent)

sess = tf.Session()
graph = tf.get_default_graph()
set_session(sess)
model = build(50, 33001)
model.load_weights('models/model_weights.hdf5')
pickle_in = open("models/tokenizer.pickle","rb")
tokenizer = pickle.load(pickle_in)
app = flask.Flask(__name__, template_folder='templates')


def make_pred(titles, urls):
    global model
    global graph
    global sess
    key_to_flair = {0: 'AskIndia',
                    1: 'Business/Finance',
                    2: 'CAA-NRC',
                    3: 'Coronavirus',
                    4: 'Demonetization',
                    5: 'Food',
                    6: 'Non-Political',
                    7: 'Photography',
                    8: 'Policy/Economy',
                    9: 'Politics',
                    10: 'Scheduled',
                    11: 'Science/Technology',
                    12: 'Sports',
                    13: '[R]eddiquette'}
    pred_dict = {}
    X = tokenizer.texts_to_sequences(titles)
    maxlen = 50
    X = list(sequence.pad_sequences(X, maxlen=maxlen))
    X = np.array(X)
    with graph.as_default():
        set_session(sess)
        predictions = model.predict(X, verbose=1)
    predictions = np.argmax(predictions, axis=-1)
    for i in range(predictions.shape[0]):
        url = urls[i]
        pred_dict[url] = key_to_flair[predictions[i]]
    return pred_dict

@app.route('/', methods=['GET', 'POST'])
def main():
    if flask.request.method == 'GET':
        return(flask.render_template('main.html'))

    if flask.request.method == 'POST':
        try:
            url = flask.request.form['url']
            submission = reddit.submission(url=url)
            title = submission.title
            flair = submission.link_flair_text
            if flair==None:
                flair = "Untagged"
            titles = [title]
            urls = [url]
            prediction = make_pred(titles, urls)
            prediction = prediction[url]
            return flask.render_template('predicted.html',
                                        result="Success!",
                                        title="Title: "+title,
                                        prediction="Precicted flair: "+prediction,
                                        flair="Actual flair: "+flair
                                        )
        except:
            return flask.render_template('predicted.html',
                                        result="Oops!",
                                        title="It seems that an error has occurred",
                                        prediction="You might've entered an invalid URL",
                                        flair="Why don't we try again?"
                                        )

@app.route('/automated_testing', methods=['POST'])
def testing():
    file = flask.request.files['upload_file'] 
    file = file.read()
    file = file.decode('utf-8')
    file = file.splitlines()
    titles = []
    urls = []
    errors = {}
    count = 1
    for url in file: 
        try:
            title = reddit.submission(url=url).title
            titles.append(title)
            urls.append(url)
        except:
            errors[url] = "error!"
            print("There was an error in parsing query on line", count, sep = ' ')
            print("Please check that the URL is valid, and that the post has a title.")
        count += 1
    predictions = make_pred(titles, urls)
    predictions.update(errors)
    predictions = flask.jsonify(predictions)
    return predictions

if __name__ == '__main__':
    app.run()