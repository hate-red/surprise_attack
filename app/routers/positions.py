from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.positions import (
    PositionResponse,
    OKEIResponse,
    CharacteristicResponse,
    CharacteristicValueResponse
)
from app.repositories.positions import PositionRepository


router = APIRouter(prefix='/kgru-positions', tags=['Parsing'])


mock_objects = [
  {
    "id": "position-001",
    "name": "Software Engineer",
    "okeis": [
      {
        "id": "okei-001",
        "name": "Engineering"
      }
    ],
    "characteristics": [
      {
        "id": "characteristic-001",
        "name": "Years of experience",
        "required": "true",
        "values": [
          {
            "id": "value-001",
            "is_range": "true",
            "range": "(12: 100]",
            "is_quality": "false",
            "quality_description": "null",
            "okeis": []
          }
        ]
      },
      {
        "id": "characteristic-002",
        "name": "Communication",
        "required": "false",
        "values": [
          {
            "id": "value-002",
            "is_range": "false",
            "range": "null",
            "is_quality": "true",
            "quality_description": "Communicates technical ideas clearly to teammates.",
            "okeis": [
              {
                "id": "okei-002",
                "name": "Collaboration"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    "id": "position-002",
    "name": "Product Designer",
    "okeis": [
      {
        "id": "okei-003",
        "name": "Product Design"
      },
      {
        "id": "okei-004",
        "name": "User Research"
      }
    ],
    "characteristics": [
      {
        "id": "characteristic-003",
        "name": "Portfolio projects",
        "required": "true",
        "values": [
          {
            "id": "value-003",
            "is_range": "true",
            "range": "[0: 10]",
            "is_quality": "false",
            "quality_description": "null",
            "okeis": []
          }
        ]
      },
      {
        "id": "characteristic-004",
        "name": "Visual design",
        "required": "true",
        "values": [
          {
            "id": "value-004",
            "is_range": "false",
            "range": "null",
            "is_quality": "true",
            "quality_description": "Creates consistent, accessible, and polished interfaces.",
            "okeis": [
              {
                "id": "okei-005",
                "name": "Visual Design"
              }
            ]
          }
        ]
      }
    ]
  }
]


@router.get('/{kgru_id}')
async def get_position(kgru_id: str):
    position = await PositionRepository.get_one_by_id(id=kgru_id)

    return position


@router.get('/{char_id}')
async def get_char(kgru_id: str) -> CharacteristicResponse | None:
    position = await PositionRepository.get_one_or_none(id=kgru_id)

    return position


@router.post('/parse')
async def parse(user_input: str) -> list[PositionResponse]:
    objects = [PositionResponse(**values) for values in mock_objects]
    return objects
