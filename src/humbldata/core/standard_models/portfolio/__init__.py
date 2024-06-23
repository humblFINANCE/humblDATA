
    """
    Context: Portfolio

    This module defines the standard models for the Portfolio context.
    """

    from pydantic import BaseModel, Field, field_validator

    class PortfolioQueryParams(BaseModel):
        example_field: str = Field(..., description="An example field")

        @field_validator('example_field')
        def validate_example_field(cls, v):
            if len(v) < 3:
                raise ValueError("example_field must be at least 3 characters long")
            return v

    class PortfolioData(BaseModel):
        result: str = Field(..., description="The result of the Portfolio operation")
    