# Importing essential libraries and modules

from flask import Flask, render_template, request, Markup,redirect
import numpy as np
import pandas as pd
from utils.disease import disease_dic
from utils.fertilizer import fertilizer_dic
import requests
import config
import pickle
import io
import torch
from torchvision import transforms
from PIL import Image
from utils.model import ResNet9
# ==============================================================================================

# -------------------------LOADING THE TRAINED MODELS -----------------------------------------------

# Loading plant disease classification model

leaf_classes = ['Apple',
                   'Apple',
                   'Apple',
                   'Apple',
                   'Blueberry',
                   'Cherry',
                   'Cherry',
                   'Corn',
                   'Corn',
                   'Corn',
                   'Corn',
                   'Grape',
                   'Grape',
                   'Grape',
                   'Grape',
                   'Orange',
                   'Peach',
                   'Peac',
                   'Pepper,',
                   'Pepper,_',
                   'Potato',
                   'Potato',
                   'Potato',
                   'Raspberry',
                   'Soybean',
                   'Squash',
                   'Strawberry',
                   'Strawberry',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato',
                   'Tomato']

leaf_model_path = 'models/plant_disease_model.pth'
leaf_model = ResNet9(3, len(leaf_classes))
leaf_model.load_state_dict(torch.load(
    leaf_model_path, map_location=torch.device('cpu')))
leaf_model.eval()


# Loading crop recommendation model

crop_recommendation_model_path = 'models/RandomForest.pkl'
crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))


# =========================================================================================

# Custom functions for calculations


def weather_fetch(city_name):
    """
    Fetch and returns the temperature and humidity of a city
    :params: city_name
    :return: temperature, humidity
    """
    api_key = config.weather_api_key
    base_url = "http://api.openweathermap.org/data/2.5/weather?"

    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    response = requests.get(complete_url)
    x = response.json()

    if x["cod"] != "404":
        y = x["main"]

        temperature = round((y["temp"] - 273.15), 2)
        humidity = y["humidity"]
        return temperature, humidity
    else:
        return None


def predict_image(img, model=leaf_model):
    """
    Transforms image to tensor and predicts disease label
    :params: image
    :return: prediction (string)
    """
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.ToTensor(),
    ])
    image = Image.open(io.BytesIO(img))
    img_t = transform(image)
    img_u = torch.unsqueeze(img_t, 0)

    # Get predictions from model
    yb = model(img_u)
    # Pick index with highest probability
    _, preds = torch.max(yb, dim=1)
    prediction = leaf_classes[preds[0].item()]
    # Retrieve the class label
    return prediction

# ===============================================================================================
# ------------------------------------ FLASK APP -------------------------------------------------


app = Flask(__name__)

# render home page


@ app.route('/')
def home():
    title = 'leaf - Home'
    return render_template('index.html', title=title)

# render crop recommendation form page
@ app.route('/about')
def about():
    title = 'leaf - about'
    return render_template('about.html', title=title)

@ app.route('/contact')
def contact():
    title = 'leaf - contact'
    return render_template('contact.html', title=title)

@ app.route('/crop-recommend')
def crop_recommend():
    title = 'leaf - Crop Recommendation'
    return render_template('crop.html', title=title)

# render fertilizer recommendation form page


@ app.route('/fertilizer')
def fertilizer_recommendation():
    title = 'leaf - Fertilizer Suggestion'

    return render_template('fertilizer.html', title=title)

# render disease prediction input page




# ===============================================================================================

# RENDER PREDICTION PAGES

# render crop recommendation result page


@ app.route('/crop-predict', methods=['POST'])
def crop_prediction():
    title = 'leaf - Crop Recommendation'

    if request.method == 'POST':
        N = int(request.form['nitrogen'])
        P = int(request.form['phosphorous'])
        K = int(request.form['pottasium'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        # state = request.form.get("stt")
        city = request.form.get("city")

        if weather_fetch(city) != None:
            temperature, humidity = weather_fetch(city)
            data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
            my_prediction = crop_recommendation_model.predict(data)
            final_prediction = my_prediction[0]

            return render_template('crop-result.html', prediction=final_prediction, title=title)

        else:

            return render_template('try_again.html', title=title)

# render fertilizer recommendation result page


@ app.route('/fertilizer-predict', methods=['POST'])
def fert_recommend():
    title = 'leaf - Fertilizer Suggestion'

    crop_name = str(request.form['cropname'])
    N = int(request.form['nitrogen'])
    P = int(request.form['phosphorous'])
    K = int(request.form['pottasium'])
    # ph = float(request.form['ph'])

    df = pd.read_csv('Data/fertilizer.csv')

    nr = df[df['Crop'] == crop_name]['N'].iloc[0]
    pr = df[df['Crop'] == crop_name]['P'].iloc[0]
    kr = df[df['Crop'] == crop_name]['K'].iloc[0]

    n = nr - N
    p = pr - P
    k = kr - K
    temp = {abs(n): "N", abs(p): "P", abs(k): "K"}
    max_value = temp[max(temp.keys())]
    if max_value == "N":
        if n < 0:
            key = 'NHigh'
        else:
            key = "Nlow"
    elif max_value == "P":
        if p < 0:
            key = 'PHigh'
        else:
            key = "Plow"
    else:
        if k < 0:
            key = 'KHigh'
        else:
            key = "Klow"

    response = Markup(str(fertilizer_dic[key]))

    return render_template('fertilizer-result.html', recommendation=response, title=title)

# render disease prediction result page


@app.route('/leaf-predict', methods=['GET', 'POST'])
def disease_prediction():
    title = 'leaf - disease Detection'

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files.get('file')
        if not file:
            return render_template('disease.html', title=title)
        try:
            img = file.read()

            prediction = predict_image(img)
          
            prediction = Markup(str(disease_dic[prediction]))
            return render_template('disease-result.html', prediction=prediction, title=title)
        except:
            pass
    return render_template('disease.html', title=title)


# ===============================================================================================
if __name__ == '__main__':
    app.run(debug=False)
