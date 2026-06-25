from pydantic import BaseModel

from app.api.v1.schemas.regions import Region


class WeatherCurrent(BaseModel):
    temperature_2m: float
    weather_code: int
    precipitation_probability: int


class WeatherDaily(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    weather_code: int
    precipitation_probability_max: int


class WeatherForecast(BaseModel):
    region_code: str
    region: Region | None = None
    current: WeatherCurrent
    daily: list[WeatherDaily]
    cached: bool
