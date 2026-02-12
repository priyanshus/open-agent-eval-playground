from typing import Any, Callable

from tools.weather import get_weather_by_city

ToolFn = Callable[[dict[str, Any]], Any]


def _weather_tool_fn(ctx: dict[str, Any]) -> Any:
    city = ctx.get("city_name") or ctx.get("query", "").strip()
    return get_weather_by_city.invoke({"city_name": city})


TOOL_CATALOG: dict[str, ToolFn] = {
    "weather_tool": _weather_tool_fn,
}
