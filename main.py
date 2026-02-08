import os


from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from starlette import status


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


class ProdModel(Base):
    __tablename__ = "products"

    product: Mapped[str]
    qty_stk: Mapped[int]


engine = create_engine(os.getenv("db_uri", "sqlite:///orders.db"))
Base.metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)


fixture_orders = [
    {
        "product": "Cloak of invisibility",
        "qty_stk": 1,
    },
    {
        "product": "Deluminator",
        "qty_stk": 2,
    },
]


with session_maker() as session:
    if not list(session.scalars(select(ProdModel))):
        products = [ProdModel(**order_details) for order_details in fixture_orders]
        session.add_all(products)
        session.commit()


app = FastAPI()


class PlaceProdSchema(BaseModel):
    product: str
    qty_stk: int


class GetProdSchema(PlaceProdSchema):
    id: int


class ListProdSchema(BaseModel):
    orders: list[GetProdSchema]


@app.get("/orders", response_model=ListProdSchema)
def list_orders():
    with session_maker() as session:
        orders = session.scalars(select(ProdModel))
        return {"orders": list(orders)}


@app.post(
    "/orders", response_model=GetProdSchema, status_code=status.HTTP_201_CREATED
)
def place_order(order_details: PlaceProdSchema):
    with session_maker() as session:
        prod = ProdModel(**order_details.model_dump())
        session.add(prod)
        session.commit()
        return {
            "id": prod.id,
            "product": prod.product,
            "qty_stk": prod.qty_stk,
        }
