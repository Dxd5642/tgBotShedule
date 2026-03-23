from fastapi import APIRouter, status
from app.api.schemas.api_models import *

router = APIRouter(prefix="", tags=['Main'])

@router.get("/", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def index_req():
        return {
            'status': 'success',
            'code': 200,
            'data': 'API для работы с базой данных бота с расписанием для КЦПТ',
            'message': 'Сервер запущен'
        }


@router.get('/health', response_model=APIResponse, status_code=status.HTTP_200_OK)
async def health_req():
    return {
        'status': 'success',
        'code': 200,
        'message': 'Сервис успешно работает'
    }