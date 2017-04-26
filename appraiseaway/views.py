from django.http import HttpResponse
from django.http import JsonResponse
import os
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
import pickle
import xmltodict
import requests
import urllib2
import urllib
import json
import numpy as np


def getWalkScore(zipcode):
    lat_jsonResponse = json.loads(urllib2.urlopen("https://www.zipcodeapi.com/rest/Jd53ArqkcWlc2CneAby3N2ccktlgYSUH60KHrb2D8oPa0dpAoXEc0QolkJCiCx0I/info.json/" + str(zipcode)).read())
    latitude = lat_jsonResponse["lat"]
    longitude = lat_jsonResponse["lng"]
    google_url = "https://maps.googleapis.com/maps/api/geocode/json?latlng="
    google_url += str(latitude) + ","
    google_url += str(longitude) + "&key=AIzaSyBSSaldlnTvJZ8KbFGPpIv_HI_Anqhokcg"
    addr_jsonResponse = json.loads(urllib2.urlopen(google_url).read())
    address = urllib.quote_plus(addr_jsonResponse["results"][0]["formatted_address"])
    walkscore_url = "http://api.walkscore.com/score?format=json"
    walkscore_url += "&address=" + str(address)
    walkscore_url += "&lat=" + str(latitude)
    walkscore_url += "&lon=" + str(longitude) + "&wsapikey=fcb3fbfd5010056cc4392c2e0aa8104c"
    walk_jsonResponse = json.loads(urllib2.urlopen(walkscore_url).read())
    walk_score = walk_jsonResponse["walkscore"]
    return walk_score


def getWalkScoreAPI(request):
    zipcode = request.GET.get('zipcode')
    return JsonResponse({"walk_score" : getWalkScore(zipcode)})


def getZillowData(request):
    zpid = request.GET.get('zpid')
    zillowUrl = "http://www.zillow.com/webservice/GetUpdatedPropertyDetails.htm?zws-id=X1-ZWz199vdd0qvbf_77v70&zpid="
    zillowUrl = zillowUrl + zpid
    r = requests.get(zillowUrl)
    xmlString = r.text
    dictResponse = xmltodict.parse(xmlString)
    image_url = ""
    if "UpdatedPropertyDetails:updatedPropertyDetails" in dictResponse \
        and "response" in dictResponse["UpdatedPropertyDetails:updatedPropertyDetails"] \
        and "images" in dictResponse["UpdatedPropertyDetails:updatedPropertyDetails"]["response"] \
        and "image" in dictResponse["UpdatedPropertyDetails:updatedPropertyDetails"]["response"]["images"] \
        and "url" in dictResponse["UpdatedPropertyDetails:updatedPropertyDetails"]["response"]["images"]["image"]:
        image_url = str(dictResponse["UpdatedPropertyDetails:updatedPropertyDetails"]["response"]["images"]["image"]["url"])
        if "[u'" in image_url:
            image_url = image_url.split("[u'")[1].split("',")[0]
    jsonResponse = {}
    jsonResponse["image_url"] = image_url
    jsonResponse["zpid"] = zpid
    return JsonResponse(jsonResponse)


def trainKNN(attributes, target, MODEL_DIR):
    for k in range(1, 11):
        neigh = KNeighborsRegressor(n_neighbors=k)
        neigh = neigh.fit(attributes, target)
        propertiesPath = os.path.join(MODEL_DIR + "/knn_model_" + str(k) + ".p")
        pickle.dump(neigh, open(propertiesPath, "wb"), protocol=2)


def trainRandomForrest(attributes, target, MODEL_DIR):
    regressor = RandomForestRegressor(n_estimators=25, criterion='mse', max_depth=None, min_samples_split=2,
                                      min_samples_leaf=1,
                                      min_weight_fraction_leaf=0.0, max_features='auto', max_leaf_nodes=None,
                                      min_impurity_split=1e-07,
                                      bootstrap=True, oob_score=True, n_jobs=1, random_state=None, verbose=0,
                                      warm_start=False)
    regressor = regressor.fit(attributes, target)
    rfModelPath = os.path.join(MODEL_DIR + "/randomForrest.p")
    pickle.dump(regressor, open(rfModelPath, "wb"), protocol=2)


def trainData(request):
    if os.getenv("OPENSHIFT_DATA_DIR") != None:
        OPENSHIFT_DATA_DIR = os.getenv("OPENSHIFT_DATA_DIR")
    else:
        PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
        OPENSHIFT_DATA_DIR = os.path.join(PROJECT_PATH, "data")

    MODEL_DIR = os.path.join(OPENSHIFT_DATA_DIR, "appraiseaway_data/model_instances")
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    propertiesPath = os.path.join(OPENSHIFT_DATA_DIR, "appraiseaway_data/house_properties.csv")
    data = pd.read_csv(propertiesPath)
    data['zip_new'] = data['zipcode'].astype('category')
    attributes = data[['zip_new', 'home_size', 'year_built', 'bedrooms', 'bathrooms','walkscore']]
    target = data['price_last_sold']

    trainKNN(attributes, target, MODEL_DIR)
    trainRandomForrest(attributes, target, MODEL_DIR)

    return HttpResponse("Trained and saved both K-NN and Random Forrest models! <br><br>Used file: " + str(propertiesPath))


def getPriceUsingRF(attributes, MODEL_DIR):
    rfModelPath = os.path.join(MODEL_DIR + "/randomForrest.p")
    regressor = pickle.load(open(rfModelPath, "rb"))
    prediction = regressor.predict(attributes)[0]
    return prediction


def getNeighborsUsingKNN(attributes, k_val, MODEL_DIR):
    neighs = []
    for k in range(1, 11):
        propertiesPath = os.path.join(MODEL_DIR + "/knn_model_" + str(k) + ".p")
        neigh = pickle.load(open(propertiesPath, "rb"))
        neighs.append(neigh)

    k_neighbors = neighs[k_val].kneighbors(np.array(attributes), n_neighbors=k_val)[1][0]
    predicted_price = neighs[int(k_val) - 1].predict(np.array(attributes))

    return k_neighbors, predicted_price


def classifyInstance(request):
    if os.getenv("OPENSHIFT_DATA_DIR") != None:
        OPENSHIFT_DATA_DIR = os.getenv("OPENSHIFT_DATA_DIR")
    else:
        PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
        OPENSHIFT_DATA_DIR = os.path.join(PROJECT_PATH, "data")

    MODEL_DIR = os.path.join(OPENSHIFT_DATA_DIR, "appraiseaway_data/model_instances")
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    propertiesPath = os.path.join(OPENSHIFT_DATA_DIR, "appraiseaway_data/house_properties.csv")
    data = pd.read_csv(propertiesPath)

    k_val = int(request.GET.get('k_val'))
    bedrooms = int(request.GET.get('bedrooms'))
    bathrooms = float(request.GET.get('bathrooms'))
    zip_code = str(request.GET.get('zip_code'))
    home_size = float(request.GET.get('home_size'))
    year_built = int(request.GET.get('year_built'))
    walkscore = getWalkScore(zip_code)

    attributes = [zip_code, year_built, home_size, bathrooms, bedrooms, walkscore]

    k_neighbors, knn_predicted_price = getNeighborsUsingKNN(attributes, k_val, MODEL_DIR)
    rf_predicted_price = getPriceUsingRF(attributes, MODEL_DIR)

    jsonResponse = {}
    jsonResponse["price_prediction"] = rf_predicted_price
    neighborsDict = {}
    for i in range(len(k_neighbors)):
        neighborAttr = {}
        neighborAttr["knn_index"] = str(k_neighbors[i])
        neighborAttr["zpid"] = str(data.loc[k_neighbors[i], 'zpid'])
        neighborsDict["neighbor" + str(i)] = neighborAttr
    jsonResponse["neighbors"] = neighborsDict
    jsonResponse["bedrooms"] = bedrooms
    jsonResponse["bathrooms"] = bathrooms
    jsonResponse["zip_code"] = zip_code
    jsonResponse["home_size"] = home_size
    jsonResponse["year_built"] = year_built

    return JsonResponse(jsonResponse)
