class Item:
    def __init__(
            self,
            id: int,  # Артикул
            name: str,
            link: str,
            brand: str,
            regular_price: int,
            promo_price: int = None,
    ):
        self.id = id
        self.name = name
        self.link = link
        self.brand = brand
        self.regular_price = regular_price
        self.promo_price = promo_price

    def __str__(self):
        return (
            f"Id: {self.id} \n"
            f"Name: {self.name} \n"
            f"Link: {self.link} \n"
            f"Brand: {self.brand} \n"
            f"Regular price: {self.regular_price} \n"
            f"Promo price: {self.promo_price}"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "link": self.link,
            "brand": self.brand,
            "regular_price": self.regular_price,
            "promo_price": self.promo_price
        }
