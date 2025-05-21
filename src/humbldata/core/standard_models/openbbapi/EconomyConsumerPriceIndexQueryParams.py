import datetime as dt
from typing import Literal

from pydantic import Field

from humbldata.core.standard_models.abstract.query_params import QueryParams


class EconomyConsumerPriceIndexQueryParams(QueryParams):
    """
    QueryParams model for Consumer Price Index (CPI) data.

    Parameters
    ----------
    provider : str | None
        The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: fred, oecd.
    country : str | list[str]
        The country to get data. Multiple comma separated items allowed for provider(s): fred, oecd.
    transform : Literal['index', 'yoy', 'period']
        Transformation of the CPI data. Period represents the change since previous. Defaults to change from one year ago (yoy).
    frequency : Literal['annual', 'quarter', 'monthly']
        The frequency of the data.
    harmonized : bool | None
        If true, returns harmonized data.
    start_date : dt.date | str | None
        Start date of the data, in YYYY-MM-DD format.
    end_date : dt.date | str | None
        End date of the data, in YYYY-MM-DD format.
    expenditure : Literal['total', 'all', 'actual_rentals', 'alcoholic_beverages_tobacco_narcotics', 'all_non_food_non_energy', 'clothing_footwear', 'communication', 'education', 'electricity_gas_other_fuels', 'energy', 'overall_excl_energy_food_alcohol_tobacco', 'food_non_alcoholic_beverages', 'fuels_lubricants_personal', 'furniture_household_equipment', 'goods', 'housing', 'housing_excluding_rentals', 'housing_water_electricity_gas', 'health', 'imputed_rentals', 'maintenance_repair_dwelling', 'miscellaneous_goods_services', 'recreation_culture', 'residuals', 'restaurants_hotels', 'services_less_housing', 'services_less_house_excl_rentals', 'services', 'transport', 'water_supply_other_services'] | None
        Expenditure component of CPI. (provider: oecd)
    """

    provider: str | None = Field(
        default=None,
        description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: fred, oecd.",
    )
    country: str | list[str] = Field(
        default="united_states",
        description="The country to get data. Multiple comma separated items allowed for provider(s): fred, oecd.",
    )
    transform: Literal["index", "yoy", "period"] = Field(
        default="yoy",
        description="Transformation of the CPI data. Period represents the change since previous. Defaults to change from one year ago (yoy).",
    )
    frequency: Literal["annual", "quarter", "monthly"] = Field(
        default="monthly",
        description="The frequency of the data.",
    )
    harmonized: bool | None = Field(
        default=False,
        description="If true, returns harmonized data.",
    )
    start_date: dt.date | str | None = Field(
        default=None,
        description="Start date of the data, in YYYY-MM-DD format.",
    )
    end_date: dt.date | str | None = Field(
        default=None,
        description="End date of the data, in YYYY-MM-DD format.",
    )
    expenditure: (
        Literal[
            "total",
            "all",
            "actual_rentals",
            "alcoholic_beverages_tobacco_narcotics",
            "all_non_food_non_energy",
            "clothing_footwear",
            "communication",
            "education",
            "electricity_gas_other_fuels",
            "energy",
            "overall_excl_energy_food_alcohol_tobacco",
            "food_non_alcoholic_beverages",
            "fuels_lubricants_personal",
            "furniture_household_equipment",
            "goods",
            "housing",
            "housing_excluding_rentals",
            "housing_water_electricity_gas",
            "health",
            "imputed_rentals",
            "maintenance_repair_dwelling",
            "miscellaneous_goods_services",
            "recreation_culture",
            "residuals",
            "restaurants_hotels",
            "services_less_housing",
            "services_less_house_excl_rentals",
            "services",
            "transport",
            "water_supply_other_services",
        ]
        | None
    ) = Field(
        default="total",
        description="Expenditure component of CPI. (provider: oecd)",
    )
