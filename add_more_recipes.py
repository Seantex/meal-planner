#!/usr/bin/env python3
"""Fügt weitere beliebte Rezepte zu recipes.json hinzu."""
import json, os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(BASE, "data", "recipes.json")

NEW_RECIPES = [
  # ── Burger & Fast-Food-Style ──────────────────────────────────────────────
  {
    "id": "smash_burger", "name": "Smash Burger mit Doppelpatty",
    "description": "Knusprige, dünn gebratene Rindfleisch-Patties mit Schmelzkäse und hausgemachter Burger-Sauce",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 15, "cook_time": 15, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 780, "protein": 45, "carbs": 52, "fat": 42},
    "tags": ["burger","rindfleisch","käse","amerikanisch"],
    "deal_keywords": ["rinderhack","faschiertes","toastbrot","burger bun","cheddar","speck"],
    "ingredients": [
      {"name":"Rinderhackfleisch (80/20)","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Burger Buns","amount":2,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Cheddar","amount":4,"unit":"Scheiben","category":"käse","is_basic":False},
      {"name":"Speck","amount":4,"unit":"Scheiben","category":"fleisch","is_basic":False},
      {"name":"Eisbergsalat","amount":4,"unit":"Blätter","category":"gemüse","is_basic":False},
      {"name":"Tomate","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Gurken-Scheiben","amount":6,"unit":"Scheiben","category":"gemüse","is_basic":False},
      {"name":"Mayonnaise","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Ketchup","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Senf","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
      {"name":"Schwarzer Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Gusseisenpfanne sehr heiß erhitzen – kein Öl! Fleisch beim Einlegen sofort mit Pfannenwender flachdrücken.",
    "recipe_url": ""
  },
  {
    "id": "chicken_burger", "name": "Crispy Chicken Burger",
    "description": "Knuspriges frittiertes Hähnchenfilet im Brioche-Bun mit Coleslaw und Jalapeños",
    "category": "geflügel", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 15, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 720, "protein": 42, "carbs": 65, "fat": 28},
    "tags": ["burger","hähnchen","knusprig","amerikanisch"],
    "deal_keywords": ["hähnchenfilet","brioche","buttermilch","paniermehl"],
    "ingredients": [
      {"name":"Hähnchenfilet","amount":2,"unit":"Stück","category":"fleisch","is_basic":False},
      {"name":"Buttermilch","amount":200,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Paniermehl","amount":150,"unit":"g","category":"brot","is_basic":False},
      {"name":"Paprikapulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Brioche Buns","amount":2,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Coleslaw","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Jalapeños (aus dem Glas)","amount":10,"unit":"Ringe","category":"konserven","is_basic":False},
      {"name":"Mayonnaise","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Öl zum Frittieren","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
    ],
    "tips": "Hähnchen über Nacht in Buttermilch einlegen – macht es unglaublich saftig und zart.",
    "recipe_url": ""
  },
  # ── Pizza & Flatbread ─────────────────────────────────────────────────────
  {
    "id": "pizza_margherita", "name": "Pizza Margherita mit Büffelmozzarella",
    "description": "Knusprig-luftiger Teig mit San-Marzano-Tomaten und frischem Büffelmozzarella",
    "category": "pasta", "type": "weekend", "difficulty": "mittel",
    "prep_time": 90, "cook_time": 15, "total_time": 105, "servings": 2,
    "nutrition_per_portion": {"calories": 640, "protein": 22, "carbs": 88, "fat": 18},
    "tags": ["pizza","vegetarisch","italienisch","teig"],
    "deal_keywords": ["mozzarella","pizzateig","tomaten","basilikum","mehl"],
    "ingredients": [
      {"name":"Pizzamehl (Tipo 00)","amount":300,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Trockenhefe","amount":5,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Büffelmozzarella","amount":250,"unit":"g","category":"käse","is_basic":False},
      {"name":"San-Marzano Tomaten (Dose)","amount":400,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Frischer Basilikum","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Knoblauch","amount":1,"unit":"Zehe","category":"gemüse","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Ofen so heiß wie möglich vorheizen (min. 250°C). Pizzastein oder umgedrehtes Backblech verwenden.",
    "recipe_url": ""
  },
  {
    "id": "pizza_salami", "name": "Pizza Diavola mit Salami",
    "description": "Würzig-scharfe Pizza mit Salami piccante, Paprika und Chili-Öl",
    "category": "pasta", "type": "weekend", "difficulty": "mittel",
    "prep_time": 90, "cook_time": 15, "total_time": 105, "servings": 2,
    "nutrition_per_portion": {"calories": 720, "protein": 28, "carbs": 85, "fat": 26},
    "tags": ["pizza","salami","scharf","italienisch"],
    "deal_keywords": ["salami","pizzateig","mozzarella","paprika","chili"],
    "ingredients": [
      {"name":"Pizzateig (fertig oder selbst)","amount":400,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Salami piccante","amount":80,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Mozzarella","amount":200,"unit":"g","category":"käse","is_basic":False},
      {"name":"Pizzasauce","amount":150,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Rote Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Peperoncini","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    ],
    "tips": "Salami erst die letzten 3 Minuten auflegen – sonst verbrennt sie.",
    "recipe_url": ""
  },
  # ── Pasta Premium ─────────────────────────────────────────────────────────
  {
    "id": "pasta_carbonara", "name": "Spaghetti Carbonara (Original)",
    "description": "Das echte römische Rezept – cremig durch Ei und Pecorino, mit Guanciale und ohne einen Tropfen Sahne",
    "category": "pasta", "type": "weekday", "difficulty": "mittel",
    "prep_time": 5, "cook_time": 20, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 720, "protein": 28, "carbs": 78, "fat": 32},
    "tags": ["pasta","carbonara","eier","käse","schnell","römisch"],
    "deal_keywords": ["spaghetti","speck","pecorino","parmesan","eier","guanciale"],
    "ingredients": [
      {"name":"Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Guanciale oder Pancetta","amount":120,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Eier (2 ganz + 2 Eigelb)","amount":4,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Pecorino Romano","amount":60,"unit":"g","category":"käse","is_basic":False},
      {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
      {"name":"Schwarzer Pfeffer","amount":None,"unit":"reichlich","category":"gewürze","is_basic":True},
    ],
    "tips": "Pfanne vom Herd nehmen bevor du die Ei-Käse-Mischung einrührst – sonst wird es Rührei statt Carbonara.",
    "recipe_url": ""
  },
  {
    "id": "tagliatelle_bolognese", "name": "Tagliatelle Bolognese (original)",
    "description": "Langsam geschmorte Rindfleisch-Bolognese mit Tagliatelle – Soulfood at its finest",
    "category": "pasta", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 90, "total_time": 110, "servings": 2,
    "nutrition_per_portion": {"calories": 740, "protein": 38, "carbs": 72, "fat": 30},
    "tags": ["pasta","bolognese","rindfleisch","ragù","italienisch"],
    "deal_keywords": ["rinderhack","faschiertes","tagliatelle","tomaten","rotwein","sellerie","karotte"],
    "ingredients": [
      {"name":"Tagliatelle","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Rinderhackfleisch","amount":300,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Pancetta","amount":50,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Stangensellerie","amount":2,"unit":"Stangen","category":"gemüse","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Tomaten (Dose, gehackt)","amount":400,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Rotwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Milch","amount":50,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Parmesan","amount":50,"unit":"g","category":"käse","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Je länger sie kocht, desto besser. Mindestens 90 Minuten, am besten 3 Stunden auf kleiner Flamme.",
    "recipe_url": ""
  },
  {
    "id": "lasagne_classica", "name": "Lasagne al forno",
    "description": "Klassische Lasagne mit saftiger Bolognese, cremiger Béchamel und viel Parmesan",
    "category": "pasta", "type": "weekend", "difficulty": "schwer",
    "prep_time": 40, "cook_time": 50, "total_time": 90, "servings": 2,
    "nutrition_per_portion": {"calories": 860, "protein": 42, "carbs": 75, "fat": 42},
    "tags": ["pasta","lasagne","bolognese","béchamel","käse","ofengericht"],
    "deal_keywords": ["lasagneplatten","rinderhack","faschiertes","mozzarella","parmesan","butter","mehl"],
    "ingredients": [
      {"name":"Lasagneplatten","amount":12,"unit":"Blätter","category":"nudeln","is_basic":False},
      {"name":"Rinderhackfleisch","amount":300,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Tomaten (Dose)","amount":400,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Mozzarella","amount":150,"unit":"g","category":"käse","is_basic":False},
      {"name":"Parmesan","amount":80,"unit":"g","category":"käse","is_basic":False},
      {"name":"Milch","amount":500,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Butter","amount":40,"unit":"g","category":"milch","is_basic":False},
      {"name":"Weizenmehl","amount":40,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
      {"name":"Muskatnuss","amount":None,"unit":"Prise","category":"gewürze","is_basic":False},
    ],
    "tips": "15 Minuten vor dem Essen ruhen lassen – dann lässt sie sich besser schneiden und schmeckt noch besser.",
    "recipe_url": ""
  },
  # ── Asiatisch ─────────────────────────────────────────────────────────────
  {
    "id": "ramen_tonkotsu", "name": "Tonkotsu Ramen",
    "description": "Reiche, cremige Schweinebrühe mit Ramen-Nudeln, weich gekochtem Ei und Chashu-Schweinefleisch",
    "category": "suppe", "type": "weekend", "difficulty": "schwer",
    "prep_time": 30, "cook_time": 120, "total_time": 150, "servings": 2,
    "nutrition_per_portion": {"calories": 820, "protein": 44, "carbs": 68, "fat": 38},
    "tags": ["ramen","japanisch","suppe","nudeln","ei","schweinefleisch"],
    "deal_keywords": ["schweinebauch","ramen nudeln","sojasauce","ingwer","frühlingszwiebeln","eier","miso"],
    "ingredients": [
      {"name":"Ramen-Nudeln","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Schweinebauch","amount":300,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Sojasauce","amount":4,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Mirin","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Ingwer","amount":3,"unit":"Scheiben","category":"gewürze","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Miso-Paste","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Schweineknochen-Brühe oder Fond","amount":1000,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Bambussprossen (Dose)","amount":100,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Nori-Blätter","amount":2,"unit":"Blätter","category":"sonstiges","is_basic":False},
      {"name":"Sesam","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
    ],
    "tips": "Für intensive Brühe: Schweineknochen 3 Min. kochen, abgießen, dann 2h langsam simmern. Eier 6:30 Min. kochen für wachsweiches Eigelb.",
    "recipe_url": ""
  },
  {
    "id": "pad_thai", "name": "Pad Thai mit Garnelen",
    "description": "Der beliebteste Straßenküchen-Klassiker Thailands – süß-sauer-salzig und unwiderstehlich",
    "category": "fisch", "type": "weekday", "difficulty": "mittel",
    "prep_time": 15, "cook_time": 15, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 32, "carbs": 72, "fat": 22},
    "tags": ["thai","wok","garnelen","nudeln","asiatisch","schnell"],
    "deal_keywords": ["reisnudeln","garnelen","shrimps","erdnüsse","sojasauce","limette","eier"],
    "ingredients": [
      {"name":"Reisnudeln (flat, 5mm)","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Garnelen (geschält)","amount":200,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Erdnüsse (geröstet)","amount":50,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Sojasprossen","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Fischsauce","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Tamarindenpaste","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Zucker","amount":2,"unit":"EL","category":"gewürze","is_basic":True},
      {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Chili","amount":1,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Öl","amount":None,"unit":"zum Braten","category":"sonstiges","is_basic":True},
    ],
    "tips": "Alles vor dem Kochen vorbereiten (Mise en place) – Pad Thai geht sehr schnell und du hast keine Zeit zum Schneiden.",
    "recipe_url": ""
  },
  {
    "id": "butter_chicken", "name": "Butter Chicken (Murgh Makhani)",
    "description": "Das cremigste, aromatischste indische Curry der Welt – Hähnchenfilet in samtig-würziger Tomatensahnesoße",
    "category": "geflügel", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 35, "total_time": 55, "servings": 2,
    "nutrition_per_portion": {"calories": 680, "protein": 42, "carbs": 38, "fat": 38},
    "tags": ["indisch","curry","hähnchen","sahne","tomaten"],
    "deal_keywords": ["hähnchenfilet","kokosmilch","tomaten","sahne","joghurt","garam masala","ingwer"],
    "ingredients": [
      {"name":"Hähnchenfilet","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Griechischer Joghurt","amount":100,"unit":"g","category":"milch","is_basic":False},
      {"name":"Tomaten (Dose, passiert)","amount":400,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Sahne","amount":150,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Butter","amount":40,"unit":"g","category":"milch","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Ingwer (frisch)","amount":3,"unit":"cm","category":"gewürze","is_basic":False},
      {"name":"Garam Masala","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kurkuma","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Basmati-Reis","amount":150,"unit":"g","category":"reis","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Hähnchen zuerst marinieren (mindestens 30 Min. in Joghurt+Gewürzen) und dann in der Pfanne anbraten – gibt Röstaromen.",
    "recipe_url": ""
  },
  {
    "id": "fried_rice_egg", "name": "Gebratener Reis mit Ei (Wok-Style)",
    "description": "Schneller, rauchiger Wok-Reis mit Ei, Gemüse und Sojasauce – besser als jedes Takeout",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 15, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 520, "protein": 16, "carbs": 78, "fat": 14},
    "tags": ["wok","reis","ei","vegetarisch","schnell","asiatisch"],
    "deal_keywords": ["reis","eier","sojasauce","frühlingszwiebeln","karotte","erbsen","knoblauch"],
    "ingredients": [
      {"name":"Gekochter Reis (vom Vortag)","amount":300,"unit":"g","category":"reis","is_basic":False},
      {"name":"Eier","amount":3,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Tiefkühlerbsen","amount":80,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Sojasauce","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Sesamöl","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
      {"name":"Ingwer (frisch)","amount":1,"unit":"cm","category":"gewürze","is_basic":False},
      {"name":"Öl","amount":None,"unit":"zum Braten","category":"sonstiges","is_basic":True},
    ],
    "tips": "Reis vom Vortag ist ideal – er ist trockener und klumpt weniger. Wok so heiß wie möglich erhitzen.",
    "recipe_url": ""
  },
  # ── Steaks & Grill ────────────────────────────────────────────────────────
  {
    "id": "ribeye_steak", "name": "Ribeye Steak mit Kräuterbutter",
    "description": "Perfekt gebratenes Ribeye mit Röstaroma-Kruste und selbstgemachter Petersilien-Kräuterbutter",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 10, "cook_time": 15, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 680, "protein": 52, "carbs": 5, "fat": 48},
    "tags": ["steak","rind","grill","kräuterbutter","low-carb"],
    "deal_keywords": ["ribeye","entrecôte","rindssteak","steak","kräuterbutter","butter","rosmarin"],
    "ingredients": [
      {"name":"Ribeye Steak","amount":2,"unit":"Stück (je 250g)","category":"fleisch","is_basic":False},
      {"name":"Butter","amount":80,"unit":"g","category":"milch","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Frischer Rosmarin","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Frischer Thymian","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Petersilie","amount":2,"unit":"EL","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Meersalz","amount":None,"unit":"grob","category":"gewürze","is_basic":True},
      {"name":"Schwarzer Pfeffer","amount":None,"unit":"grob gemahlen","category":"gewürze","is_basic":True},
    ],
    "tips": "Steak 30 Min. vor dem Braten auf Raumtemperatur bringen. Pfanne soll fast rauchen. Zum Schluss mit Butter, Knoblauch und Rosmarin arrosieren.",
    "recipe_url": ""
  },
  # ── Meeresfrüchte ─────────────────────────────────────────────────────────
  {
    "id": "pasta_gamberi", "name": "Pasta mit Garnelen und Cherrytomaten",
    "description": "Süditalienische Pasta – saftige Garnelen in Knoblauch-Weißwein-Sauce mit Cherrytomaten",
    "category": "fisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 32, "carbs": 68, "fat": 16},
    "tags": ["pasta","garnelen","shrimps","meeresfrüchte","schnell","mediterran"],
    "deal_keywords": ["garnelen","shrimps","linguine","spaghetti","cherrytomaten","weißwein","knoblauch"],
    "ingredients": [
      {"name":"Linguine","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Garnelen (geschält)","amount":250,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Cherrytomaten","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Weißwein","amount":80,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Frische Petersilie","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Peperoncino","amount":1,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":4,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Garnelen nur 2 Minuten pro Seite anbraten – wenn sie sich kringeln und rosa werden sind sie fertig.",
    "recipe_url": ""
  },
  {
    "id": "lachs_teriyaki", "name": "Lachs Teriyaki mit Jasminreis",
    "description": "Glasiertes Lachsfilet mit süßlich-herzhafter Teriyaki-Sauce auf fluffigem Jasminreis",
    "category": "fisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 42, "carbs": 62, "fat": 22},
    "tags": ["lachs","teriyaki","japanisch","reis","schnell"],
    "deal_keywords": ["lachsfilet","lachs","jasminreis","sojasauce","honig","ingwer","sesamöl"],
    "ingredients": [
      {"name":"Lachsfilet","amount":2,"unit":"Stück","category":"fisch","is_basic":False},
      {"name":"Jasminreis","amount":150,"unit":"g","category":"reis","is_basic":False},
      {"name":"Sojasauce","amount":4,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Honig","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Mirin","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Ingwer (frisch)","amount":2,"unit":"cm","category":"gewürze","is_basic":False},
      {"name":"Knoblauch","amount":1,"unit":"Zehe","category":"gemüse","is_basic":False},
      {"name":"Sesamöl","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
      {"name":"Sesam","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"zum Braten","category":"sonstiges","is_basic":True},
    ],
    "tips": "Lachs bei mittlerer Hitze mit der Hautseite nach unten beginnen – 4 Min., dann wenden und nur 2 Min. von der anderen Seite.",
    "recipe_url": ""
  },
  # ── Vegetarisch / Vegan (lecker!) ─────────────────────────────────────────
  {
    "id": "tacos_al_pastor_veg", "name": "Tacos mit gegrilltem Halloumi und Mango-Salsa",
    "description": "Knuspriger Halloumi, fruchtige Mango-Jalapeño-Salsa und cremige Guacamole in Mais-Tortillas",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 20, "cook_time": 10, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 24, "carbs": 58, "fat": 28},
    "tags": ["tacos","halloumi","käse","mango","vegetarisch","mexikanisch"],
    "deal_keywords": ["halloumi","mais tortillas","mango","avocado","jalapeños","limette","koriander"],
    "ingredients": [
      {"name":"Halloumi","amount":250,"unit":"g","category":"käse","is_basic":False},
      {"name":"Mais-Tortillas","amount":6,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Mango","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Jalapeños","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Rote Zwiebel","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Koriander (frisch)","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Rotkohl","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Sauerrahm","amount":4,"unit":"EL","category":"milch","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"zum Braten","category":"sonstiges","is_basic":True},
    ],
    "tips": "Halloumi in dicke Scheiben schneiden und bei hoher Hitze braten – soll goldbraun und karamellisiert werden.",
    "recipe_url": ""
  },
  {
    "id": "aubergine_parmigiana", "name": "Melanzani Parmigiana",
    "description": "Geschichtete Auberginen mit hausgemachter Tomatensauce und geschmolzenem Mozzarella aus dem Ofen",
    "category": "vegetarisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 30, "cook_time": 45, "total_time": 75, "servings": 2,
    "nutrition_per_portion": {"calories": 480, "protein": 22, "carbs": 38, "fat": 26},
    "tags": ["aubergine","melanzani","vegetarisch","ofengericht","italienisch","käse"],
    "deal_keywords": ["auberginen","melanzani","mozzarella","parmesan","tomaten","basilikum"],
    "ingredients": [
      {"name":"Auberginen","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Mozzarella","amount":200,"unit":"g","category":"käse","is_basic":False},
      {"name":"Parmesan","amount":60,"unit":"g","category":"käse","is_basic":False},
      {"name":"Tomaten (Dose, passiert)","amount":400,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Frischer Basilikum","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":4,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Auberginen vor dem Braten 30 Min. gesalzen ruhen lassen und das Wasser abdrücken – dadurch werden sie weicher und nehmen weniger Öl auf.",
    "recipe_url": ""
  },
  # ── Mexikanisch ───────────────────────────────────────────────────────────
  {
    "id": "tacos_carne_asada", "name": "Tacos Carne Asada",
    "description": "Mariniertes, gegrilltes Rindersteak in Tortillas mit Salsa verde und frischer Guacamole",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 15, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 640, "protein": 38, "carbs": 52, "fat": 28},
    "tags": ["tacos","mexikanisch","rindersteak","guacamole","carne asada"],
    "deal_keywords": ["rindersteak","mais tortillas","avocado","limette","koriander","knoblauch"],
    "ingredients": [
      {"name":"Flank Steak oder Rumpsteak","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Mais-Tortillas","amount":8,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Avocado","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Limette","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Koriander","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Jalapeño","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Tomaten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Steak bei sehr hoher Hitze 3-4 Min. pro Seite grillen, dann 5 Min. ruhen lassen und quer zur Faser schneiden.",
    "recipe_url": ""
  },
  # ── Österreichisch-Deutsch ────────────────────────────────────────────────
  {
    "id": "wiener_schnitzel_veal", "name": "Wiener Schnitzel (original)",
    "description": "Das Original: zartes Kalbfleisch, luftig-knusprige Panier, Zitrone und Petersilienbutter",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 15, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 680, "protein": 44, "carbs": 42, "fat": 36},
    "tags": ["schnitzel","wiener schnitzel","kalbfleisch","paniert","österreichisch","klassiker"],
    "deal_keywords": ["kalbsschnitzel","kalbfleisch","semmelbrösel","eier","butter","zitrone"],
    "ingredients": [
      {"name":"Kalbsschnitzel","amount":2,"unit":"Stück (je 180g)","category":"fleisch","is_basic":False},
      {"name":"Semmelbrösel","amount":100,"unit":"g","category":"brot","is_basic":False},
      {"name":"Weizenmehl","amount":80,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Butter","amount":80,"unit":"g","category":"milch","is_basic":False},
      {"name":"Öl (zum Frittieren)","amount":200,"unit":"ml","category":"sonstiges","is_basic":True},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Petersilie","amount":4,"unit":"Zweige","category":"gemüse","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Panier NICHT fest andrücken – die Luft zwischen Fleisch und Panier macht sie fluffig und lässt sie beim Braten 'soufflieren'.",
    "recipe_url": ""
  },
  {
    "id": "gulasch_österr", "name": "Österreichisches Rindsgulasch",
    "description": "Dunkles, tiefes Gulasch mit viel Zwiebel und Paprika – der Inbegriff österreichischer Hausmannskost",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 120, "total_time": 140, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 40, "carbs": 35, "fat": 32},
    "tags": ["gulasch","rindfleisch","österreichisch","eintopf","paprika","klassiker"],
    "deal_keywords": ["rindfleisch","rind","paprikapulver","zwiebel","knoblauch","tomatenmark","lorbeer"],
    "ingredients": [
      {"name":"Rindfleisch (Wadschunken/Gulaschfleisch)","amount":500,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Zwiebeln","amount":4,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Edelsüßes Paprikapulver","amount":3,"unit":"EL","category":"gewürze","is_basic":False},
      {"name":"Geräuchertes Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Tomatenmark","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Rindssuppe oder Wasser","amount":400,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Kümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Lorbeerblätter","amount":2,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Majoran","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Öl","amount":None,"unit":"zum Anbraten","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Das Geheimnis: Zwiebeln sehr lang und dunkel rösten bis sie fast karamelisiert sind. Mindestens 2 Stunden köcheln lassen.",
    "recipe_url": ""
  },
  # ── Hähnchen (weitere) ────────────────────────────────────────────────────
  {
    "id": "haehnchen_shawarma", "name": "Hähnchen Shawarma Bowl",
    "description": "Nahost-Feeling: würziges Shawarma-Hähnchen mit Hummus, Taboulé und Granatapfelkernen",
    "category": "geflügel", "type": "weekday", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 20, "total_time": 40, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 44, "carbs": 52, "fat": 24},
    "tags": ["hähnchen","shawarma","libanesisch","bowl","orientalisch"],
    "deal_keywords": ["hähnchenfilet","hummus","pita","granatapfel","joghurt","kreuzkümmel","koriander"],
    "ingredients": [
      {"name":"Hähnchenfilet","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Hummus (Dose oder selbst)","amount":200,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Griechischer Joghurt","amount":150,"unit":"g","category":"milch","is_basic":False},
      {"name":"Pita-Brot","amount":2,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Gurke","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Tomate","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Rotkohl","amount":150,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Kreuzkümmel","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Koriander (gemahlen)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kurkuma","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
    ],
    "tips": "Hähnchen mindestens 2 Stunden in der Gewürzmarinade ziehen lassen – am besten über Nacht.",
    "recipe_url": ""
  },
  {
    "id": "haehnchen_pesto", "name": "Hähnchen mit Pesto-Kruste und Ofengemüse",
    "description": "Saftige Hähnchenbrüste unter einer aromatischen Pesto-Parmesan-Kruste mit buntem Ofengemüse",
    "category": "geflügel", "type": "weekday", "difficulty": "einfach",
    "prep_time": 15, "cook_time": 25, "total_time": 40, "servings": 2,
    "nutrition_per_portion": {"calories": 560, "protein": 48, "carbs": 22, "fat": 30},
    "tags": ["hähnchen","pesto","ofengericht","gemüse","einfach"],
    "deal_keywords": ["hähnchenfilet","pesto","parmesan","zucchini","paprika","kirschtomaten"],
    "ingredients": [
      {"name":"Hähnchenfilet","amount":2,"unit":"Stück","category":"fleisch","is_basic":False},
      {"name":"Pesto (Glas)","amount":4,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Parmesan","amount":30,"unit":"g","category":"käse","is_basic":False},
      {"name":"Zucchini","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Rote Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Kirschtomaten","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Rote Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
    ],
    "tips": "Gemüse mit Hähnchen zusammen auf dem Blech bei 200°C backen – alles ist gleichzeitig fertig und das Gemüse nimmt die Hähnchensäfte auf.",
    "recipe_url": ""
  },
  # ── Süßes (Dessert) ───────────────────────────────────────────────────────
  {
    "id": "tiramisu", "name": "Tiramisu (klassisch)",
    "description": "Das unwiderstehliche italienische Dessert: Espresso-getränkte Löffelbiskuits mit cremiger Mascarpone",
    "category": "süß", "type": "weekend", "difficulty": "einfach",
    "prep_time": 25, "cook_time": 0, "total_time": 250, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 12, "carbs": 58, "fat": 38},
    "tags": ["dessert","tiramisu","mascarpone","kaffee","italienisch","no-bake"],
    "deal_keywords": ["mascarpone","löffelbiskuits","savoiardi","espresso","eier","kakao"],
    "ingredients": [
      {"name":"Mascarpone","amount":250,"unit":"g","category":"milch","is_basic":False},
      {"name":"Löffelbiskuits (Savoiardi)","amount":12,"unit":"Stück","category":"sonstiges","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Zucker","amount":60,"unit":"g","category":"gewürze","is_basic":True},
      {"name":"Espresso (stark)","amount":150,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Kakaopulver","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Amaretto (optional)","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    ],
    "tips": "Löffelbiskuits nur kurz (1 Sek.) in Espresso tauchen – sie sollen noch einen Kern haben, nicht durchweicht sein.",
    "recipe_url": ""
  },
]

with open(RECIPES_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_ids = {r["id"] for r in data["recipes"]}
added = []
skipped = []

for r in NEW_RECIPES:
    if r["id"] in existing_ids:
        skipped.append(r["name"])
        continue
    data["recipes"].append(r)
    existing_ids.add(r["id"])
    added.append(r["name"])

if added:
    backup_path = RECIPES_PATH + ".backup2"
    shutil.copy2(RECIPES_PATH, backup_path)
    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ {len(added)} neue Rezepte hinzugefügt:")
    for name in added:
        print(f"  + {name}")
    print(f"Gesamt: {len(data['recipes'])} Rezepte")
else:
    print("Alle Rezepte bereits vorhanden.")

if skipped:
    print(f"Übersprungen (bereits vorhanden): {skipped}")
