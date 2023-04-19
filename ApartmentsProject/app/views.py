from django.shortcuts import render
from django.views import View

from app.forms import ObjectForm
from app.utils import get_price, get_price_history, neural_model, get_house_info

prediction_model = neural_model()

class MainView(View):

    def get(self, request):
        return render(request, 'main_page.html')

    def post(self, request):
        r = ObjectForm(request.POST)
        if r.is_valid():
            # columns = list(prediction_model.get("features").columns)
            columns = prediction_model.get("features")
            data = r.cleaned_data
            f1 = [int(data.get("level")), int(data.get("levels")), int(data.get("rooms")), int(data.get("area")), int(data.get("kitchen_area")), 0]
            f2 = [0 for i in range(len(columns) - 6)]
            f = f1+f2
            if str(float(data.get("postal_code"))) in columns:
                f[columns.index(str(float(data.get("postal_code"))))] = 1
            f = [f]
            prices = get_price(address=r.cleaned_data.get("address"), rooms=r.cleaned_data.get("rooms"), area=r.cleaned_data.get("area"))

            price_history = get_price_history(address=r.cleaned_data.get("address"))

            my_prices = []
            my_prices.append(round(prediction_model.get("model").predict(f)[0][0]*price_history.get("city_coef")/1000000, 2))
            my_prices.append(round(prediction_model.get("model").predict(f)[0][0]*price_history.get("house_coef")/1000000, 2))
            my_prices.append(round(prediction_model.get("model").predict(f)[0][0]*price_history.get("district_coef")/1000000, 2))


            my_prices.sort()
            print(my_prices)
            # my_price1 = prediction_model.get("model").predict(f)*price_history.get("house_coef")
            # my_price1 = prediction_model1.get("model").predict(f)

            house_info = get_house_info(address=r.cleaned_data.get("address"))
            if not prices.get("error"):
                return render(request, 'result.html', {"my_prices": my_prices, "other_prices": prices, "price_history": price_history, "house_info": house_info})
            else:
                return render(request, 'result.html', {"price": "error"})

