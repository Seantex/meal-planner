#!/usr/bin/env python3
"""Fügt 30 hochwertige neue Rezepte zu recipes.json hinzu."""
import json, os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
RECIPES_PATH = os.path.join(BASE, "data", "recipes.json")

NEW_RECIPES = [
  {
    "id": "aglio_olio", "name": "Spaghetti Aglio e Olio", "description": "Klassiker der römischen Küche – goldener Knoblauch, Olivenöl und Peperoncino in perfekter Harmonie",
    "category": "pasta", "type": "weekday", "difficulty": "einfach",
    "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 18, "carbs": 82, "fat": 20},
    "tags": ["pasta","knoblauch","vegetarisch","schnell","italienisch"],
    "deal_keywords": ["spaghetti","nudeln","pasta","knoblauch","olivenöl","peperoncino"],
    "ingredients": [
      {"name":"Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Knoblauch","amount":6,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Peperoncino","amount":2,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Olivenöl extra vergine","amount":80,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Petersilie","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True},
      {"name":"Schwarzer Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Das Pasta-Kochwasser ist dein bester Freund – 2-3 EL davon in die Sauce geben macht sie samtig.",
    "recipe_url": ""
  },
  {
    "id": "cacio_e_pepe", "name": "Cacio e Pepe", "description": "Nur 3 Zutaten, aber eine der köstlichsten Pasten der Welt – Käse, Pfeffer und Pasta-Technik",
    "category": "pasta", "type": "weekday", "difficulty": "mittel",
    "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
    "nutrition_per_portion": {"calories": 650, "protein": 28, "carbs": 78, "fat": 24},
    "tags": ["pasta","käse","pfeffer","vegetarisch","römisch"],
    "deal_keywords": ["spaghetti","tonnarelli","pecorino","parmesan","schwarzer pfeffer"],
    "ingredients": [
      {"name":"Tonnarelli oder Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Pecorino Romano","amount":100,"unit":"g","category":"käse","is_basic":False},
      {"name":"Parmesan","amount":50,"unit":"g","category":"käse","is_basic":False},
      {"name":"Schwarzer Pfeffer (grob gemahlen)","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Käse immer vom Herd nehmen bevor er dazukommt – sonst klumpt er. Viel Pasta-Wasser bereithalten.",
    "recipe_url": ""
  },
  {
    "id": "penne_ricotta_spinat", "name": "Penne mit Ricotta und Spinat", "description": "Cremige Ricotta-Sauce mit frischem Spinat und Zitrone – leicht, schnell und unglaublich lecker",
    "category": "pasta", "type": "weekday", "difficulty": "einfach",
    "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 28, "carbs": 80, "fat": 18},
    "tags": ["pasta","spinat","ricotta","vegetarisch","schnell","cremig"],
    "deal_keywords": ["penne","nudeln","ricotta","spinat","zitrone","parmesan"],
    "ingredients": [
      {"name":"Penne","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Ricotta","amount":200,"unit":"g","category":"milch","is_basic":False},
      {"name":"Babyspinat","amount":150,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Zitrone (Abrieb und Saft)","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
      {"name":"Pinienkerne","amount":30,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Pinienkerne ohne Fett rösten bis sie goldbraun sind – das macht den ganzen Unterschied.",
    "recipe_url": ""
  },
  {
    "id": "teriyaki_haehnchen", "name": "Teriyaki-Hähnchen mit Jasminreis", "description": "Saftiges Hähnchen in glänzender Teriyaki-Glasur mit fluffigem Jasminreis – schnell und beeindruckend",
    "category": "geflügel", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 550, "protein": 42, "carbs": 68, "fat": 10},
    "tags": ["hähnchen","japanisch","reis","schnell","glasiert"],
    "deal_keywords": ["hähnchen","hühnerbrust","jasminreis","sojasoße","ingwer","honig","knoblauch"],
    "ingredients": [
      {"name":"Hähnchenbrust","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Jasminreis","amount":200,"unit":"g","category":"reis","is_basic":False},
      {"name":"Sojasoße","amount":60,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Honig","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Mirin","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Ingwer (frisch)","amount":2,"unit":"cm","category":"gemüse","is_basic":False},
      {"name":"Sesam","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True}
    ],
    "tips": "Hähnchen vor dem Anbraten flach klopfen – so gart es gleichmäßig und bleibt saftig.",
    "recipe_url": ""
  },
  {
    "id": "haehnchen_paprika", "name": "Hähnchenpfanne mit buntem Paprika", "description": "Aromatische Hähnchenpfanne mit rotem, gelbem und grünem Paprika in Tomaten-Weißwein-Sauce",
    "category": "geflügel", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 25, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 480, "protein": 44, "carbs": 22, "fat": 18},
    "tags": ["hähnchen","paprika","mediterran","schnell","gesund"],
    "deal_keywords": ["hähnchen","hühnerbrust","paprika","tomate","zwiebel","knoblauch","weißwein"],
    "ingredients": [
      {"name":"Hähnchenbrust","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Rote Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Gelbe Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Passierte Tomaten","amount":200,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Paprikapulver edelsüß","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Thymian","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Dazu passt Ciabatta zum Soßentunken perfekt.",
    "recipe_url": ""
  },
  {
    "id": "souvlaki", "name": "Souvlaki mit Pitabrot und Tzatziki", "description": "Griechische Schweinespieße mit selbstgemachtem Tzatziki, frischem Pitabrot und Tomaten",
    "category": "fleisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 15, "cook_time": 15, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 45, "carbs": 48, "fat": 24},
    "tags": ["schwein","griechisch","grill","spieß","pitabrot","tzatziki"],
    "deal_keywords": ["schweinefleisch","schweinefilet","pitabrot","joghurt","gurke","knoblauch","zitrone"],
    "ingredients": [
      {"name":"Schweinefilet","amount":350,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Pitabrot","amount":2,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Griechischer Joghurt","amount":200,"unit":"g","category":"milch","is_basic":False},
      {"name":"Gurke","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Tomaten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Rote Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Oregano","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Fleisch mindestens 30 Min. marinieren. Tzatziki eine Stunde vorher machen damit er zieht.",
    "recipe_url": ""
  },
  {
    "id": "koettbullar", "name": "Köttbullar mit Kartoffelpüree und Sahnesoße", "description": "Zarte schwedische Hackbällchen in cremiger Sahnesoße mit samtigem Kartoffelpüree",
    "category": "fleisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 15, "cook_time": 25, "total_time": 40, "servings": 2,
    "nutrition_per_portion": {"calories": 680, "protein": 38, "carbs": 52, "fat": 32},
    "tags": ["hack","schwedisch","kartoffeln","sahne","comfort food"],
    "deal_keywords": ["faschiertes","hackfleisch","kartoffeln","sahne","butter","zwiebel","senf"],
    "ingredients": [
      {"name":"Faschiertes (gemischt)","amount":350,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Kartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Sahne","amount":150,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Milch","amount":100,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Butter","amount":40,"unit":"g","category":"milch","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Ei","amount":1,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Semmelbrösel","amount":3,"unit":"EL","category":"brot","is_basic":False},
      {"name":"Senf","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
      {"name":"Rinderbrühe","amount":200,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Preiselbeeren","amount":None,"unit":"zum Servieren","category":"sonstiges","is_basic":False},
      {"name":"Salz, Pfeffer, Muskat","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Bällchen mit nassen Händen formen – so kleben sie nicht. Für extra Saftigkeit etwas Sahne ins Hack mischen.",
    "recipe_url": ""
  },
  {
    "id": "chili_con_carne", "name": "Chili con Carne mit Reis", "description": "Feurig-würziges Chili mit Hackfleisch, Kidneybohnen und Mais – perfektes Wohlfühlessen",
    "category": "fleisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 35, "total_time": 45, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 42, "carbs": 72, "fat": 18},
    "tags": ["hack","mexikanisch","bohnen","mais","scharf","reis"],
    "deal_keywords": ["faschiertes","hackfleisch","kidneybohnen","mais","tomate","paprika","chili","reis"],
    "ingredients": [
      {"name":"Faschiertes (Rind)","amount":300,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Kidneybohnen (Dose)","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Mais (Dose)","amount":1,"unit":"kleine Dose","category":"konserven","is_basic":False},
      {"name":"Gehackte Tomaten (Dose)","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Basmati-Reis","amount":180,"unit":"g","category":"reis","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Rote Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Chili (frisch oder Flocken)","amount":1,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Paprikapulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Sauerrahm","amount":None,"unit":"zum Servieren","category":"milch","is_basic":False},
      {"name":"Öl, Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Je länger das Chili köchelt, desto besser. Am nächsten Tag schmeckt es noch intensiver!",
    "recipe_url": ""
  },
  {
    "id": "garnelen_knoblauchbutter", "name": "Garnelen in Knoblauch-Kräuter-Butter mit Baguette", "description": "Saftige Garnelen in schäumender Knoblauchbutter mit frischen Kräutern – fertig in 15 Minuten",
    "category": "fisch", "type": "both", "difficulty": "einfach",
    "prep_time": 5, "cook_time": 10, "total_time": 15, "servings": 2,
    "nutrition_per_portion": {"calories": 420, "protein": 32, "carbs": 24, "fat": 22},
    "tags": ["garnelen","meeresfrüchte","knoblauch","butter","schnell","baguette"],
    "deal_keywords": ["garnelen","shrimps","meeresfrüchte","butter","baguette","knoblauch","petersilie"],
    "ingredients": [
      {"name":"Garnelen (TK, geschält)","amount":300,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Butter","amount":60,"unit":"g","category":"milch","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Baguette","amount":1,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Petersilie","amount":0.5,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Weißwein","amount":50,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Chili","amount":0.5,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Garnelen nur kurz anbraten (1-2 Min je Seite) – sie werden sonst gummiartig.",
    "recipe_url": ""
  },
  {
    "id": "poke_bowl_thunfisch", "name": "Thunfisch Poke Bowl mit Avocado und Edamame", "description": "Frische hawaiianische Bowl mit rohem Thunfisch, cremiger Avocado und Sesam-Dressing",
    "category": "fisch", "type": "both", "difficulty": "einfach",
    "prep_time": 20, "cook_time": 15, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 40, "carbs": 52, "fat": 22},
    "tags": ["thunfisch","bowlgerichte","hawaiianisch","gesund","avocado","roh"],
    "deal_keywords": ["thunfisch","sashimi","avocado","edamame","sojasauce","sesam","reis","gurke"],
    "ingredients": [
      {"name":"Sashimi-Thunfisch (frisch)","amount":250,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Sushi-Reis","amount":200,"unit":"g","category":"reis","is_basic":False},
      {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Edamame (TK)","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Gurke","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Sojasoße","amount":3,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Sesamöl","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Sesam","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
      {"name":"Sriracha","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
      {"name":"Ingwer (frisch)","amount":1,"unit":"cm","category":"gemüse","is_basic":False},
      {"name":"Reisessig","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Nur allerbesten Sashimi-Thunfisch verwenden – frisch vom Fischhändler oder Sushi-Qualität.",
    "recipe_url": ""
  },
  {
    "id": "fish_tacos", "name": "Fish Tacos mit Mango-Coleslaw", "description": "Knuspriger Fisch in Maistortillas mit frischem Mango-Kohl-Salat und Limetten-Crème",
    "category": "fisch", "type": "both", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 15, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 520, "protein": 34, "carbs": 56, "fat": 18},
    "tags": ["fisch","mexikanisch","tacos","mango","coleslaw","leicht"],
    "deal_keywords": ["weißfisch","kabeljau","dorsch","tilapia","maistortilla","mango","kohl","limette"],
    "ingredients": [
      {"name":"Weißfischfilet (Kabeljau/Tilapia)","amount":300,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Maistortillas","amount":4,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Mango","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Weißkohl","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Sauerrahm","amount":100,"unit":"g","category":"milch","is_basic":False},
      {"name":"Limetten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Koriander","amount":0.5,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Jalapeño","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kreuzkümmel","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Mehl","amount":50,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Fisch im Bierteig macht ihn extra knusprig. Coleslaw kann 1h vorher gemacht werden.",
    "recipe_url": ""
  },
  {
    "id": "lachs_senf_honig", "name": "Lachsfilet mit Senf-Honig-Kruste", "description": "Saftiges Lachsfilet mit knuspriger Senf-Honig-Kräuter-Kruste und Schmortomaten",
    "category": "fisch", "type": "both", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 510, "protein": 42, "carbs": 18, "fat": 28},
    "tags": ["lachs","backen","senf","honig","gesund","omega3"],
    "deal_keywords": ["lachs","lachsfilet","senf","honig","tomaten","zitrone","dill"],
    "ingredients": [
      {"name":"Lachsfilet","amount":400,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Senf (körnig)","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Honig","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Paniermehl","amount":30,"unit":"g","category":"brot","is_basic":False},
      {"name":"Cherrytomaten","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Dill (frisch)","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Butter","amount":20,"unit":"g","category":"milch","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Lachs nicht überkochen – er ist fertig wenn er sich beim leichten Druck leicht teilt (ca. 15 Min bei 180°C).",
    "recipe_url": ""
  },
  {
    "id": "kichererbsen_curry", "name": "Kichererbsen-Curry mit Kokosmilch und Spinat", "description": "Würziges, cremiges Curry mit knackigen Kichererbsen, Kokos und viel frischem Spinat",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 25, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 520, "protein": 18, "carbs": 68, "fat": 20},
    "tags": ["vegetarisch","vegan","curry","kichererbsen","indien","spinat","kokos"],
    "deal_keywords": ["kichererbsen","kokosmilch","spinat","tomate","ingwer","knoblauch","reis","curry"],
    "ingredients": [
      {"name":"Kichererbsen (Dose)","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Kokosmilch","amount":1,"unit":"Dose (400ml)","category":"konserven","is_basic":False},
      {"name":"Babyspinat","amount":150,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Gehackte Tomaten","amount":200,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Ingwer (frisch)","amount":3,"unit":"cm","category":"gemüse","is_basic":False},
      {"name":"Currypulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Garam Masala","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kurkuma","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Basmati-Reis","amount":180,"unit":"g","category":"reis","is_basic":False},
      {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Kichererbsen kurz anrösten bevor die Flüssigkeit dazukommt – gibt ein nussiges Aroma.",
    "recipe_url": ""
  },
  {
    "id": "tomatensuppe_cremig", "name": "Cremige Tomatensuppe mit Basilikum-Öl", "description": "Intensive, samtige Tomatensuppe aus Ofentomaten mit Sahne und frischem Basilikum-Öl",
    "category": "suppe", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 35, "total_time": 45, "servings": 2,
    "nutrition_per_portion": {"calories": 340, "protein": 7, "carbs": 30, "fat": 20},
    "tags": ["vegetarisch","suppe","tomate","cremig","basilikum","ofentomaten"],
    "deal_keywords": ["tomaten","cherrytomaten","sahne","basilikum","knoblauch","baguette"],
    "ingredients": [
      {"name":"Fleischtomaten","amount":800,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Cherrytomaten","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Sahne","amount":100,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Gemüsebrühe","amount":300,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Basilikum","amount":1,"unit":"Topf","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":60,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Balsamico","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Zucker","amount":1,"unit":"TL","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Tomaten zuerst im Ofen bei 180°C rösten – das intensiviert den Geschmack enorm.",
    "recipe_url": ""
  },
  {
    "id": "linsensuppe_rot", "name": "Rote Linsensuppe mit Paprika-Butter", "description": "Sättigende türkische Linsensuppe mit geröstetem Paprikapulver und einem Spritzer Zitrone",
    "category": "suppe", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 25, "total_time": 35, "servings": 2,
    "nutrition_per_portion": {"calories": 420, "protein": 22, "carbs": 62, "fat": 10},
    "tags": ["vegetarisch","vegan","suppe","linsen","türkisch","günstig"],
    "deal_keywords": ["rote linsen","karotte","zwiebel","knoblauch","tomate","gemüsebrühe","butter","paprikapulver"],
    "ingredients": [
      {"name":"Rote Linsen","amount":200,"unit":"g","category":"konserven","is_basic":False},
      {"name":"Karotten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Tomatenmark","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Gemüsebrühe","amount":1000,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Butter","amount":30,"unit":"g","category":"milch","is_basic":False},
      {"name":"Geräuchertes Paprikapulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Paprikabutter am Ende darüber geben macht den typischen türkischen Look und Geschmack.",
    "recipe_url": ""
  },
  {
    "id": "quesadillas_kaese", "name": "Käse-Quesadillas mit Avocado-Dip", "description": "Knusprige mexikanische Quesadillas mit geschmolzenem Käse, Paprika und hausgemachtem Guacamole",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 15, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 22, "carbs": 52, "fat": 32},
    "tags": ["vegetarisch","mexikanisch","käse","avocado","schnell","quesadillas"],
    "deal_keywords": ["tortilla","käse","mozzarella","avocado","paprika","tomaten","jalapeño"],
    "ingredients": [
      {"name":"Weizentortillas (groß)","amount":4,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Mozzarella","amount":150,"unit":"g","category":"käse","is_basic":False},
      {"name":"Cheddar","amount":100,"unit":"g","category":"käse","is_basic":False},
      {"name":"Rote Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Cherrytomaten","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Rote Zwiebel","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Jalapeño (aus dem Glas)","amount":4,"unit":"Scheiben","category":"konserven","is_basic":False},
      {"name":"Koriander","amount":None,"unit":"nach Belieben","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Butter statt Öl in der Pfanne macht die Quesadillas goldener und knuspriger.",
    "recipe_url": ""
  },
  {
    "id": "caprese_gnocchi", "name": "Caprese-Gnocchi aus der Pfanne", "description": "Knusprig gebratene Gnocchi mit Cherrytomaten, Mozzarella und Basilikum – fertig in 20 Minuten",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
    "nutrition_per_portion": {"calories": 560, "protein": 22, "carbs": 70, "fat": 20},
    "tags": ["vegetarisch","gnocchi","caprese","mozzarella","tomate","schnell"],
    "deal_keywords": ["gnocchi","mozzarella","cherrytomaten","basilikum","knoblauch","balsamico"],
    "ingredients": [
      {"name":"Gnocchi (frisch)","amount":500,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Mozzarella","amount":150,"unit":"g","category":"käse","is_basic":False},
      {"name":"Cherrytomaten","amount":250,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Basilikum","amount":1,"unit":"Topf","category":"gemüse","is_basic":False},
      {"name":"Balsamico-Creme","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Butter","amount":30,"unit":"g","category":"milch","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Gnocchi NICHT kochen – direkt trocken in der Pfanne anbraten bis sie goldbraun sind. Kein Kleben!",
    "recipe_url": ""
  },
  {
    "id": "sweet_potato_bowl", "name": "Süßkartoffel-Bowl mit Tahini und Kichererbsen", "description": "Nahrhafte Bowl mit gerösteten Süßkartoffeln, crispy Kichererbsen und cremigem Tahini-Dressing",
    "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 15, "cook_time": 30, "total_time": 45, "servings": 2,
    "nutrition_per_portion": {"calories": 540, "protein": 17, "carbs": 78, "fat": 20},
    "tags": ["vegetarisch","vegan","bowl","süßkartoffel","gesund","tahini","kichererbsen"],
    "deal_keywords": ["süßkartoffel","kichererbsen","tahini","spinat","avocado","granatapfel","sesam"],
    "ingredients": [
      {"name":"Süßkartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Kichererbsen (Dose)","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Tahini","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Babyspinat","amount":100,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Granatapfelkerne","amount":50,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":1,"unit":"Zehe","category":"gemüse","is_basic":False},
      {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Kichererbsen trocken tupfen und mit Paprika + Cumin rösten bis sie knusprig sind.",
    "recipe_url": ""
  },
  {
    "id": "zwiebelsuppe", "name": "Französische Zwiebelsuppe mit Gruyère-Kruste", "description": "Klassische, intensive Zwiebelsuppe mit karamellisierten Zwiebeln und überbackenem Käse",
    "category": "suppe", "type": "weekend", "difficulty": "mittel",
    "prep_time": 15, "cook_time": 60, "total_time": 75, "servings": 2,
    "nutrition_per_portion": {"calories": 480, "protein": 18, "carbs": 42, "fat": 24},
    "tags": ["suppe","französisch","zwiebel","käse","überbacken","comfort food"],
    "deal_keywords": ["zwiebeln","gruyère","emmentaler","baguette","rinderbrühe","weißwein","butter"],
    "ingredients": [
      {"name":"Zwiebeln","amount":800,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Rinderbrühe","amount":800,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Baguette","amount":4,"unit":"Scheiben","category":"brot","is_basic":False},
      {"name":"Gruyère","amount":120,"unit":"g","category":"käse","is_basic":False},
      {"name":"Trockener Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Butter","amount":40,"unit":"g","category":"milch","is_basic":False},
      {"name":"Thymian","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Lorbeerblatt","amount":1,"unit":"Stück","category":"gewürze","is_basic":False},
      {"name":"Cognac/Brandy","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Zucker","amount":1,"unit":"TL","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Zwiebeln 45 Min karamellisieren lassen – das ist das Geheimnis. Nicht beeilen!",
    "recipe_url": ""
  },
  {
    "id": "schweinsbraten_knödel", "name": "Schweinsbraten mit Semmelknödeln und Bratensauce", "description": "Saftiger österreichischer Schweinsbraten mit knuspriger Kruste und handgemachten Semmelknödeln",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 30, "cook_time": 120, "total_time": 150, "servings": 2,
    "nutrition_per_portion": {"calories": 780, "protein": 52, "carbs": 58, "fat": 35},
    "tags": ["schwein","österreichisch","braten","knödel","sonntagsessen","traditionell"],
    "deal_keywords": ["schweinsnacken","schweinskarree","schweinsschulter","semmeln","zwiebel","bier","knödel"],
    "ingredients": [
      {"name":"Schweinskarree","amount":600,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Semmeln (altbacken)","amount":3,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Milch","amount":150,"unit":"ml","category":"milch","is_basic":False},
      {"name":"Ei","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Zwiebel","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Dunkles Bier","amount":250,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Suppengemüse (Karotte, Sellerie)","amount":1,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Kümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Majoran","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Petersilie","amount":3,"unit":"EL","category":"gemüse","is_basic":False},
      {"name":"Öl, Salz, Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Fleisch 1h vorher aus dem Kühlschrank nehmen. Kruste einschneiden für mehr Knusprigkeit.",
    "recipe_url": ""
  },
  {
    "id": "pulled_pork_burger", "name": "Pulled Pork Burger mit Coleslaw", "description": "Unwiderstehlich zart gezogenes Schweinefleisch im Brioche-Bun mit cremigem Coleslaw",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 240, "total_time": 260, "servings": 2,
    "nutrition_per_portion": {"calories": 820, "protein": 52, "carbs": 62, "fat": 38},
    "tags": ["schwein","american bbq","burger","coleslaw","weekend","slow cook"],
    "deal_keywords": ["schweineschulter","schweinsschulter","brioche","weißkohl","bbq-soße","apfelessig"],
    "ingredients": [
      {"name":"Schweineschulter","amount":500,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Brioche-Buns","amount":2,"unit":"Stück","category":"brot","is_basic":False},
      {"name":"Weißkohl","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"BBQ-Soße","amount":4,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Apfelessig","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Mayonnaise","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Paprikapulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Knoblauchpulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Honig","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Salz, Pfeffer, Zucker","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Im Ofen bei 120°C 4-5h garen – je länger, desto zarter. Perfektes Meal-Prep für Reste!",
    "recipe_url": ""
  },
  {
    "id": "lammkoteletts", "name": "Lammkoteletts mit Rosmarin-Kartoffeln und Minz-Joghurt", "description": "Zartrosa gegrillte Lammkoteletts mit aromatischen Ofenkartoffeln und erfrischendem Minz-Dip",
    "category": "fleisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 20, "cook_time": 40, "total_time": 60, "servings": 2,
    "nutrition_per_portion": {"calories": 680, "protein": 48, "carbs": 38, "fat": 36},
    "tags": ["lamm","grill","rosmarin","kartoffeln","griechisch","weekend"],
    "deal_keywords": ["lammkoteletts","lammchops","kartoffeln","rosmarin","joghurt","minze","knoblauch","zitrone"],
    "ingredients": [
      {"name":"Lammkoteletts","amount":4,"unit":"Stück","category":"fleisch","is_basic":False},
      {"name":"Kartoffeln (festkochend)","amount":400,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Griechischer Joghurt","amount":150,"unit":"g","category":"milch","is_basic":False},
      {"name":"Frische Minze","amount":0.5,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Rosmarin","amount":4,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Thymian","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Lamm 30 Min mit Olivenöl, Knoblauch und Rosmarin marinieren. Medium-rare bei 62°C Kerntemperatur.",
    "recipe_url": ""
  },
  {
    "id": "sushi_bowl", "name": "Sushi Bowl mit Lachs und Mango", "description": "Alles was man an Sushi liebt – in Bowl-Form: Sushi-Reis, Lachs-Tataki, Avocado und Mango",
    "category": "fisch", "type": "weekend", "difficulty": "mittel",
    "prep_time": 25, "cook_time": 20, "total_time": 45, "servings": 2,
    "nutrition_per_portion": {"calories": 620, "protein": 38, "carbs": 70, "fat": 20},
    "tags": ["lachs","japanisch","bowl","avocado","mango","sushi","gesund"],
    "deal_keywords": ["lachsfilet","lachs","sushireis","avocado","mango","gurke","sojasoße","sesam","ingwer"],
    "ingredients": [
      {"name":"Sashimi-Lachsfilet","amount":250,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Sushi-Reis","amount":200,"unit":"g","category":"reis","is_basic":False},
      {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Mango","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Gurke","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Edamame (TK)","amount":80,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Reisessig","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Sojasoße","amount":3,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Sesamöl","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Noriblätter","amount":2,"unit":"Blätter","category":"sonstiges","is_basic":False},
      {"name":"Sesam","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
      {"name":"Eingelegter Ingwer","amount":None,"unit":"nach Belieben","category":"sonstiges","is_basic":False},
      {"name":"Wasabi","amount":None,"unit":"nach Belieben","category":"sonstiges","is_basic":False},
      {"name":"Zucker, Salz","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Lachs kurz von allen Seiten scharf anbraten (Tataki-Stil) oder roh servieren wenn Sashimi-Qualität.",
    "recipe_url": ""
  },
  {
    "id": "pad_see_ew", "name": "Pad See Ew (Thai-Nudeln mit Broccoli)", "description": "Rauchig-würzige thailändische Pfannudeln mit breiten Reisnudeln, Ei, Broccoli und Sojasoße",
    "category": "geflügel", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 15, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 580, "protein": 34, "carbs": 68, "fat": 16},
    "tags": ["thai","nudeln","hähnchen","wok","schnell","broccoli"],
    "deal_keywords": ["hähnchenbrust","reisnudeln","broccoli","ei","sojasoße","austernsoße","knoblauch"],
    "ingredients": [
      {"name":"Breite Reisnudeln","amount":200,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Hähnchenbrust","amount":250,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Broccoli","amount":200,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Helle Sojasoße","amount":3,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Dunkle Sojasoße","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Austernsoße","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Zucker","amount":1,"unit":"TL","category":"sonstiges","is_basic":True},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True}
    ],
    "tips": "Wok so heiß wie möglich erhitzen – das gibt den typischen Wok-Rauchgeschmack (Wok Hei).",
    "recipe_url": ""
  },
  {
    "id": "haehnchen_zitrone_kapern", "name": "Piccata-Hähnchen mit Kapern und Zitrone", "description": "Zartes Hähnchen in einer eleganten Zitrone-Kapern-Butter-Sauce – Restaurantqualität in 25 Min",
    "category": "geflügel", "type": "weekday", "difficulty": "mittel",
    "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
    "nutrition_per_portion": {"calories": 440, "protein": 44, "carbs": 12, "fat": 22},
    "tags": ["hähnchen","italienisch","kapern","zitrone","butter","schnell"],
    "deal_keywords": ["hähnchenbrust","kapern","zitrone","butter","weißwein","petersilie"],
    "ingredients": [
      {"name":"Hähnchenbrust","amount":400,"unit":"g","category":"fleisch","is_basic":False},
      {"name":"Kapern","amount":2,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Zitrone","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Butter","amount":50,"unit":"g","category":"milch","is_basic":False},
      {"name":"Weißwein","amount":80,"unit":"ml","category":"sonstiges","is_basic":False},
      {"name":"Hühnerbrühe","amount":100,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Mehl","amount":30,"unit":"g","category":"sonstiges","is_basic":False},
      {"name":"Petersilie","amount":0.5,"unit":"Bund","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Hähnchen flach klopfen und im Mehl wenden – so wird die Sauce cremiger.",
    "recipe_url": ""
  },
  {
    "id": "minestrone", "name": "Minestrone mit Parmesan-Croutons", "description": "Herzhafte italienische Gemüsesuppe mit Cannellini-Bohnen, Nudeln und knusprigen Parmesan-Croutons",
    "category": "suppe", "type": "weekday", "difficulty": "einfach",
    "prep_time": 15, "cook_time": 35, "total_time": 50, "servings": 2,
    "nutrition_per_portion": {"calories": 420, "protein": 18, "carbs": 62, "fat": 12},
    "tags": ["vegetarisch","suppe","italienisch","gemüse","bohnen","gesund"],
    "deal_keywords": ["cannellini-bohnen","tomate","zucchini","karotte","sellerie","nudeln","parmesan","gemüsebrühe"],
    "ingredients": [
      {"name":"Cannellini-Bohnen (Dose)","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Gehackte Tomaten","amount":1,"unit":"Dose (400g)","category":"konserven","is_basic":False},
      {"name":"Gemüsebrühe","amount":800,"unit":"ml","category":"konserven","is_basic":False},
      {"name":"Zucchini","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Karotten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Sellerie","amount":2,"unit":"Stangen","category":"gemüse","is_basic":False},
      {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Kleine Pasta (Ditali)","amount":80,"unit":"g","category":"nudeln","is_basic":False},
      {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
      {"name":"Basilikum","amount":5,"unit":"Blätter","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Olivenöl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Parmesan-Rinde mitkochen – das gibt unglaublich viel Umami-Geschmack.",
    "recipe_url": ""
  },
  {
    "id": "garnelen_fried_rice", "name": "Gebratener Garnelen-Reis mit Ei", "description": "Rauchiger asiatischer Fried Rice mit saftigen Garnelen, knackigem Gemüse und Ei",
    "category": "fisch", "type": "weekday", "difficulty": "einfach",
    "prep_time": 10, "cook_time": 15, "total_time": 25, "servings": 2,
    "nutrition_per_portion": {"calories": 520, "protein": 30, "carbs": 68, "fat": 14},
    "tags": ["garnelen","wok","reis","schnell","asiatisch","ei"],
    "deal_keywords": ["garnelen","shrimps","reis","ei","erbsen","karotte","sojasoße","frühlingszwiebeln"],
    "ingredients": [
      {"name":"Garnelen (TK, geschält)","amount":200,"unit":"g","category":"fisch","is_basic":False},
      {"name":"Gekochter Reis (vom Vortag)","amount":300,"unit":"g","category":"reis","is_basic":False},
      {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
      {"name":"Erbsen (TK)","amount":80,"unit":"g","category":"gemüse","is_basic":False},
      {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
      {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"gemüse","is_basic":False},
      {"name":"Sojasoße","amount":3,"unit":"EL","category":"konserven","is_basic":False},
      {"name":"Sesamöl","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
      {"name":"Ingwer","amount":1,"unit":"cm","category":"gemüse","is_basic":False},
      {"name":"Öl","amount":None,"unit":"nach Bedarf","category":"sonstiges","is_basic":True},
      {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":True}
    ],
    "tips": "Abgekühler Reis vom Vortag ist ideal – frischer Reis klebt zu sehr. Wok max. aufheizen!",
    "recipe_url": ""
  }
]

with open(RECIPES_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

existing_ids = {r["id"] for r in data["recipes"]}
added = []
for r in NEW_RECIPES:
    if r["id"] not in existing_ids:
        data["recipes"].append(r)
        existing_ids.add(r["id"])
        added.append(r["name"])

shutil.copy2(RECIPES_PATH, RECIPES_PATH + ".backup")
with open(RECIPES_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✓ {len(added)} neue Rezepte hinzugefügt:")
for n in added:
    print(f"  + {n}")
print(f"Gesamt: {len(data['recipes'])} Rezepte")
