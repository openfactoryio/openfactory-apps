from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    asset_uuid: str = Field(
        ...,
        description="Unique identifier of the asset in OpenFactory",
        example="TRIGGERS-APP"
    )
    uns_id: str = Field(
        ...,
        description="UNS (Unified Namespace) identifier representing the asset's logical location in the factory",
        example="factory/line1/robot1"
    )
    availability: str = Field(
        ...,
        description="Current availability state of the asset (e.g., AVAILABLE, UNAVAILABLE)",
        example="AVAILABLE"
    )
    type: str = Field(
        ...,
        description="Type of the asset as defined in OpenFactory (e.g., Device, OpenFactoryApp)",
        example="OpenFactoryApp"
    )


class AssetAttribute(BaseModel):
    id: str = Field(
        ...,
        description="Identifier of the attribute (e.g., avail, barcode, serialnumber)",
        example="avail"
    )
    value: str = Field(
        ...,
        description="Current value of the attribute",
        example="AVAILABLE"
    )
    type: str = Field(
        ...,
        description="Category of the attribute (e.g., Sample, Events, Condition)",
        example="Events"
    )
    tag: str = Field(
        ...,
        description="Semantic tag describing the attribute meaning",
        example="Availability"
    )
