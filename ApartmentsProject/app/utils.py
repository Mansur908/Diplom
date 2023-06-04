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
from catboost import CatBoostRegressor

def coeff_determination(y_true, y_pred):
    SS_res =  K.sum(K.square(y_true - y_pred))
    SS_tot = K.sum(K.square(y_true - K.mean(y_true)))
    return (1 - SS_res/(SS_tot + K.epsilon()))


def neural_model():
    model = keras.models.load_model('ml_model/model_500it512x3.h5', custom_objects={'coeff_determination': coeff_determination})
    with open("ml_model/model_features.json", "r") as file:
        features = ast.literal_eval(file.read())
    return {"model": model, "features": features}

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
        print(response.text)
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
    cookies = {
        'gdpr': '0',
        '_ym_uid': '16628061384553095',
        'suid': '229083780277c594cd435947c5fa1166.0d84a3470a8e929cfc8e8323ec62793d',
        'yandex_login': 'mansurnurgaleev',
        'yandexuid': '4568416251597769814',
        'my': 'YwA=',
        'L': 'R3UDUlpwRwZ3UFhiemhQYkR0TwFhXHZWFDsIJg8TKkcVCSMeNzMj.1671038781.15191.360086.569d8c528d7b688439695ec3de6fa469',
        'font_loaded': 'YSv1',
        'i': 'hbU0esgR6Uiun3l8Yk1AI6ZS+6gvNar4AIRoIBQ5Dxca6+1mvQydxiO1zamYr7mJZDkwq4NHt7ecE21BuHy3jkSdtPM=',
        'link_to_global_tooltip_shown': 'YES',
        'backcall_agreement_popup_shown': 'YES',
        'is_gdpr': '0',
        'is_gdpr_b': 'CI3/eBCXtwEoAg==',
        'yandex_csyr': '1684008015',
        'yandex_gid': '43',
        '_yasc': 'z/KZeoM9i5NQVsk89ec/62Ff2AWvvUlf0yhRVhhlfi8EqmqvyWpkSZdcX1Lr1hvs',
        '_ym_d': '1685099584',
        '_yasc': 'lp6sUguEHa5sJvyGW6pjBF62r/YJOZTmMJLTQtFHcUiutfB50ywIJvJofOk=',
        'adSource': 'yandex_direct%2C1685099588259%2C460_67550027_msk_poisk_tgo_newbuilding_common_adsource%2Ccid%3A67550027%7Cgid%3A4748775472%7Caid%3A11405341657%7Cph%3A44260587579%7Cpt%3Apremium%7Cpn%3A1%7Csrc%3Anone%7Cst%3Asearch',
        'show_egrn_reports_link': 'NO_717635560',
        'housearch_popup_shown': 'YES',
        'exp_uid': '1168559c-5e7f-4c21-ba44-418355c1d3f7',
        '_ga': 'GA1.1.1269829652.1685099625',
        '_ga_CP0397ZQ47': 'GS1.1.1685099625.1.1.1685099994.0.0.0',
        'rgid': '582357',
        '_ym_isad': '2',
        '_ym_visorc': 'b',
        'spravka': 'dD0xNjg1ODk0NDE4O2k9MTc2LjUyLjI2LjIwNDtEPTM3RDhCOTA1MTU2NzY4MkVDNTE1QThDOEM5ODM0MjQ1MzUzM0E4Q0Q0MzNGNjgzNzhDOTBGNTA1QTNCQzdCRDA3MTZCN0UyMjBERjcyRjlGMENBNURFNkUyN0U5NjVDRjc0N0Q3MkU1NTlDOTRBQUNCNUVGOUU2NDBDO3U9MTY4NTg5NDQxODI1MDgxNzE3ODtoPWM4YTE4NjYyYzNjODgzYWU2YzA0MzM5NjQ4MmMxZWZk',
        '_csrf_token': 'b55e54b8ae12e31768158260094590f018fd2df2bb8b3fde',
        'prev_uaas_data': '4568416251597769814%23761679%23746795%23772130%23710253%23721757%23760224%23758923%23763775%23213160%23361531%23610826%23337343%23761554%23763787%23765891%23777831%23769750',
        'prev_uaas_expcrypted': 'gVX_ek_V991YXzAvIdEuoBdeKC_QH0DFpe07AWfIRRYp2T7XiZhOFQuzKW6_v_GnHe0-LUF0WZmxelcEFiNcTMk-PiY9aDy2oYW2Awjny7Wuxc_tSWma6jAF6KEMBcEmJs3NIdAOyHvpA9fSAm7R2QnRmRJk6mre8Pt336JNjJEOBHknqGEOjHnePLXJQBW8ChdflWwaYSlkqfnDTZS-lKttYsG5arFdCzn1hQpeMxj6wLQmPTPu3drnmcKZS7KjilUrC4t0i44%2C',
        'Session_id': '3:1685894418.5.1.1657919276792:gBw0sA:27.1.2:1|1659530635.-1.0|717635560.-1.2.1:135228406.2:13119505|6:10182473.13434.TjDpYALWK0OcFO5mbp3N5jH6BpA',
        'sessar': '1.99.CiC-sCFeG3pYu_kbEpEi4MyydAoPHQRcWhwU_sC62OkSWA.htEQU-EImnRwCBUcAmSYtvbJeZ4JFlwM-qXLfUw0_gI',
        'yp': '2001253698.pcs.0#1717362811.p_sw.1685826811#1686929947.hdrc.0#1712309349.stltp.serp_bk-map_1_1680773349#1996605646.hks.0#1716985620.p_cl.1685449620#1686241324.mcv.1#1686241324.mcl.190w8iu#1686331247.szm.1:1680x1050:1680x939#1717362812.p_undefined.1685826811#2001254418.udn.cDptYW5zdXJudXJnYWxlZXY%3D',
        'ys': 'udn.cDptYW5zdXJudXJnYWxlZXY%3D#c_chck.1481632492',
        'mda2_beacon': '1685894418915',
        'sso_status': 'sso.passport.yandex.ru:synchronized',
        'from': 'other',
        'from_lifetime': '1685894424902',
    }

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
