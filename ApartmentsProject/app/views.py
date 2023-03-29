from django.shortcuts import render
from django.views import generic, View

from app.forms import ObjectForm
from app.utils import get_price, get_price_history, neural_model, get_prediction_model, get_house_info

prediction_model1 = get_prediction_model()
# print("Success")

prediction_model = neural_model()



class MainPageView(generic.TemplateView):
    template_name = 'main_page.html'


class MainView(View):

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
            print(str(float(data.get("postal_code"))))
            f = [f]
            prices = get_price(address=r.cleaned_data.get("address"), rooms=r.cleaned_data.get("rooms"), area=r.cleaned_data.get("area"))

            my_price = prediction_model.get("model").predict(f)
            my_price1 = prediction_model1.get("model").predict(f)

            price_history = get_price_history(address=r.cleaned_data.get("address"))
            photos = get_house_info(address=r.cleaned_data.get("address"))
            if not prices.get("error"):
                return render(request, 'result.html', {"my_price": round(my_price[0][0]/1000000, 2), "my_price1": round(my_price1[0]/1000000, 2), "other_prices": prices, "price_history": price_history, "photos": photos})
            else:
                return render(request, 'result.html', {"price": "error"})




# Добавить

# Информцию о доме
# Карты
# Получать индекс и количество этажей в доме из API

