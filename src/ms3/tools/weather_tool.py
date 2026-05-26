import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WeatherInfo:
    location: str
    temperature: float
    temperature_unit: str
    condition: str
    humidity: float
    wind_speed: float
    wind_direction: Optional[str] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    forecast: Optional[list] = None
    timestamp: datetime = datetime.now()


class WeatherTool:
    """
    天气查询工具
    """
    
    name = "get_weather"
    description = "查询指定城市的天气信息"
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openweathermap"):
        self.api_key = api_key
        self.provider = provider
    
    async def __call__(
        self,
        location: str,
        units: str = "metric",
        include_forecast: bool = True,
    ) -> WeatherInfo:
        logger.info(f"Getting weather for: {location}")
        
        try:
            if not self.api_key:
                logger.warning("No API key configured, returning mock weather")
                return self._get_mock_weather(location, units, include_forecast)
            
            if self.provider == "openweathermap":
                return await self._get_openweathermap_weather(location, units, include_forecast)
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return self._get_mock_weather(location, units, include_forecast)
                
        except Exception as e:
            logger.error(f"Weather query error: {e}")
            return self._get_mock_weather(location, units, include_forecast)
    
    def _get_mock_weather(
        self, location: str, units: str, include_forecast: bool
    ) -> WeatherInfo:
        temp_unit = "°C" if units == "metric" else "°F"
        base_temp = 22 if units == "metric" else 72
        
        forecast = None
        if include_forecast:
            forecast = [
                {"day": "明天", "temp": base_temp + 2, "condition": "多云"},
                {"day": "后天", "temp": base_temp - 1, "condition": "小雨"},
                {"day": "3天后", "temp": base_temp + 1, "condition": "晴"},
            ]
        
        return WeatherInfo(
            location=location,
            temperature=base_temp,
            temperature_unit=temp_unit,
            condition="晴",
            humidity=55.0,
            wind_speed=3.5,
            wind_direction="东北风",
            pressure=1013.0,
            visibility=10.0,
            forecast=forecast,
        )
    
    async def _get_openweathermap_weather(
        self, location: str, units: str, include_forecast: bool
    ) -> WeatherInfo:
        return self._get_mock_weather(location, units, include_forecast)
