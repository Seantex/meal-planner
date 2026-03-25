"""
Generiert die recipes.json Datenbank.
Ausführen mit: python3 generate_recipes.py
"""
import json, os

RECIPES = []

# ═══════════════════════════════════════════════════════════════
# PASTA – WOCHENTAG
# ═══════════════════════════════════════════════════════════════

RECIPES += [
{
  "id": "carbonara",
  "name": "Spaghetti Carbonara",
  "description": "Klassische römische Pasta mit cremiger Ei-Käse-Sauce und knusprigem Speck",
  "category": "pasta", "type": "weekday", "difficulty": "mittel",
  "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 680, "protein": 34, "carbs": 74, "fat": 26},
  "tags": ["pasta","speck","ei","käse","italienisch","schnell"],
  "deal_keywords": ["speck","pancetta","guanciale","bauchspeck","spaghetti","pasta","nudeln","pecorino","parmesan","eier"],
  "ingredients": [
    {"name":"Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Speck oder Pancetta","amount":150,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Eier (ganz)","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Eigelb","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Pecorino oder Parmesan","amount":80,"unit":"g","category":"käse","is_basic":False},
    {"name":"Schwarzer Pfeffer","amount":None,"unit":"nach Bedarf","category":"gewürze","is_basic":False},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1040121193626726/Spaghetti-Carbonara.html",
  "tips": "Pfanne vom Herd nehmen bevor die Eier dazukommen – sonst wird es Rührei!"
},
{
  "id": "bolognese",
  "name": "Spaghetti Bolognese",
  "description": "Herzhaftes Hackfleisch-Ragù nach Art von Bologna – ein absoluter Klassiker",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 35, "total_time": 50, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 42, "carbs": 78, "fat": 22},
  "tags": ["pasta","hackfleisch","tomate","italienisch","klassiker"],
  "deal_keywords": ["faschiertes","hackfleisch","rinderhack","gemischtes hack","spaghetti","pasta","nudeln","tomatensauce","tomaten","passata"],
  "ingredients": [
    {"name":"Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Faschiertes (Rind oder gemischt)","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Sellerie","amount":1,"unit":"Stange","category":"gemüse","is_basic":False},
    {"name":"Tomatenmark","amount":2,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Rotwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/495991140869613/Spaghetti-Bolognese.html",
  "tips": "Je länger das Ragù köchelt, desto besser. Gerne 45–60 Min wenn Zeit ist."
},
{
  "id": "arrabiata",
  "name": "Pasta all'Arrabbiata",
  "description": "Feurige Tomatensauce mit Chili und Knoblauch – schnell, günstig und super lecker",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 20, "total_time": 25, "servings": 2,
  "nutrition_per_portion": {"calories": 520, "protein": 16, "carbs": 88, "fat": 12},
  "tags": ["pasta","tomate","scharf","vegetarisch","schnell","günstig"],
  "deal_keywords": ["penne","pasta","nudeln","tomatensauce","passata","tomaten","chili"],
  "ingredients": [
    {"name":"Penne","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Chili (Flocken oder frisch)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/881401188398192/Pasta-all-arrabbiata.html",
  "tips": "Wer es milder mag einfach weniger Chili nehmen. Frische Petersilie drüber am Ende."
},
{
  "id": "pesto_pasta",
  "name": "Pasta al Pesto mit Kirschtomaten",
  "description": "Frisches Basilikum-Pesto mit bunten Kirschtomaten – fertig in 15 Minuten",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 12, "total_time": 17, "servings": 2,
  "nutrition_per_portion": {"calories": 610, "protein": 18, "carbs": 74, "fat": 28},
  "tags": ["pasta","pesto","tomate","vegetarisch","sehr schnell"],
  "deal_keywords": ["pesto","basilikum","kirschtomaten","pasta","nudeln","pinienkerne","parmesan"],
  "ingredients": [
    {"name":"Spaghetti oder Trofie","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Pesto (Glas oder frisch)","amount":120,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Kirschtomaten","amount":200,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Parmesan","amount":40,"unit":"g","category":"käse","is_basic":False},
    {"name":"Pinienkerne","amount":30,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"1 EL","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/289421095822038/Pasta-mit-Pesto-und-Kirschtomaten.html",
  "tips": "Etwas Pastawasser unter das Pesto mischen – das macht die Sauce samtig."
},
{
  "id": "tortellini_sahne",
  "name": "Tortellini in Sahne-Schinken-Sauce",
  "description": "Cremige Sahnesauce mit Schinken und Erbsen zu gekauften Tortellini",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 28, "carbs": 65, "fat": 38},
  "tags": ["pasta","sahne","schinken","schnell","cremig"],
  "deal_keywords": ["tortellini","schinken","kochschinken","sahne","obers","erbsen","parmesan"],
  "ingredients": [
    {"name":"Tortellini (gekauft)","amount":500,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Kochschinken","amount":150,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Sahne (Obers)","amount":200,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Tiefkühlerbsen","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Parmesan","amount":50,"unit":"g","category":"käse","is_basic":False},
    {"name":"Butter","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1065531195803327/Tortellini-in-Sahnesauce.html",
  "tips": "Sauce nicht zu lange kochen – Tortellini quellen sonst nach."
},
{
  "id": "lachs_pasta",
  "name": "Lachs-Pasta mit Sahne und Dill",
  "description": "Cremige Lachssauce mit frischem Dill – elegantes Abendessen in 25 Minuten",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 18, "total_time": 28, "servings": 2,
  "nutrition_per_portion": {"calories": 750, "protein": 38, "carbs": 72, "fat": 32},
  "tags": ["pasta","lachs","fisch","sahne","dill","schnell"],
  "deal_keywords": ["lachs","lachsfilet","räucherlachs","sahne","obers","dill","pasta","nudeln","tagliatelle"],
  "ingredients": [
    {"name":"Tagliatelle oder Spaghetti","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Lachsfilet","amount":300,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Sahne (Obers)","amount":200,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Frischer Dill","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Zitrone","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Weißwein","amount":50,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Butter","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1179801209456085/Pasta-mit-Lachssauce.html",
  "tips": "Lachs nicht zu lange braten – er sollte innen noch leicht rosa sein."
},
{
  "id": "thunfisch_pasta",
  "name": "Pasta mit Thunfisch und Kapern",
  "description": "Mediterrane Pasta mit Thunfisch, Kapern und Oliven – schnell und günstig",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 18, "total_time": 23, "servings": 2,
  "nutrition_per_portion": {"calories": 590, "protein": 36, "carbs": 75, "fat": 14},
  "tags": ["pasta","thunfisch","fisch","schnell","mediterran","günstig"],
  "deal_keywords": ["thunfisch","thunfischdose","kapern","oliven","pasta","nudeln","tomaten","passata"],
  "ingredients": [
    {"name":"Spaghetti oder Penne","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Thunfisch (Dose, Abtropfgewicht)","amount":160,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Passierte Tomaten","amount":300,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Kapern","amount":2,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Schwarze Oliven","amount":50,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Parmesan","amount":30,"unit":"g","category":"käse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/596221162568437/Pasta-al-Tonno.html",
  "tips": "Thunfisch erst am Ende einrühren – er soll nur warm werden, nicht zerfallen."
},
{
  "id": "amatriciana",
  "name": "Pasta all'Amatriciana",
  "description": "Würzige Tomatensauce mit Speck und Pecorino – rustikaler römischer Klassiker",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 8, "cook_time": 22, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 660, "protein": 28, "carbs": 76, "fat": 24},
  "tags": ["pasta","speck","tomate","römisch","italienisch"],
  "deal_keywords": ["speck","pancetta","guanciale","bauchspeck","rigatoni","bucatini","pasta","nudeln","pecorino","tomaten","passata"],
  "ingredients": [
    {"name":"Rigatoni oder Bucatini","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Speck oder Pancetta","amount":150,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Pecorino Romano","amount":60,"unit":"g","category":"käse","is_basic":False},
    {"name":"Chili (Flocken)","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Weißwein","amount":50,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1494011247434534/Pasta-all-Amatriciana.html",
  "tips": "Kein Knoblauch – das ist das Originalrezept! Speck in Streifen, nicht gewürfelt."
},
{
  "id": "gnocchi_gorgonzola",
  "name": "Gnocchi mit Gorgonzola-Walnuss-Sauce",
  "description": "Samtige Gorgonzolasauce mit gerösteten Walnüssen – fertig in 20 Minuten",
  "category": "pasta", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 15, "total_time": 20, "servings": 2,
  "nutrition_per_portion": {"calories": 740, "protein": 22, "carbs": 68, "fat": 42},
  "tags": ["gnocchi","käse","gorgonzola","vegetarisch","cremig","schnell"],
  "deal_keywords": ["gnocchi","gorgonzola","blauschimmelkäse","walnüsse","sahne","obers","parmesan"],
  "ingredients": [
    {"name":"Gnocchi (fertig)","amount":500,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Gorgonzola","amount":120,"unit":"g","category":"käse","is_basic":False},
    {"name":"Sahne (Obers)","amount":100,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Walnüsse","amount":50,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Parmesan","amount":30,"unit":"g","category":"käse","is_basic":False},
    {"name":"Frischer Salbei","amount":4,"unit":"Blätter","category":"gewürze","is_basic":False},
    {"name":"Butter","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1286811221021284/Gnocchi-mit-Gorgonzola-Sauce.html",
  "tips": "Walnüsse kurz ohne Fett rösten – gibt Aroma. Sauce nicht zu stark erhitzen."
},
]

# ═══════════════════════════════════════════════════════════════
# FLEISCH – WOCHENTAG
# ═══════════════════════════════════════════════════════════════

RECIPES += [
{
  "id": "schnitzel_kartoffelsalat",
  "name": "Schnitzel mit Kartoffelsalat",
  "description": "Knuspriges paniertes Schnitzel mit warmem Wiener Kartoffelsalat",
  "category": "fleisch", "type": "weekday", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 20, "total_time": 40, "servings": 2,
  "nutrition_per_portion": {"calories": 780, "protein": 52, "carbs": 58, "fat": 34},
  "tags": ["schnitzel","schwein","kartoffel","österreichisch","klassiker"],
  "deal_keywords": ["schnitzel","schweineschnitzel","putenschnitzel","kalbsschnitzel","kartoffeln","erdäpfel","semmelbrösel","panier"],
  "ingredients": [
    {"name":"Schweine- oder Putenschnitzel","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Semmelbrösel","amount":80,"unit":"g","category":"brot","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Mehl","amount":4,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Senf","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Weißweinessig","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Sonnenblumenöl","amount":None,"unit":"reichlich","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/673451170499789/Wiener-Schnitzel.html",
  "tips": "Schnitzel dünn klopfen und in reichlich Öl schwimmend braten – nicht pressen!"
},
{
  "id": "burger",
  "name": "Hausgemachter Burger",
  "description": "Saftiger selbstgemachter Burger mit frischen Beilagen und Cheddar",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 20, "total_time": 35, "servings": 2,
  "nutrition_per_portion": {"calories": 820, "protein": 48, "carbs": 56, "fat": 42},
  "tags": ["burger","hackfleisch","amerikanisch","käse","schnell"],
  "deal_keywords": ["faschiertes","hackfleisch","rinderhack","burgerbrot","burgerbrötchen","cheddar","käse","speck","bacon","salat","tomate"],
  "ingredients": [
    {"name":"Faschiertes (Rind)","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Burgerbrötchen","amount":2,"unit":"Stück","category":"brot","is_basic":False},
    {"name":"Cheddar","amount":4,"unit":"Scheiben","category":"käse","is_basic":False},
    {"name":"Salat","amount":4,"unit":"Blätter","category":"gemüse","is_basic":False},
    {"name":"Tomate","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Gewürzgurken","amount":4,"unit":"Scheiben","category":"konserven","is_basic":False},
    {"name":"Ketchup & Mayonnaise","amount":None,"unit":"nach Belieben","category":"sonstiges","is_basic":False},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1039731193537622/American-Burger.html",
  "tips": "Patty nur einmal wenden – nicht drücken! Käse direkt drauf wenn noch heiß."
},
{
  "id": "gyros",
  "name": "Gyros mit Tzatziki und Pommes",
  "description": "Würziges Gyrosfleisch mit selbstgemachtem Tzatziki und Ofen-Pommes",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 20, "cook_time": 25, "total_time": 45, "servings": 2,
  "nutrition_per_portion": {"calories": 760, "protein": 46, "carbs": 52, "fat": 38},
  "tags": ["gyros","schwein","griechisch","tzatziki","pommes"],
  "deal_keywords": ["schweinefleisch","schweineschulter","gyros","joghurt","gurke","kartoffeln","erdäpfel","paprikapulver"],
  "ingredients": [
    {"name":"Schweineschulter oder -nacken","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln (für Pommes)","amount":400,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Griechischer Joghurt","amount":200,"unit":"g","category":"milch","is_basic":False},
    {"name":"Salatgurke","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Paprikapulver (edelsüß)","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Kreuzkümmel","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zitrone","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/720851176048374/Gyros-vom-Blech.html",
  "tips": "Fleisch mind. 1h marinieren. Pommes bei 220°C knusprig backen."
},
{
  "id": "chicken_tikka",
  "name": "Chicken Tikka Masala mit Reis",
  "description": "Cremiges indisches Curry mit zartem Hähnchenfleisch – mild und aromatisch",
  "category": "fleisch", "type": "weekday", "difficulty": "mittel",
  "prep_time": 15, "cook_time": 30, "total_time": 45, "servings": 2,
  "nutrition_per_portion": {"calories": 680, "protein": 48, "carbs": 65, "fat": 22},
  "tags": ["curry","hähnchen","indisch","kokosmilch","reis","exotisch"],
  "deal_keywords": ["hähnchenbrust","hühnerbrust","kokosmilch","tomaten","passata","reis","currypulver","ingwer","garam masala"],
  "ingredients": [
    {"name":"Hähnchenbrust","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Basmati-Reis","amount":180,"unit":"g","category":"reis","is_basic":False},
    {"name":"Kokosmilch","amount":200,"unit":"ml","category":"konserven","is_basic":False},
    {"name":"Passierte Tomaten","amount":200,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Currypulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Garam Masala","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Ingwer (frisch oder Pulver)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Joghurt","amount":100,"unit":"g","category":"milch","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1040281193649108/Chicken-Tikka-Masala.html",
  "tips": "Hähnchen vorher in Joghurt und Gewürzen marinieren – macht es zart und aromatisch."
},
{
  "id": "tacos",
  "name": "Tacos mit Hackfleisch und Guacamole",
  "description": "Mexikanische Tacos mit würzigem Hackfleisch, Guacamole und frischen Toppings",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 20, "total_time": 35, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 38, "carbs": 58, "fat": 34},
  "tags": ["tacos","hackfleisch","mexikanisch","avocado","schnell"],
  "deal_keywords": ["faschiertes","hackfleisch","avocado","tortilla","tacoshells","mais","bohnen","cheddar","sauerrahm"],
  "ingredients": [
    {"name":"Taco-Shells oder Weizentortillas","amount":6,"unit":"Stück","category":"brot","is_basic":False},
    {"name":"Faschiertes (Rind)","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Mais (Dose)","amount":100,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Kidney-Bohnen (Dose)","amount":100,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Cheddar (gerieben)","amount":80,"unit":"g","category":"käse","is_basic":False},
    {"name":"Sauerrahm","amount":100,"unit":"g","category":"milch","is_basic":False},
    {"name":"Tomaten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Taco-Gewürz oder Kreuzkümmel","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/802621183154695/Tacos-mit-Hackfleisch.html",
  "tips": "Avocado erst kurz vor dem Servieren zerdrücken, sonst wird sie braun."
},
{
  "id": "pfeffersteak",
  "name": "Pfeffersteak mit Ofenkartoffeln",
  "description": "Saftiges Rindersteak mit cremiger Pfeffersauce und knusprigen Ofenkartoffeln",
  "category": "fleisch", "type": "weekday", "difficulty": "mittel",
  "prep_time": 10, "cook_time": 35, "total_time": 45, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 54, "carbs": 44, "fat": 36},
  "tags": ["steak","rind","kartoffel","sahnesauce","französisch"],
  "deal_keywords": ["rindersteak","entrecote","hüftsteak","rumpsteak","steak","kartoffeln","sahne","obers","pfeffer"],
  "ingredients": [
    {"name":"Rindersteak (je ca. 200g)","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Sahne (Obers)","amount":150,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Grüner Pfeffer (Glas)","amount":1,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Brandy oder Cognac (optional)","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Rosmarin","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/688351172299567/Steak-mit-Pfeffersauce.html",
  "tips": "Steak 30 Min vor dem Braten aus dem Kühlschrank nehmen. Nach dem Braten 5 Min ruhen lassen."
},
{
  "id": "haehnchen_curry",
  "name": "Hähnchen-Curry mit Kokosmilch",
  "description": "Aromatisches Thai-Curry mit Hähnchen, Gemüse und Jasminreis",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 25, "total_time": 40, "servings": 2,
  "nutrition_per_portion": {"calories": 650, "protein": 44, "carbs": 60, "fat": 24},
  "tags": ["curry","hähnchen","thai","kokosmilch","reis","scharf"],
  "deal_keywords": ["hähnchenbrust","hühnerbrust","kokosmilch","currypaste","ingwer","paprika","reis","zucchini"],
  "ingredients": [
    {"name":"Hähnchenbrust","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kokosmilch","amount":400,"unit":"ml","category":"konserven","is_basic":False},
    {"name":"Rote Currypaste","amount":2,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Jasminreis","amount":180,"unit":"g","category":"reis","is_basic":False},
    {"name":"Paprika (rot)","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zucchini","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Frischer Ingwer","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Fischsauce","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1197951211843940/Thai-Curry-mit-Haehnchen.html",
  "tips": "Currypaste kurz in Öl anrösten bevor Kokosmilch dazu kommt – das verstärkt das Aroma."
},
{
  "id": "cevapcici",
  "name": "Cevapcici mit Djuvec-Reis",
  "description": "Balkanische Hackfleischröllchen mit würzigem Paprika-Gemüse-Reis",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 20, "cook_time": 25, "total_time": 45, "servings": 2,
  "nutrition_per_portion": {"calories": 680, "protein": 40, "carbs": 60, "fat": 26},
  "tags": ["cevapcici","hackfleisch","balkan","reis","paprika"],
  "deal_keywords": ["faschiertes","hackfleisch","rinderhack","lammhack","paprika","paprikapulver","reis","zwiebel","aivar"],
  "ingredients": [
    {"name":"Faschiertes (Rind/Lamm gemischt)","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Langkornreis","amount":160,"unit":"g","category":"reis","is_basic":False},
    {"name":"Paprika (rot und grün)","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zwiebel","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tomaten (Dose)","amount":200,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Paprikapulver (geräuchert)","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Ajvar (Paprikamark)","amount":2,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Sauerrahm","amount":100,"unit":"g","category":"milch","is_basic":False},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1010071190939034/Cevapcici.html",
  "tips": "Hackfleisch gut kneten und mind. 30 Min kühl rasten lassen. Dann formen sie sich besser."
},
{
  "id": "haehnchen_wraps",
  "name": "Hähnchen-Wraps mit Avocado",
  "description": "Frische Wraps mit gegrilltem Hähnchen, Avocado, Salat und Joghurt-Sauce",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 15, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 620, "protein": 42, "carbs": 52, "fat": 24},
  "tags": ["wraps","hähnchen","avocado","frisch","leicht","schnell"],
  "deal_keywords": ["hähnchenbrust","hühnerbrust","tortilla","wraps","avocado","joghurt","salat","tomate","paprika"],
  "ingredients": [
    {"name":"Hähnchenbrust","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Weizentortillas (groß)","amount":4,"unit":"Stück","category":"brot","is_basic":False},
    {"name":"Avocado","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Griechischer Joghurt","amount":150,"unit":"g","category":"milch","is_basic":False},
    {"name":"Salat (gemischt)","amount":80,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Tomate","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Rote Zwiebel","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1286341220973180/Haehnchen-Wraps.html",
  "tips": "Hähnchen in dünne Streifen schneiden und heiß in der Pfanne scharf anbraten."
},
{
  "id": "nasi_goreng",
  "name": "Nasi Goreng",
  "description": "Indonesischer gebratener Reis mit Hähnchen, Ei und Gemüse",
  "category": "fleisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 620, "protein": 36, "carbs": 72, "fat": 18},
  "tags": ["reis","hähnchen","asiatisch","ei","scharf","schnell"],
  "deal_keywords": ["hähnchenbrust","hühnerbrust","reis","eier","sojasoße","sambal","frühlingszwiebeln","koriander"],
  "ingredients": [
    {"name":"Gekochter Reis (Vortag)","amount":300,"unit":"g","category":"reis","is_basic":False},
    {"name":"Hähnchenbrust","amount":200,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Sojasoße","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Sambal Oelek","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tiefkühlerbsen","amount":80,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Sesamöl","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1078921197280956/Nasi-Goreng.html",
  "tips": "Vortagsreis funktioniert am besten – frischer Reis wird matschig."
},
{
  "id": "rindergeschnetzeltes",
  "name": "Züricher Geschnetzeltes mit Rösti",
  "description": "Zartes Rindgeschnetzeltes in Champignon-Sahnesauce mit knusprigem Rösti",
  "category": "fleisch", "type": "weekday", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 25, "total_time": 45, "servings": 2,
  "nutrition_per_portion": {"calories": 760, "protein": 48, "carbs": 52, "fat": 38},
  "tags": ["rind","geschnetzeltes","champignons","schweizer","rösti","sahne"],
  "deal_keywords": ["rindsfleisch","rindsfilet","kalbsfilet","champignons","pilze","sahne","obers","kartoffeln","weißwein"],
  "ingredients": [
    {"name":"Rindsfilet oder -lende","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Champignons","amount":250,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Sahne (Obers)","amount":200,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Kartoffeln (für Rösti)","amount":500,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Butter","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/789511181816026/Zuercher-Geschnetzeltes.html",
  "tips": "Fleisch in sehr heißer Pfanne scharf anbraten – nicht mehr als 2 Min sonst wird es zäh."
},
]

# ═══════════════════════════════════════════════════════════════
# FISCH – WOCHENTAG
# ═══════════════════════════════════════════════════════════════

RECIPES += [
{
  "id": "lachs_reis",
  "name": "Lachs mit Reis und Brokkoli",
  "description": "Gebratenes Lachsfilet mit Basmatireis und gedünstetem Brokkoli – ausgewogen und proteinreich",
  "category": "fisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 22, "total_time": 32, "servings": 2,
  "nutrition_per_portion": {"calories": 580, "protein": 48, "carbs": 52, "fat": 18},
  "tags": ["lachs","fisch","reis","brokkoli","gesund","proteinreich"],
  "deal_keywords": ["lachs","lachsfilet","lachssteak","brokkoli","reis","basmati","zitrone","dill"],
  "ingredients": [
    {"name":"Lachsfilet","amount":350,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Basmati-Reis","amount":180,"unit":"g","category":"reis","is_basic":False},
    {"name":"Brokkoli","amount":300,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Sojasauce","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Honig","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":1,"unit":"Zehe","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1157921207680916/Lachs-mit-Reis-und-Brokkoli.html",
  "tips": "Lachs mit Honig-Sojasoße glasieren – gibt eine schöne Kruste in der Pfanne."
},
{
  "id": "fischfilet_kartoffeln",
  "name": "Gegrilltes Fischfilet mit Kräuterbutter und Kartoffeln",
  "description": "Zartes Fischfilet mit selbstgemachter Kräuterbutter und Petersilkartoffeln",
  "category": "fisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 15, "cook_time": 22, "total_time": 37, "servings": 2,
  "nutrition_per_portion": {"calories": 540, "protein": 42, "carbs": 40, "fat": 22},
  "tags": ["fisch","fischfilet","kräuterbutter","kartoffel","leicht"],
  "deal_keywords": ["fischfilet","seelachs","tilapia","pangasius","dorsch","kabeljau","forelle","kartoffeln","butter","petersilie","zitrone"],
  "ingredients": [
    {"name":"Fischfilet (Seelachs oder Dorsch)","amount":350,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Kartoffeln","amount":450,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Butter (weich)","amount":60,"unit":"g","category":"milch","is_basic":False},
    {"name":"Petersilie (frisch)","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Semmelbrösel","amount":2,"unit":"EL","category":"brot","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":1,"unit":"Zehe","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/773841180254516/Fischfilet-mit-Kraeuterbutter.html",
  "tips": "Fisch mit Semmelbröseln panieren und in Butter goldbraun braten – gibt tolle Kruste."
},
{
  "id": "garnelen_curry",
  "name": "Garnelen-Curry mit Jasminreis",
  "description": "Würziges Kokosmilch-Curry mit saftigen Garnelen und duftendem Jasminreis",
  "category": "fisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 560, "protein": 36, "carbs": 62, "fat": 18},
  "tags": ["garnelen","curry","kokosmilch","reis","thai","meeresfrüchte"],
  "deal_keywords": ["garnelen","crevetten","shrimps","kokosmilch","currypaste","jasminreis","reis","zitronengras","limette"],
  "ingredients": [
    {"name":"Garnelen (roh, geschält)","amount":300,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Jasminreis","amount":180,"unit":"g","category":"reis","is_basic":False},
    {"name":"Kokosmilch","amount":400,"unit":"ml","category":"konserven","is_basic":False},
    {"name":"Rote Currypaste","amount":2,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Paprika (rot)","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zucchini","amount":0.5,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Frischer Koriander","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Fischsauce","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1141211205874548/Garnelen-Curry.html",
  "tips": "Garnelen nur 2–3 Min garen – sobald sie rosa werden, sind sie fertig."
},
]

# ═══════════════════════════════════════════════════════════════
# EIER / VEGETARISCH – WOCHENTAG
# ═══════════════════════════════════════════════════════════════

RECIPES += [
{
  "id": "shakshuka",
  "name": "Shakshuka",
  "description": "Nordafrikanische Eier in würziger Tomatensauce – deftig, schnell und besonders",
  "category": "eier", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 20, "total_time": 30, "servings": 2,
  "nutrition_per_portion": {"calories": 420, "protein": 22, "carbs": 28, "fat": 24},
  "tags": ["eier","tomate","vegetarisch","schnell","nordeafrikanisch","deftig"],
  "deal_keywords": ["eier","tomaten","passata","paprika","feta","brot","chili"],
  "ingredients": [
    {"name":"Eier","amount":4,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Paprika (rot)","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Feta","amount":80,"unit":"g","category":"käse","is_basic":False},
    {"name":"Paprikapulver (geräuchert)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Chili","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Brot (zum Dippen)","amount":4,"unit":"Scheiben","category":"brot","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1567801260609543/Shakshuka.html",
  "tips": "Eier in Mulden in der Sauce geben und mit Deckel stocken lassen – Eigelb soll noch cremig sein."
},
{
  "id": "palatschinken_herzhaft",
  "name": "Herzhafte Palatschinken mit Schinken und Käse",
  "description": "Dünne Palatschinken gefüllt mit Schinken, Käse und frischen Kräutern",
  "category": "eier", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 25, "total_time": 35, "servings": 2,
  "nutrition_per_portion": {"calories": 560, "protein": 30, "carbs": 48, "fat": 26},
  "tags": ["palatschinken","eier","schinken","käse","österreichisch","herzhaft"],
  "deal_keywords": ["eier","schinken","kochschinken","käse","gouda","milch","mehl","sahne"],
  "ingredients": [
    {"name":"Eier","amount":3,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Milch","amount":250,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Kochschinken","amount":150,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Gouda oder Emmentaler (gerieben)","amount":120,"unit":"g","category":"käse","is_basic":False},
    {"name":"Schnittlauch","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Sauerrahm","amount":100,"unit":"g","category":"milch","is_basic":False},
    {"name":"Mehl","amount":120,"unit":"g","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"1 Prise","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1168061208785164/Herzhafte-Palatschinken.html",
  "tips": "Teig mind. 20 Min rasten lassen. Pfanne gut vorheizen für gleichmäßige Palatschinken."
},
{
  "id": "palatschinken_suess",
  "name": "Palatschinken mit Nutella und Früchten",
  "description": "Klassische dünne Palatschinken mit Nutella, frischen Früchten und Staubzucker",
  "category": "eier", "type": "weekday", "difficulty": "einfach",
  "prep_time": 5, "cook_time": 20, "total_time": 25, "servings": 2,
  "nutrition_per_portion": {"calories": 580, "protein": 14, "carbs": 82, "fat": 22},
  "tags": ["palatschinken","süß","nutella","früchte","österreichisch","dessert"],
  "deal_keywords": ["eier","milch","nutella","erdbeeren","banane","heidelbeeren","staubzucker","schlagobers"],
  "ingredients": [
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Milch","amount":250,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Nutella oder Marmelade","amount":4,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Erdbeeren oder Banane","amount":200,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Staubzucker","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Mehl","amount":120,"unit":"g","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"1 Prise","category":"basics","is_basic":True},
    {"name":"Zucker","amount":1,"unit":"TL","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1213961213668584/Palatschinken.html",
  "tips": "Teig sehr dünn in der Pfanne verteilen. Mit Schlagobers und frischen Beeren servieren."
},
{
  "id": "fried_rice",
  "name": "Gebratener Reis mit Ei und Gemüse",
  "description": "Klassischer asiatischer gebratener Reis – schnell, günstig und befriedigend",
  "category": "vegetarisch", "type": "weekday", "difficulty": "einfach",
  "prep_time": 10, "cook_time": 18, "total_time": 28, "servings": 2,
  "nutrition_per_portion": {"calories": 480, "protein": 18, "carbs": 76, "fat": 14},
  "tags": ["reis","ei","vegetarisch","asiatisch","schnell","günstig"],
  "deal_keywords": ["reis","eier","sojasoße","karotte","tiefkühlgemüse","frühlingszwiebeln","sesam"],
  "ingredients": [
    {"name":"Gekochter Reis (Vortag)","amount":300,"unit":"g","category":"reis","is_basic":False},
    {"name":"Eier","amount":3,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tiefkühlerbsen","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Sojasoße","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Sesamöl","amount":1,"unit":"TL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Ingwer","amount":1,"unit":"TL","category":"gewürze","is_basic":False}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1114161201930688/Gebratener-Reis.html",
  "tips": "Kalter Vortagsreis ist Pflicht – frischer Reis wird klebrig."
},
{
  "id": "risotto_parmesan",
  "name": "Parmesan-Risotto mit frischen Kräutern",
  "description": "Cremiges Risotto mit reichlich Parmesan und frischen Kräutern – simpel und köstlich",
  "category": "vegetarisch", "type": "weekday", "difficulty": "mittel",
  "prep_time": 5, "cook_time": 35, "total_time": 40, "servings": 2,
  "nutrition_per_portion": {"calories": 620, "protein": 20, "carbs": 78, "fat": 24},
  "tags": ["risotto","parmesan","vegetarisch","cremig","italienisch"],
  "deal_keywords": ["risottoreis","arborio","parmesan","pecorino","weißwein","gemüsesuppe","butter"],
  "ingredients": [
    {"name":"Risotto-Reis (Arborio)","amount":200,"unit":"g","category":"reis","is_basic":False},
    {"name":"Parmesan (frisch gerieben)","amount":100,"unit":"g","category":"käse","is_basic":False},
    {"name":"Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Gemüsesuppe","amount":700,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Frische Kräuter (Basilikum/Petersilie)","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Butter","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/853221186629716/Parmesan-Risotto.html",
  "tips": "Heiße Brühe löffelweise zugeben und ständig rühren – das macht Risotto cremig."
},
]

# ═══════════════════════════════════════════════════════════════
# WOCHENEND-REZEPTE
# ═══════════════════════════════════════════════════════════════

RECIPES += [
{
  "id": "pizza",
  "name": "Selbstgemachte Pizza",
  "description": "Hausgemachte Pizza mit knusprigem Boden, Tomatensoße und Lieblings-Toppings",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 40, "cook_time": 15, "total_time": 90, "servings": 2,
  "nutrition_per_portion": {"calories": 780, "protein": 34, "carbs": 96, "fat": 28},
  "tags": ["pizza","teig","italienisch","wochenende","mozzarella","klassiker"],
  "deal_keywords": ["mozzarella","pizzakäse","salami","schinken","kochschinken","passata","tomatensauce","mehl","hefe","paprika","champignons","pizza"],
  "ingredients": [
    {"name":"Weizenmehl (Typ 00 oder 405)","amount":320,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Hefe (frisch oder Trockenhefe)","amount":7,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Mozzarella","amount":250,"unit":"g","category":"käse","is_basic":False},
    {"name":"Passierte Tomaten","amount":200,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Salami oder Schinken","amount":100,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Champignons","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Salz & Zucker","amount":None,"unit":"je 1 TL","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/971941190255494/Pizzateig-der-beste.html",
  "tips": "Teig mind. 30 Min gehen lassen. Ofen auf max. Temperatur (250°C) vorheizen – inklusive Blech!"
},
{
  "id": "lasagne",
  "name": "Lasagne Bolognese",
  "description": "Hausgemachte Lasagne mit saftigem Hackfleisch-Ragù und cremiger Béchamel",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 45, "cook_time": 45, "total_time": 90, "servings": 2,
  "nutrition_per_portion": {"calories": 860, "protein": 52, "carbs": 72, "fat": 38},
  "tags": ["lasagne","hackfleisch","béchamel","italienisch","wochenende","auflauf"],
  "deal_keywords": ["faschiertes","hackfleisch","lasagneplatten","nudelplatten","passata","tomaten","parmesan","mozzarella","milch","sahne"],
  "ingredients": [
    {"name":"Lasagneplatten (keine Vorkochzeit)","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Faschiertes (Rind oder gemischt)","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Milch","amount":500,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Parmesan (gerieben)","amount":80,"unit":"g","category":"käse","is_basic":False},
    {"name":"Mozzarella","amount":150,"unit":"g","category":"käse","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Karotte","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tomatenmark","amount":2,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Rotwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Mehl","amount":3,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz, Pfeffer & Muskatnuss","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/752501177965416/Lasagne.html",
  "tips": "Ragù mind. 30 Min köcheln lassen. Letzte Schicht großzügig mit Béchamel und Parmesan bedecken."
},
{
  "id": "brathaehnchen",
  "name": "Knuspriges Brathähnchen mit Ofengemüse",
  "description": "Ganzes Hähnchen aus dem Ofen mit Kräuterbutter und buntem Ofengemüse",
  "category": "fleisch", "type": "weekend", "difficulty": "einfach",
  "prep_time": 20, "cook_time": 75, "total_time": 95, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 58, "carbs": 32, "fat": 38},
  "tags": ["hähnchen","brathähnchen","ofen","gemüse","knusprig","wochenende"],
  "deal_keywords": ["ganzes hähnchen","brathähnchen","hähnchen","karotte","kartoffeln","zucchini","paprika","rosmarin","thymian"],
  "ingredients": [
    {"name":"Hähnchen (ganz, ca. 1.2kg)","amount":1200,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln","amount":400,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Paprika","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zucchini","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Karotte","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Rosmarin","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Thymian","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Butter","amount":60,"unit":"g","category":"milch","is_basic":False},
    {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1039671193530450/Knuspriges-Brathaehnchen.html",
  "tips": "Kräuterbutter unter die Haut schieben. Letzte 15 Min auf Oberhitze für knusprige Kruste."
},
{
  "id": "gulasch",
  "name": "Rindergulasch mit Semmelknödeln",
  "description": "Saftiges österreichisches Rindergulasch mit hausgemachten Semmelknödeln",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 30, "cook_time": 90, "total_time": 120, "servings": 2,
  "nutrition_per_portion": {"calories": 840, "protein": 56, "carbs": 68, "fat": 32},
  "tags": ["gulasch","rind","österreichisch","schmorenfleisch","semmelknödel","wochenende"],
  "deal_keywords": ["rindfleisch","rindsgulasch","rindsbrust","zwiebel","paprikapulver","semmel","semmeln","eier","milch"],
  "ingredients": [
    {"name":"Rinderbrust oder Schulter","amount":500,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Zwiebel","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Paprikapulver (edelsüß)","amount":3,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Tomatenmark","amount":1,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Rindssuppe","amount":400,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Semmel (altbacken)","amount":4,"unit":"Stück","category":"brot","is_basic":False},
    {"name":"Milch","amount":200,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Petersilie","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Kümmel","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Majoran","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/700511173641765/Rindergulasch.html",
  "tips": "Zwiebel goldbraun anrösten bis karamelisiert – das gibt Farbe und Geschmack. Mind. 90 Min schmoren."
},
{
  "id": "beef_stroganoff",
  "name": "Beef Stroganoff mit Bandnudeln",
  "description": "Zartes Rindfleisch in cremiger Senf-Sahnesauce mit Champignons und Bandnudeln",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 30, "total_time": 50, "servings": 2,
  "nutrition_per_portion": {"calories": 780, "protein": 50, "carbs": 64, "fat": 34},
  "tags": ["rind","sahne","russisch","nudeln","champignons","cremig"],
  "deal_keywords": ["rindsfilet","rindfleisch","lende","champignons","pilze","sahne","obers","senf","bandnudeln","pasta"],
  "ingredients": [
    {"name":"Rindsfilet oder -lende","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Bandnudeln (Pappardelle)","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Champignons","amount":250,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Sahne (Obers)","amount":200,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Sauerrahm","amount":100,"unit":"g","category":"milch","is_basic":False},
    {"name":"Senf (mittelscharf)","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Paprikapulver","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"1 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/753621178094774/Beef-Stroganoff.html",
  "tips": "Fleisch in sehr heißer Pfanne kurz scharf anbraten – nicht durchgaren. Sauce separat zubereiten."
},
{
  "id": "pasta_al_forno",
  "name": "Pasta al Forno (Nudelauflauf)",
  "description": "Üppiger Pasta-Auflauf mit Hackfleisch, Béchamel und goldbrauner Käsekruste",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 30, "cook_time": 45, "total_time": 75, "servings": 2,
  "nutrition_per_portion": {"calories": 880, "protein": 48, "carbs": 84, "fat": 38},
  "tags": ["auflauf","hackfleisch","pasta","käse","béchamel","wochenende"],
  "deal_keywords": ["faschiertes","hackfleisch","rigatoni","penne","pasta","nudeln","parmesan","mozzarella","milch","passata"],
  "ingredients": [
    {"name":"Rigatoni oder Penne","amount":250,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Faschiertes (Rind oder gemischt)","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Passierte Tomaten","amount":300,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Milch","amount":400,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Mozzarella","amount":150,"unit":"g","category":"käse","is_basic":False},
    {"name":"Parmesan (gerieben)","amount":60,"unit":"g","category":"käse","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Mehl","amount":3,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz, Pfeffer & Muskat","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1111691201570756/Pasta-al-Forno.html",
  "tips": "Nudeln leicht unter al dente kochen – sie garen im Ofen nach. Großzügig Käse oben drauf!"
},
{
  "id": "chicken_parmigiana",
  "name": "Chicken Parmigiana",
  "description": "Paniertes Hähnchenschnitzel mit Tomatensauce und geschmolzenem Mozzarella",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 25, "cook_time": 35, "total_time": 60, "servings": 2,
  "nutrition_per_portion": {"calories": 760, "protein": 58, "carbs": 52, "fat": 34},
  "tags": ["hähnchen","mozzarella","tomate","paniert","italienisch","amerikanisch"],
  "deal_keywords": ["hähnchenbrust","hühnerbrust","mozzarella","passata","tomatensauce","parmesan","semmelbrösel","eier"],
  "ingredients": [
    {"name":"Hähnchenbrust (2 Stück, dünn)","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Mozzarella","amount":200,"unit":"g","category":"käse","is_basic":False},
    {"name":"Passierte Tomaten","amount":300,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Parmesan (gerieben)","amount":60,"unit":"g","category":"käse","is_basic":False},
    {"name":"Semmelbrösel","amount":80,"unit":"g","category":"brot","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Frisches Basilikum","amount":10,"unit":"Blätter","category":"gewürze","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Mehl","amount":3,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"4 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1578631261839590/Chicken-Parmigiana.html",
  "tips": "Hähnchen dünn klopfen. In Öl anbraten, dann mit Sauce und Käse im Ofen bei 200°C überbacken."
},
{
  "id": "paella",
  "name": "Paella mit Hähnchen und Meeresfrüchten",
  "description": "Spanische Paella mit saftigem Hähnchen, Garnelen und aromatischem Safranreis",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 45, "total_time": 65, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 52, "carbs": 68, "fat": 22},
  "tags": ["paella","hähnchen","garnelen","reis","spanisch","safran","wochenende"],
  "deal_keywords": ["hähnchen","garnelen","crevetten","risottoreis","rundkornreis","safran","paprika","chorizo","erbsen","meeresfrüchte"],
  "ingredients": [
    {"name":"Hähnchenschenkel oder -brust","amount":300,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Garnelen (roh)","amount":200,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Paella-Reis oder Arborio","amount":200,"unit":"g","category":"reis","is_basic":False},
    {"name":"Safranfäden","amount":0.5,"unit":"g","category":"gewürze","is_basic":False},
    {"name":"Paprika (rot)","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tomaten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tiefkühlerbsen","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Chorizo (optional)","amount":80,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Hühnerbrühe","amount":500,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Paprikapulver (geräuchert)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1004511189929538/Paella.html",
  "tips": "Safran in warmem Wasser einweichen. Reis nach dem Einrühren NICHT mehr rühren – das macht die Socarrat (Kruste)."
},
{
  "id": "pad_thai",
  "name": "Pad Thai mit Garnelen",
  "description": "Traditioneller thai. Wok-Nudeln mit Garnelen, Ei, Erdnüssen und Tamarindensauce",
  "category": "fisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 20, "total_time": 40, "servings": 2,
  "nutrition_per_portion": {"calories": 640, "protein": 36, "carbs": 74, "fat": 22},
  "tags": ["pad thai","garnelen","nudeln","thai","erdnüsse","wok"],
  "deal_keywords": ["garnelen","crevetten","shrimps","reisnudeln","erdnüsse","sojasprossen","eier","tamarinde","fischsauce","limette"],
  "ingredients": [
    {"name":"Reisnudeln (flach)","amount":200,"unit":"g","category":"nudeln","is_basic":False},
    {"name":"Garnelen (roh, geschält)","amount":250,"unit":"g","category":"fisch","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Sojasprossen","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Erdnüsse (geröstet)","amount":60,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Frühlingszwiebeln","amount":3,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Tamarindenpaste","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Fischsauce","amount":2,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Palmzucker oder brauner Zucker","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Limette","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Chili (frisch oder Flocken)","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1108441201112420/Pad-Thai.html",
  "tips": "Nudeln nur einweichen, nicht kochen. Sehr hohe Hitze im Wok für authentisches Aroma."
},
{
  "id": "enchiladas",
  "name": "Enchiladas mit Hackfleisch",
  "description": "Gefüllte mexikanische Tortillas mit Hackfleisch, überbacken mit Enchilada-Sauce und Käse",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 25, "cook_time": 35, "total_time": 60, "servings": 2,
  "nutrition_per_portion": {"calories": 820, "protein": 48, "carbs": 68, "fat": 36},
  "tags": ["enchiladas","hackfleisch","mexikanisch","käse","wochenende","auflauf"],
  "deal_keywords": ["faschiertes","hackfleisch","tortilla","weizentortilla","cheddar","käse","mais","bohnen","tomaten","sauerrahm"],
  "ingredients": [
    {"name":"Weizentortillas (mittel)","amount":6,"unit":"Stück","category":"brot","is_basic":False},
    {"name":"Faschiertes (Rind)","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Cheddar oder Gouda (gerieben)","amount":200,"unit":"g","category":"käse","is_basic":False},
    {"name":"Kidneybohnen (Dose)","amount":200,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Mais (Dose)","amount":150,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Passierte Tomaten","amount":400,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Sauerrahm","amount":150,"unit":"g","category":"milch","is_basic":False},
    {"name":"Paprikapulver","amount":2,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Kreuzkümmel","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":2,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1024071191786428/Enchiladas.html",
  "tips": "Tortillas vor dem Füllen kurz in der Pfanne erwärmen – so lassen sie sich besser rollen."
},
{
  "id": "moussaka",
  "name": "Moussaka",
  "description": "Griechischer Auberginen-Auflauf mit Hackfleisch-Ragù und cremiger Béchamel",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 40, "cook_time": 50, "total_time": 90, "servings": 2,
  "nutrition_per_portion": {"calories": 780, "protein": 44, "carbs": 42, "fat": 48},
  "tags": ["moussaka","aubergine","hackfleisch","griechisch","béchamel","wochenende"],
  "deal_keywords": ["faschiertes","hackfleisch","lammhack","aubergine","kartoffeln","tomaten","passata","parmesan","milch","zimt"],
  "ingredients": [
    {"name":"Auberginen","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Faschiertes (Lamm oder Rind)","amount":350,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln","amount":300,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Passierte Tomaten","amount":300,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Milch","amount":400,"unit":"ml","category":"milch","is_basic":False},
    {"name":"Parmesan oder Kefalotiri","amount":60,"unit":"g","category":"käse","is_basic":False},
    {"name":"Ei","amount":1,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Zwiebel","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Zimt","amount":0.5,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Oregano","amount":1,"unit":"TL","category":"gewürze","is_basic":False},
    {"name":"Mehl","amount":3,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"4 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/748231177493030/Moussaka.html",
  "tips": "Auberginen gesalzen 15 Min ziehen lassen, dann abspülen – so werden sie nicht bitter."
},
{
  "id": "wiener_schnitzel_gross",
  "name": "Wiener Schnitzel mit Petersilkartoffeln",
  "description": "Das perfekte Wiener Schnitzel – dünn, knusprig und aufgeschäumt in Butter",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 25, "cook_time": 30, "total_time": 55, "servings": 2,
  "nutrition_per_portion": {"calories": 820, "protein": 56, "carbs": 60, "fat": 38},
  "tags": ["schnitzel","kalb","wiener","österreichisch","butter","knusprig","klassiker"],
  "deal_keywords": ["kalbsschnitzel","kalbfleisch","schnitzel","semmelbrösel","panier","kartoffeln","butter","zitrone","petersilie","eier"],
  "ingredients": [
    {"name":"Kalbsschnitzel (je ca. 180g)","amount":360,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Semmelbrösel","amount":120,"unit":"g","category":"brot","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Kartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Petersilie (frisch)","amount":0.5,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Butterschmalz oder Pflanzenöl","amount":None,"unit":"reichlich","category":"sonstiges","is_basic":False},
    {"name":"Mehl","amount":4,"unit":"EL","category":"basics","is_basic":True},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/748481177495998/Echtes-Wiener-Schnitzel.html",
  "tips": "Schnitzel auf 4mm klopfen. In reichlich Fett schwimmend braten und die Pfanne schwenken – so wellt sich die Panier auf."
},
{
  "id": "lammchops",
  "name": "Lammkoteletts mit Rosmarinkartoffeln",
  "description": "Zartes Lammkotelett mit Knoblauch und Rosmarin, dazu Rosmarin-Ofenkartoffeln",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 20, "cook_time": 35, "total_time": 55, "servings": 2,
  "nutrition_per_portion": {"calories": 720, "protein": 50, "carbs": 38, "fat": 40},
  "tags": ["lamm","koteletts","rosmarin","kartoffel","mediterran","wochenende"],
  "deal_keywords": ["lammkoteletts","lammchops","lamm","lammfleisch","rosmarin","kartoffeln","thymian","zitrone","knoblauch"],
  "ingredients": [
    {"name":"Lammkoteletts (4 Stück)","amount":400,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Kartoffeln","amount":500,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Rosmarin","amount":4,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Thymian","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Zitrone","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Dijon-Senf","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"4 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":4,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1029971192345252/Lammkoteletts-mit-Rosmarin.html",
  "tips": "Lamm mind. 30 Min bei Zimmertemperatur akklimatisieren. Medium (rosa) bei 60°C Kerntemperatur."
},
{
  "id": "risotto_funghi",
  "name": "Risotto ai Funghi (Pilzrisotto)",
  "description": "Cremiges Pilzrisotto mit getrockneten Steinpilzen und frischen Champignons",
  "category": "vegetarisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 15, "cook_time": 40, "total_time": 55, "servings": 2,
  "nutrition_per_portion": {"calories": 640, "protein": 20, "carbs": 80, "fat": 26},
  "tags": ["risotto","pilze","champignons","vegetarisch","cremig","wochenende"],
  "deal_keywords": ["risottoreis","arborio","champignons","pilze","steinpilze","waldpilze","parmesan","weißwein","butter","sahne"],
  "ingredients": [
    {"name":"Risotto-Reis (Arborio)","amount":200,"unit":"g","category":"reis","is_basic":False},
    {"name":"Champignons","amount":300,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Getrocknete Steinpilze","amount":20,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Parmesan (gerieben)","amount":80,"unit":"g","category":"käse","is_basic":False},
    {"name":"Weißwein","amount":100,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Gemüsesuppe","amount":700,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Thymian","amount":2,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Schalotten","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Butter","amount":None,"unit":"4 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1053481194932072/Pilzrisotto.html",
  "tips": "Steinpilze 20 Min in warmem Wasser einweichen, Wasser zum Kochen verwenden. Langsam und mit Liebe rühren."
},
{
  "id": "bibimbap",
  "name": "Bibimbap (Koreanische Reisschüssel)",
  "description": "Bunte koreanische Reisschüssel mit mariniertem Rindfleisch, Gemüse und Gochujang-Sauce",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 30, "cook_time": 30, "total_time": 60, "servings": 2,
  "nutrition_per_portion": {"calories": 660, "protein": 42, "carbs": 72, "fat": 22},
  "tags": ["bibimbap","koreanisch","reis","rind","gemüse","ei","asiatisch"],
  "deal_keywords": ["rindfleisch","rindslende","reis","eier","karotte","spinat","zucchini","sojasoße","sesamöl","gochujang"],
  "ingredients": [
    {"name":"Rundkornreis","amount":200,"unit":"g","category":"reis","is_basic":False},
    {"name":"Rindfleisch (Lende, in Streifen)","amount":250,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Eier","amount":2,"unit":"Stück","category":"eier","is_basic":False},
    {"name":"Karotte","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Spinat (frisch)","amount":100,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Zucchini","amount":1,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Gochujang (korean. Chilipaste)","amount":2,"unit":"EL","category":"gewürze","is_basic":False},
    {"name":"Sojasoße","amount":3,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Sesamöl","amount":2,"unit":"TL","category":"sonstiges","is_basic":False},
    {"name":"Sesam","amount":1,"unit":"EL","category":"sonstiges","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Zucker","amount":1,"unit":"TL","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1456001242914604/Bibimbap.html",
  "tips": "Jedes Gemüse separat würzen und anbraten. Das Ei kommt als Spiegel obenauf – Eigelb soll fließen."
},
{
  "id": "coq_au_vin",
  "name": "Coq au Vin",
  "description": "Klassisches französisches Hähnchen in Rotwein geschmort mit Champignons und Speck",
  "category": "fleisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 25, "cook_time": 65, "total_time": 90, "servings": 2,
  "nutrition_per_portion": {"calories": 680, "protein": 52, "carbs": 22, "fat": 34},
  "tags": ["hähnchen","rotwein","champignons","speck","französisch","schmoren"],
  "deal_keywords": ["hähnchenschenkel","hähnchen","champignons","pilze","speck","speckwürfel","rotwein","schalotten","thymian","lorbeer"],
  "ingredients": [
    {"name":"Hähnchenschenkel (4 Stück)","amount":800,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Rotwein (kräftig)","amount":300,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Champignons","amount":200,"unit":"g","category":"gemüse","is_basic":False},
    {"name":"Speckwürfel","amount":100,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Schalotten","amount":6,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Hühnerbrühe","amount":200,"unit":"ml","category":"sonstiges","is_basic":False},
    {"name":"Thymian","amount":3,"unit":"Zweige","category":"gewürze","is_basic":False},
    {"name":"Lorbeerblätter","amount":2,"unit":"Stück","category":"gewürze","is_basic":False},
    {"name":"Tomatenmark","amount":1,"unit":"EL","category":"konserven","is_basic":False},
    {"name":"Butter","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Knoblauch","amount":3,"unit":"Zehen","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/878341188126710/Coq-au-Vin.html",
  "tips": "Hähnchen gut anbraten bis goldbraun. Rotwein vollständig reduzieren lassen bevor Brühe dazu kommt."
},
{
  "id": "pizza_margherita",
  "name": "Pizza Margherita",
  "description": "Klassische Pizza mit Tomatensauce, Mozzarella und frischem Basilikum",
  "category": "vegetarisch", "type": "weekend", "difficulty": "mittel",
  "prep_time": 35, "cook_time": 15, "total_time": 90, "servings": 2,
  "nutrition_per_portion": {"calories": 680, "protein": 26, "carbs": 92, "fat": 22},
  "tags": ["pizza","vegetarisch","mozzarella","tomate","basilikum","italienisch"],
  "deal_keywords": ["mozzarella","pizzakäse","passata","tomatensauce","mehl","hefe","basilikum","pizza"],
  "ingredients": [
    {"name":"Weizenmehl (Typ 00)","amount":320,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Hefe","amount":7,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Mozzarella (Büffel oder Fior di Latte)","amount":250,"unit":"g","category":"käse","is_basic":False},
    {"name":"Passierte Tomaten","amount":200,"unit":"g","category":"konserven","is_basic":False},
    {"name":"Frisches Basilikum","amount":1,"unit":"Bund","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"3 EL","category":"basics","is_basic":True},
    {"name":"Salz & Zucker","amount":None,"unit":"je 1 TL","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1017981191239576/Pizza-Margherita.html",
  "tips": "Ofen auf 250°C mit Blech vorheizen. Mozzarella gut abtropfen lassen – sonst wird die Pizza wässrig."
},
{
  "id": "flammkuchen",
  "name": "Flammkuchen mit Speck und Zwiebeln",
  "description": "Knuspriger elsässischer Flammkuchen mit Sauerrahm, Speck und Zwiebeln",
  "category": "fleisch", "type": "weekend", "difficulty": "einfach",
  "prep_time": 25, "cook_time": 15, "total_time": 55, "servings": 2,
  "nutrition_per_portion": {"calories": 660, "protein": 22, "carbs": 72, "fat": 32},
  "tags": ["flammkuchen","speck","sauerrahm","elsässisch","knusprig","wochenende"],
  "deal_keywords": ["speck","bauchspeck","räucherspeck","sauerrahm","crème fraîche","zwiebel","mehl","hefe"],
  "ingredients": [
    {"name":"Mehl","amount":250,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Speck (in Streifen)","amount":150,"unit":"g","category":"fleisch","is_basic":False},
    {"name":"Sauerrahm oder Crème fraîche","amount":200,"unit":"g","category":"milch","is_basic":False},
    {"name":"Zwiebel","amount":2,"unit":"Stück","category":"gemüse","is_basic":False},
    {"name":"Trockenhefe","amount":3,"unit":"g","category":"sonstiges","is_basic":False},
    {"name":"Muskatnuss","amount":None,"unit":"1 Prise","category":"gewürze","is_basic":False},
    {"name":"Olivenöl","amount":None,"unit":"2 EL","category":"basics","is_basic":True},
    {"name":"Salz & Pfeffer","amount":None,"unit":"nach Bedarf","category":"basics","is_basic":True}
  ],
  "recipe_url": "https://www.chefkoch.de/rezepte/1193761212350592/Flammkuchen.html",
  "tips": "Teig hauchdünn ausrollen. Ofen auf 250°C maximal aufheizen – Flammkuchen soll in 12 Min fertig sein."
},
]

# ═══════════════════════════════════════════════════════════════
# Datei schreiben
# ═══════════════════════════════════════════════════════════════

out_path = os.path.join(os.path.dirname(__file__), "data", "recipes.json")
os.makedirs(os.path.dirname(out_path), exist_ok=True)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"recipes": RECIPES}, f, ensure_ascii=False, indent=2)

print(f"✅ {len(RECIPES)} Rezepte geschrieben nach: {out_path}")
