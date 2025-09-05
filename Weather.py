import requests
city_name = input("Enter the city:-")

API_Key = "6c95410239msh6901ad4bccd5692p116e14jsn89c74385f4ab"
url = "https://weatherapi-com.p.rapidapi.com/alerts.json"

headers = {
    "X-RapidAPI-Key": API_Key,
    "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
}

params = {"q": city_name}

response = requests.get(url, headers=headers, params=params)

data = response.json()
print("City:", data["location"]["name"])
print("Country:", data["location"]["country"])
print("Temperature (°C):", data["current"]["temp_c"])
print("Condition:", data["current"]["condition"]["text"])
