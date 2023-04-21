import ast
import json
from datetime import date

import keras
import requests
from keras import backend as K

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time

def coeff_determination(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res/(SS_tot + K.epsilon()))


def neural_model():
    model = keras.models.load_model('ml_model/model_500it512x3.h5', custom_objects={'coeff_determination': coeff_determination})
    with open("ml_model/model_features.json", "r") as file:
        features = ast.literal_eval(file.read())
    return {"model": model, "features": features}


headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'Authorization': 'bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoicHJlZHMiLCJzIjoiY2FsYy1mcm9udCJ9.LNjGQxSrx3HT3KbjvPBLpOQhHZd-HKRyfU1QKkJC1Oo',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://domclick.ru',
        'Referer': 'https://domclick.ru/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.41',
        'sec-ch-ua': '"Microsoft Edge";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

def get_price(address, rooms, area):

    json_data = {
        'geocode_str': f'Россия, Республика Татарстан, Казань, улица {address}',
        'kind': [
            'house',
        ],
        'precision': [
            'exact',
        ],
    }

    try:
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data)
        guid = json.loads(response.text)["answer"]["guid"]
    except:
        return {"market_price": None, "min_market_price": None, "max_market_price": None, "error": True}

    params = {
        'quality': '2',
        # 'wall_material': '2',
        'rooms': f'{rooms}',
        'comm_sq': f'{area}',
        'guid': guid,  # '247df637-c07d-4320-92d4-e9b2edcc33e1',
        # 'include_analogs': '1',
    }

    response = requests.get(
        'https://liquidator-proxy.domclick.ru/api/v4/pricepredict',
        params=params,
        headers=headers,
    )

    market_price = json.loads(response.text)["answer"]["market_price"]
    max_market_price = json.loads(response.text)["answer"]["max_market_price"]
    min_market_price = json.loads(response.text)["answer"]["min_market_price"]

    return {"market_price": market_price, "min_market_price": min_market_price, "max_market_price": max_market_price, "error": False}


def get_price_history(address):

    json_data = {
        'geocode_str': f'Россия, Республика Татарстан, Казань, улица {address}',
        'kind': [
            'house',
        ],
        'precision': [
            'exact',
        ],
    }

    try:
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data)
    except:
        return None

    guid = json.loads(response.text)["answer"]["guid"]

    params = {
        'house_guid': guid,
        'date_from': '2019-01-01',
        'date_to': date.today(),
    }

    response = requests.get('https://price-charts.domclick.ru/api/v1/house', params=params, headers=headers)

    city_points = json.loads(response.text)["answer"]["city_points"]
    district_points = json.loads(response.text)["answer"]["district_points"]
    house_points = json.loads(response.text)["answer"]["house_points"]
    region_points = json.loads(response.text)["answer"]["region_points"]


    months = [i['month'] for i in city_points]
    city_points = [i["price"] for i in city_points]
    district_points = [i["price"] for i in district_points]
    house_points = [i["price"] for i in house_points]
    region_points = [i["price"] for i in region_points]

    city_coef = city_points[len(city_points)-1] / city_points[months.index("2022-01-01")]
    house_coef = house_points[len(house_points)-1] / house_points[months.index("2022-01-01")]
    district_coef = district_points[len(district_points)-1] / district_points[months.index("2022-01-01")]

    return {"months": months, "city_points": city_points, "district_points": district_points, "house_points": house_points, "region_points": region_points, "city_coef": city_coef, "house_coef": house_coef, "district_coef": district_coef}


def get_house_info(address):
    json_data = {
        'geocode_str': f'Россия, Республика Татарстан, Казань, улица {address}',
        'kind': [
            'house',
        ],
        'precision': [
            'exact',
        ],
    }

    try:
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data)
    except:
        return None

    guid = json.loads(response.text)["answer"]["guid"]

    params = {
        'guid': guid,
    }

    response = requests.get(
        'https://liquidator-proxy.domclick.ru/geo/v1/smart-house',
        params=params,
        headers=headers,
    )

    data = json.loads(response.text)
    try:
        metro_name = data["answer"]["poi"][0]["display_name"]
    except:
        metro_name = None
    try:
        metro_distance = data["answer"]["poi"][0]["distance"]
    except:
        metro_distance = None
    try:
        raion_name = data["answer"]["districts"][0]["display_name"]
    except:
        raion_name = None
    try:
        built_year = data["answer"]["house_info"]["built_year"]
    except:
        built_year = None
    try:
        house_address = data["answer"]["name"]
    except:
        house_address = None

    lat = data["answer"]['lat']
    lon = data["answer"]['lon']

    try:
        photos = [f"https://img.dmclk.ru/s960x640q80{i['storage_url']}" for i in data["answer"]["house_photos"]]
    except:
        photos = []
    return {"photos": photos, "metro_name": metro_name, "metro_distance": metro_distance, "raion_name": raion_name, "built_year": built_year, "house_address": house_address, "lat": lat, "lon": lon}



def get_avito_data(address, rooms, area, floor, floorAtHouse):
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        # executable_path="C:/Users/mansu/Downloads/chromedriver_win32/chromedriver",
        executable_path="../../ApartmentsProject/chromedriver",
        options=options
    )

    try:
        driver.get("https://www.avito.ru/evaluation/realty/")
        address_field = driver.find_element(By.NAME, "address")
        address_field.clear()
        address_field.send_keys(address)
        time.sleep(1)
        address_field = driver.find_element(By.CLASS_NAME, "suggest-suggest-gqVpu")
        address_field.click()

        rooms_field = Select(driver.find_element(By.NAME, "rooms"))
        rooms_field.select_by_value(rooms)

        area_field = driver.find_element(By.NAME, "area")
        area_field.clear()
        area_field.send_keys(area)

        floor_field = driver.find_element(By.NAME, "floor")
        floor_field.clear()
        floor_field.send_keys(floor)

        floorAtHouse_field = driver.find_element(By.NAME, "floorAtHouse")
        floorAtHouse_field.clear()
        floorAtHouse_field.send_keys(floorAtHouse)

        renovationType = Select(driver.find_element(By.NAME, "renovationType"))
        renovationType.select_by_value("cosmetic")

        houseType = Select(driver.find_element(By.NAME, "houseType"))
        houseType.select_by_value("brick")

        button = driver.find_element(By.CLASS_NAME, "index-submitButton-n8vij")
        driver.execute_script("arguments[0].click();", button)
        time.sleep(5)

        # min_price = driver.find_element(By.CLASS_NAME, "css-168huo8").text
        # price = driver.find_element(By.CLASS_NAME, "css-whcfla").text
        # max_price = driver.find_element(By.CLASS_NAME, "css-168huo8").text
        # print(min_price.split()[1])
        # print(price.split()[0])
        # print(max_price.split()[1])

        spl = str(driver.page_source).split('млн')
        min_price = spl[0].split("до ")[1]
        price = spl[1].split("от ")[1]
        max_price = spl[2].split(">")[-1]

        return({"min_price": min_price, "price": price, "max_price": max_price})

    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()



# def get_prediction_model():
#     df = pd.read_csv('https://query.data.world/s/vha3wyujw2famdzxa46zpep5gwdtym')
#     kazan = df[(df['id_region'] == 16) & (df['postal_code'] >= 420000) & (df['postal_code'] < 421000)]
#     kazan = kazan[kazan['price'] < 14000000]
#     kazan = kazan[kazan['area'] < 140]
#     a = kazan.copy()
#     a = a.drop(['Unnamed: 0', 'date', 'building_type', 'geo_lat', 'geo_lon', 'house_id', 'street_id', 'id_region'],
#                axis=1)
#
#     one_hot = pd.get_dummies(a['postal_code'])
#     a = a.drop('postal_code', axis=1)
#     a = a.join(one_hot)
#
#     a.columns = a.columns.astype(str)
#
#     prices = a['price']
#     features = a.drop('price', axis=1)
#
#     X_train, X_test, Y_train, Y_test = train_test_split(features, prices, test_size=0.2, random_state=10)
#
#     regr = LinearRegression()
#     regr.fit(X_train, Y_train)
#
#     return {"model": regr, "features": features}
