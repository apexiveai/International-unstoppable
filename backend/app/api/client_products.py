from fastapi import APIRouter

from app.services.product_access import PRODUCTS

router = APIRouter(

    prefix="/api/client",

    tags=["Client Products"],

)

@router.get("/products")

def get_client_products():

    return {

        "products": [

            {

                "product_key": key,

                "product_name": value["name"],

                "url": value["url"],

            }

            for key, value in PRODUCTS.items()

        ]

    }