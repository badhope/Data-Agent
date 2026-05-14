from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
import numpy as np
import math

logger = get_logger(__name__)

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result."""
    try:
        allowed_funcs = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'sqrt': math.sqrt,
            'abs': abs,
            'pow': pow,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }

        result = eval(expression, {"__builtins__": {}}, allowed_funcs)

        return f"🧮 Calculation Result:\n\n{expression} = {result}"
    except Exception as e:
        return f"❌ Calculation failed: {str(e)}"

@tool
def statistics(numbers: List[float]) -> str:
    """Calculate statistics for a list of numbers."""
    try:
        if not numbers:
            return "❌ Empty number list"

        arr = np.array(numbers)

        stats = {
            "count": len(numbers),
            "sum": np.sum(arr),
            "mean": np.mean(arr),
            "median": np.median(arr),
            "min": np.min(arr),
            "max": np.max(arr),
            "std": np.std(arr),
            "variance": np.var(arr),
        }

        output = "📊 Statistics Results:\n\n"
        for key, value in stats.items():
            output += f"• {key}: {value:.2f}\n"

        return output
    except Exception as e:
        return f"❌ Statistics calculation failed: {str(e)}"

@tool
def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another."""
    try:
        rates = {
            "USD": 1.0,
            "CNY": 7.24,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 154.0,
            "KRW": 1380.0,
            "AUD": 1.54,
            "CAD": 1.36,
        }

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)

        if not from_rate or not to_rate:
            available = ', '.join(rates.keys())
            return f"❌ Unsupported currency. Supported: {available}"

        result = (amount / from_rate) * to_rate

        return f"💱 Currency Conversion:\n\n{amount} {from_currency} = {result:.2f} {to_currency}"
    except Exception as e:
        return f"❌ Conversion failed: {str(e)}"

@tool
def date_diff(date1: str, date2: str, unit: str = "days") -> str:
    """Calculate the difference between two dates."""
    try:
        from langchain_office_assistant.utils.helpers import parse_date

        d1 = parse_date(date1)
        d2 = parse_date(date2)

        diff = abs((d2 - d1).days)

        units = {
            "days": diff,
            "weeks": diff / 7,
            "months": diff / 30.44,
            "years": diff / 365.25,
        }

        if unit not in units:
            return f"❌ Invalid unit. Supported: days, weeks, months, years"

        result = units[unit]

        return f"📅 Date Difference:\n\n{date1} ↔ {date2} = {result:.2f} {unit}"
    except Exception as e:
        return f"❌ Date calculation failed: {str(e)}"

@tool
def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value from one unit to another."""
    try:
        conversions = {
            "length": {
                "m": 1.0, "km": 0.001, "cm": 100.0, "mm": 1000.0,
                "in": 39.3701, "ft": 3.28084, "yd": 1.09361, "mi": 0.000621371
            },
            "weight": {
                "kg": 1.0, "g": 1000.0, "mg": 1000000.0,
                "lb": 2.20462, "oz": 35.274
            },
            "volume": {
                "l": 1.0, "ml": 1000.0, "gal": 0.264172, "qt": 1.05669
            }
        }

        unit_categories = {
            "m": "length", "km": "length", "cm": "length", "mm": "length",
            "in": "length", "ft": "length", "yd": "length", "mi": "length",
            "kg": "weight", "g": "weight", "mg": "weight", "lb": "weight", "oz": "weight",
            "l": "volume", "ml": "volume", "gal": "volume", "qt": "volume"
        }

        from_cat = unit_categories.get(from_unit.lower())
        to_cat = unit_categories.get(to_unit.lower())

        if not from_cat or not to_cat:
            return f"❌ Unsupported unit. Supported: length (m, km, cm, mm, in, ft, yd, mi), weight (kg, g, mg, lb, oz), volume (l, ml, gal, qt)"

        if from_cat != to_cat:
            return f"❌ Units must be in the same category"

        from_factor = conversions[from_cat][from_unit.lower()]
        to_factor = conversions[from_cat][to_unit.lower()]

        result = (value / from_factor) * to_factor

        return f"📏 Unit Conversion:\n\n{value} {from_unit} = {result:.4f} {to_unit}"
    except Exception as e:
        return f"❌ Conversion failed: {str(e)}"

class CalcPlugin(BasePlugin):
    name = "calc"
    description = "计算插件 - 公式计算、数据统计"

    def __init__(self):
        super().__init__()

    def initialize(self, config: Dict) -> None:
        self.config = config
        logger.info(f"CalcPlugin initialized")

    def get_tools(self) -> List:
        return [calculate, statistics, currency_convert, date_diff, unit_convert]

    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "calculate": calculate,
            "statistics": statistics,
            "currency_convert": currency_convert,
            "date_diff": date_diff,
            "unit_convert": unit_convert,
        }

        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"

        tool_func = tools_map[tool_name]
        return tool_func.invoke(kwargs)
