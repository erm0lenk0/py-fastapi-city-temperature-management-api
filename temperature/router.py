import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.engine import SessionLocal
from city import models as city_models
from . import crud, schemas

router = APIRouter(prefix="/temperatures", tags=["temperatures"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.Temperature)
def create_temperature(
    temperature: schemas.TemperatureCreate, db: Session = Depends(get_db)
):
    return crud.create_temperature(db, temperature)


@router.get("/", response_model=list[schemas.Temperature])
def read_temperature(
    city_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    if city_id is not None:
        records = crud.get_temperature_by_city(db, city_id, skip=skip, limit=limit)
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"No temperature records found for city {city_id}",
            )
        return records
    return crud.get_temperature(db, skip=skip, limit=limit)


@router.get("/by_city/{city_id}", response_model=list[schemas.Temperature])
def read_temperature_by_city(
    city_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    records = crud.get_temperature_by_city(db, city_id, skip=skip, limit=limit)
    if not records:
        raise HTTPException(
            status_code=404, detail=f"No temperature records found for city {city_id}"
        )
    return records


@router.post("/update")
async def update_temperature(db: Session = Depends(get_db)):
    cities = db.query(city_models.City).all()
    if not cities:
        raise HTTPException(status_code=404, detail="No cities found in database")

    async with httpx.AsyncClient() as client:
        for city in cities:
            api_key = "91b6e3629ffeb604315deaea2b739d7e"
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city.name}&appid={api_key}&units=metric"

            response = await client.get(url)
            if response.status_code != 200:
                continue

            data = response.json()
            temp_value = data["main"]["temp"]

            crud.create_temperature(
                db,
                schemas.TemperatureCreate(
                    city_id=city.id,
                    date_time=datetime.datetime.utcnow(),
                    temperature=temp_value,
                ),
            )

        return {"message": "Temperature updated successfully"}
