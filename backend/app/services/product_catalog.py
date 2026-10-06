PRODUCT_CATALOG = [

    {

        "product_key": "trademark",
        "name": "Trademark Conflict",
        "slug": "trademark",
        "url": "https://trademark.apexiveai.com",

        "description": (
            "AI-powered trademark visual conflict "
            "and document analysis."
        ),
    },

    {

        "product_key": "workforce",
        "name": "Autonomous Workforce Agent",
        "slug": "workforce",

        "url": "https://workforce.apexiveai.com",
        "description": (
            "Autonomous enterprise workforce "
            "and governed agent execution."
        ),

    },

    {

        "product_key": "max_myanmar",
        "name": "MAX-MYANMAR",
        "slug": "max-myanmar",
        "url": "https://max.apexiveai.com",

        "description": (
            "MAX-MYANMAR operational intelligence "
            "platform."
        ),

    },

    {

        "product_key": "mna",

        "name": "MYANMAR NATIONAL AIRLINES",

        "slug": "mna",

        "url": "https://mna.apexiveai.com",

        "description": (

            "Myanmar National Airlines "

            "AI workforce and operations platform."

        ),

    },

]

def get_product(product_key: str):

    key = product_key.strip().lower()

    for product in PRODUCT_CATALOG:

        if product["product_key"] == key:

            return product

    return None

def get_all_products():

    return PRODUCT_CATALOG