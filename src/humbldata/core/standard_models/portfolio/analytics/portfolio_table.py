
    """
    PortfolioTable Standard Model.

    Context: Portfolio || Category: Analytics || Command: PortfolioTable.

    This module is used to define the QueryParams and Data model for the
    PortfolioTable command.
    """

    from pydantic import BaseModel, Field, field_validator

    class PortfolioTableQueryParams(BaseModel):
        example_field: str = Field(..., description="An example field")

        @field_validator('example_field')
        def validate_example_field(cls, v):
            if len(v) < 3:
                raise ValueError("example_field must be at least 3 characters long")
            return v

    class PortfolioTableData(BaseModel):
        result: str = Field(..., description="The result of the PortfolioTable operation")
    