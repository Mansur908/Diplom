import ast
import json
from datetime import date

import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
from catboost import CatBoostRegressor


def catboost_model():
    from_file = CatBoostRegressor()
    model = from_file.load_model("ml_model/catboost_model")
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
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data, verify=False)
        guid = json.loads(response.text)["answer"]["guid"]
    except:
        return {"market_price": None, "min_market_price": None, "max_market_price": None, "error": True}

    params = {
        'quality': '2',
        'rooms': f'{rooms}',
        'comm_sq': f'{area}',
        'guid': guid
    }

    response = requests.get(
        'https://liquidator-proxy.domclick.ru/api/v4/pricepredict',
        params=params,
        headers=headers,
        verify=False
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
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data, verify=False)
    except:
        return None

    guid = json.loads(response.text)["answer"]["guid"]

    params = {
        'house_guid': guid,
        'date_from': '2019-01-01',
        'date_to': date.today(),
    }

    response = requests.get('https://price-charts.domclick.ru/api/v1/house', params=params, headers=headers, verify=False)

    city_points = json.loads(response.text)["answer"]["city_points"]
    district_points = json.loads(response.text)["answer"]["district_points"]
    house_points = json.loads(response.text)["answer"]["house_points"]
    region_points = json.loads(response.text)["answer"]["region_points"]


    months = [i['month'] for i in city_points]
    city_points = [i["price"] for i in city_points]
    district_points = [i["price"] for i in district_points]
    house_points = [i["price"] for i in house_points]
    region_points = [i["price"] for i in region_points]
    
    try:
        city_coef = city_points[len(city_points)-1] / city_points[months.index("2022-01-01")]
        house_coef = house_points[len(house_points)-1] / house_points[months.index("2022-01-01")]
        district_coef = district_points[len(district_points)-1] / district_points[months.index("2022-01-01")]
    except:
        city_coef, house_coef, district_coef = 1, 1, 1



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
        response = requests.post('https://liquidator-proxy.domclick.ru/geo/v1/geocode', headers=headers, json=json_data, verify=False)
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
        verify=False
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
        photos = [f"http://img.dmclk.ru/s960x640q80{i['storage_url']}" for i in data["answer"]["house_photos"]]
    except:
        photos = []
    return {"photos": photos, "metro_name": metro_name, "metro_distance": metro_distance, "raion_name": raion_name, "built_year": built_year, "house_address": house_address, "lat": lat, "lon": lon}



def get_avito_data(address, rooms, area, floor, floorAtHouse):
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless")

    try:
        driver = webdriver.Chrome(
            executable_path="C:/Users/mansu/Downloads/chromedriver_win32/chromedriver.exe",
            # executable_path="/usr/src/project/chromedriver",
            # executable_path="../../ApartmentsProject/chromedriver.exe",
            options=options
        )

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

        spl = str(driver.page_source).split('млн')
        min_price = spl[0].split("до ")[1]
        max_price = spl[1].split("от ")[1]
        price = spl[2].split(">")[-1]

        return({"min_price": min_price, "price": price, "max_price": max_price})

    except Exception as ex:
        print(ex)
        return ({"min_price": "-", "price": "-", "max_price": "-"})
    finally:
        driver.close()
        driver.quit()


def get_yandex_data(address, rooms, area):
    cookies = {}

    headers = {
        'authority': 'realty.ya.ru',
        'accept': 'application/json',
        'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'client-view-type': 'desktop',
        'content-type': 'application/json',
        'origin': 'https://realty.ya.ru',
        'referer': 'https://realty.ya.ru/calculator-stoimosti/kvartira/odnokomnatnaya/?address=%D0%A0%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B0%20%D0%A2%D0%B0%D1%82%D0%B0%D1%80%D1%81%D1%82%D0%B0%D0%BD%2C%20%D0%9A%D0%B0%D0%B7%D0%B0%D0%BD%D1%8C%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%97%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0%2C%207&area=120',
        'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50',
        'x-client-version': '353.0.11564961',
        'x-metrika-client-id': '16628061384553095',
        'x-requested-with': 'XMLHttpRequest',
        'x-retpath-y': 'https://realty.ya.ru/calculator-stoimosti/kvartira/odnokomnatnaya/?address=%D0%A0%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B0%20%D0%A2%D0%B0%D1%82%D0%B0%D1%80%D1%81%D1%82%D0%B0%D0%BD%2C%20%D0%9A%D0%B0%D0%B7%D0%B0%D0%BD%D1%8C%2C%20%D1%83%D0%BB%D0%B8%D1%86%D0%B0%20%D0%97%D0%B8%D0%BD%D0%B8%D0%BD%D0%B0%2C%207&area=120',
    }

    json_data = {
        'fields': {
            'ADDRESS': f'Республика Татарстан, Казань, улица {address}',
            'ROOMS': f'{rooms}',
            'AREA': f'{area}',
        },
        'offerType': 'SELL',
        'offerCategory': 'APARTMENT',
        'page': 1,
        'pageSize': 3,
    }

    response = requests.post(
        'https://realty.ya.ru/gate/ya-deal-valuation/get-flat-valuation/',
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    data = json.loads(response.text)
    try:
        price = int(data['response']['priceSimilar']['range']['currentBuildingPrice'])
        price = round(price / 1000000, 2)
        max_price = int(data['response']['priceSimilar']['range']['max'])
        max_price = round(max_price / 1000000, 2)
        min_price = int(data['response']['priceSimilar']['range']['min'])
        min_price = round(min_price / 1000000, 2)
    except:
        price, max_price, min_price = None, None, None
    try:
        ceiling_height = data['response']['buildingInfo']['ceilingHeight']
    except:
        try:
            ceiling_height = int(float(data['response']['archiveData']['offers'][0]['apartment']['ceilingHeight'])*100)
        except:
            ceiling_height = None
    try:
        flats_count = data['response']['buildingInfo']['flatsCount']
    except:
        flats_count = None
    try:
        floors = data['response']['buildingInfo']['floors']
    except:
        floors = None
    try:
        has_elevator = data['response']['buildingInfo']['hasElevator']
    except:
        has_elevator = None
    try:
        has_gas = data['response']['buildingInfo']['hasGas']
    except:
        has_gas = None
    try:
        metro_time = data['response']['buildingInfo']['metros'][0]['time']
    except:
        metro_time = None

    return({"min_price": min_price, "price": price, "max_price": max_price,
            "ceiling_height": ceiling_height, "flats_count": flats_count, "floors": floors,
            "has_elevator": has_elevator, "has_gas": has_gas, "metro_time": metro_time})
