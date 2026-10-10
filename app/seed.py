import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Import your models and async session factory:
from app.models.positions import Position, OKEI, Characteristic, CharacteristicValue
from app.database import async_session_maker

def parse_range(data: dict | None) -> Range | None:
    if data is None:
        return None

    lower = data.get("min_value")
    upper = data.get("max_value")

    lower_inclusive = data.get("min_notation") == "greaterOrEqual"
    upper_inclusive = data.get("max_notation") == "lessOrEqual"
    bounds = ("[" if lower_inclusive else "(") + (
        "]" if upper_inclusive else ")"
    )

    return Range(lower, upper, bounds=bounds)


async def get_or_create_okei(session: AsyncSession, data: dict) -> OKEI:
    # okei_id = data["id"]
    # okei = await session.get(OKEI, okei_id)

    # if okei is None:
        # okei = OKEI(id=okei_id, name=data["name"])
    okei = OKEI(name=data["name"])
    session.add(okei)
    await session.flush()

    return okei


async def load_positions(json_path: str) -> None:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    async with async_session_maker() as session:
        for item in data['positions']:
            position_id = item["ktru_code"]

            if await session.get(Position, position_id) is not None:
                continue

            position = Position(id=position_id, name=item["name"])

            for okei_data in item.get("okeis", []):
                position.okeis.append(
                    await get_or_create_okei(session, okei_data)
                )

            for characteristic_data in item.get("characteristics", []):
                characteristic = Characteristic(
                    name=characteristic_data["name"],
                    required=characteristic_data.get("required", True),
                )

                for value_data in characteristic_data.get("values", []):
                    range_data = value_data.get("range")
                    if value_data.get("is_range") and range_data is None:
                        raise ValueError(
                            f"Range value {value_data['id']} has no range data"
                        )

                    description = value_data.get("quality_description")
                    value = CharacteristicValue(
                        # The JSON has no "name"; replace with a lookup if available.
                        name=description or value_data["id"],
                        is_range=value_data.get("is_range", False),
                        range=parse_range(range_data),
                        is_quality=value_data.get("is_quality", False),
                        quality_description=description,
                    )

                    for okei_data in value_data.get("okeis", []):
                        value.okeis.append(
                            await get_or_create_okei(session, okei_data)
                        )

                    characteristic.values.append(value)

                position.characteristics.append(characteristic)

            session.add(position)
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Example:
# async_sessionmaker_factory = async_sessionmaker(
#     engine, class_=AsyncSession, expire_on_commit=False
# )

async def main() -> None:
    await load_positions("/home/q/python/hackathon/app/parser/ktru_db.json")


