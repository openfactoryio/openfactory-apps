from fastapi import APIRouter, Request
from typing import List
from openfactory import OpenFactory
from openfactory.assets import Asset
from models import AssetResponse, AssetAttribute

router = APIRouter(tags=["OpenFactoryAPI"])


@router.get(
    "/api/assets",
    response_model=List[AssetResponse],
    summary="List deployed OpenFactory assets",
)
async def get_assets(request: Request):
    """
    Retrieve the list of assets currently deployed in OpenFactory.

    Each asset provides:
    - asset_uuid: unique identifier of the asset
    - uns_id: Unified Namespace identifier
    - availability: current availability state
    - type: asset type (e.g., Scanner, Fusion, MTConnectAgent)

    Notes:
    - Availability is normalized to uppercase string values
    - MTConnectAgent assets use agent-specific availability
    """
    app = request.app.state.ofa_app
    ofa = OpenFactory(ksqlClient=app.ksql)

    results = []

    for asset in ofa.assets():
        if asset.type == "MTConnectAgent":
            availability = asset.agent_avail.value.upper()
        else:
            availability = asset.avail.value.upper()

        results.append({
            "asset_uuid": asset.asset_uuid,
            "uns_id": asset.uns_id.value,
            "availability": availability,
            "type": asset.type,
        })

    return results


@router.get(
    "/api/assets/{asset_uuid}",
    response_model=List[AssetAttribute],
    summary="Inspect an asset",
)
async def inspect_asset(request: Request, asset_uuid: str):
    """
    Retrieve all attributes of a specific asset.

    Path parameters:
    - asset_uuid: unique identifier of the asset to inspect

    Output:
    - A flat list of attributes, each containing:
        - id: attribute identifier (e.g., avail, barcode)
        - value: current value of the attribute
        - type: attribute category (Sample, Events, Condition)
        - tag: semantic tag describing the attribute
    """
    app = request.app.state.ofa_app
    asset = Asset(asset_uuid, ksqlClient=app.ksql)

    results: list[AssetAttribute] = []

    try:
        # --------------------
        # Samples
        # --------------------
        for sample in asset.samples():
            results.append({
                "id": sample["ID"],
                "value": sample["VALUE"],
                "type": "Sample",
                "tag": sample["TAG"],
            })

        # --------------------
        # Events
        # --------------------
        for event in asset.events():
            results.append({
                "id": event["ID"],
                "value": event["VALUE"],
                "type": "Events",
                "tag": event["TAG"],
            })

        # --------------------
        # Conditions
        # --------------------
        for cond in asset.conditions():
            results.append({
                "id": cond["ID"],
                "value": cond["VALUE"],
                "type": "Condition",
                "tag": cond["TAG"],
            })

        return results

    finally:
        # Always ensure cleanup (important in long-running API)
        asset.close()
