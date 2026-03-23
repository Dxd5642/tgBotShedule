from fastapi import APIRouter, status, Response, Query
from app.api.schemas.api_models import *
from app.services import utils as ut 
from app.core.database_utils import create_new_user_for_tg # Поместить в utils


router = APIRouter(prefix="/v1/users", tags=["Users"])

@router.post("/",
             response_model=APIResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Создать нового пользователя")
async def func_create_new_user(data: NewUserData, response: Response) -> dict:
    """_Функция для ообработки запроса на добавление пользователя в базу данных_

    Args:
        data (NewUserData): _Json объект с данными пользователя_

    Returns:
        dict: _json объект с результатом работы функций_
    """
    try:
        res = await create_new_user_for_tg(data.first_name, data.second_name, data.tg_username, data.chat_id, data.role, data.subgroup, data.group_name, data.theacher_name)
        if res['status'] == 'error':
            response.status_code = 500
            return {
                'status': 'error',
                'code': 500,
                'message': str(res['content'])
            }
        
        response.status_code = 201
        return {
                'status': 'success',
                'code': 201,
                'message': f"Пользователь {data.tg_username} успешно добавлен в базу данных!"
            }


    except Exception as e:
        response.status_code = 500
        return {
            'status': 'error',
            'code': 500,
            'message': str(e)
        }



@router.patch("/me/setting/view-type",
              response_model=APIResponse,
              status_code=status.HTTP_201_CREATED,
              summary="Изменить тип получаемого расписания")
async def func_change_user_type_response_schedule(data: UserChangeTypeResSch, response: Response) -> dict:
    """_Функция для обработки запросов на изменение типа вида расписания_

    Args:
        data (UserChangeTypeResSch): _Данные пользователя, и новый тип_
        response (Response): _Нужен для настройки кодов_

    Returns:
        dict: _Ответ сервера_
    """
    try:
        res = await ut.change_type_response_schedule(data.chat_id, data.type)
        if res['status'] == 'error':
            return {
            'status': 'error',
            'code': 500,
            'message': str(res['content'])
        }

        return {
            'status': 'success',
            'code': 201,
            'message': 'Данные успешно изменены'
        }

    except Exception as e:
        response.status_code = 500
        return {
            'status': 'error',
            'code': 500,
            'message': str(e)
        }



@router.patch("me/setting/alerts",
              response_model=APIResponse,
              status_code=status.HTTP_201_CREATED,
              summary="Включение/выключение уведомлений об изменениях")
async def func_change_user_alerts_by_change(data: UserChangeTypeResSch, response: Response) -> dict:
    """_Функция для обработки запросов на включение и выключени уведомлений об изменениях_

    Args:
        data (UserChangeTypeResSch): _Данные об пользователе_
        response (Response): _Нужен для изменения кодов_

    Returns:
        dict: _Ответ сервера_
    """
    try:
        res = await ut.change_type_response_schedule(data.chat_id, data.type)
        if res['status'] == 'error':
            return {
            'status': 'error',
            'code': 500,
            'message': str(res['content'])
        }

        return {
            'status': 'success',
            'code': 201,
            'message': 'Данные успешно изменены'
        }

    except Exception as e:
        response.status_code = 500
        return {
            'status': 'error',
            'code': 500,
            'message': str(e)
        }
