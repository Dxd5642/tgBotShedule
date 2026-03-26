from fastapi import APIRouter, status, Response, Query
from app.api.schemas.api_models import *
from app.services import utils as ut 
from app.core.database_utils import create_new_user_for_tg, change_type_response_schedule, change_on_off_alerts_change_sch # Поместить в utils
from app.core.logger_setup import AppLoggers


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
        AppLoggers.api.info(f"Запрос на '/v1/users/' от пользователя :{data.tg_username}")
        res = await create_new_user_for_tg(data.first_name, data.second_name, data.tg_username, data.chat_id, data.role, data.subgroup, data.group_name, data.theacher_name)
        if res['status'] == 'error':
            response.status_code = 500
            AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/'. Ошибка: {res['content']}")
            return {
                'status': 'error',
                'code': 500,
                'message': str(res['content'])
            }
        
        response.status_code = 201
        AppLoggers.api.info(f"Успешная обработка запроса '/v1/users/'")
        return {
                'status': 'success',
                'code': 201,
                'message': f"Пользователь {data.tg_username} успешно добавлен в базу данных!"
            }


    except Exception as e:
        response.status_code = 500
        AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/'. Ошибка: {e}", exc_info=True)
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
        AppLoggers.api.info(f"Запрос на '/v1/users/me/setting/view-type', Данные запроса: ChatID:{data.chat_id}, Type: {data.type}")
        res = await change_type_response_schedule(data.chat_id, data.type)
        if res['status'] == 'error':
            AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/me/setting/view-type'. Ошибка: {res['content']}")
            return {
            'status': 'error',
            'code': 500,
            'message': str(res['content'])
        }

        AppLoggers.api.info(f"Успешная обработка запроса '/v1/users/me/setting/view-type'")
        return {
            'status': 'success',
            'code': 201,
            'message': 'Данные успешно изменены'
        }

    except Exception as e:
        response.status_code = 500
        AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/me/setting/view-type'. Ошибка: {e}", exc_info=True)
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
        AppLoggers.api.info(f"Запрос на '/v1/users/me/setting/alerts', Данные запроса: ChatID:{data.chat_id}, Type: {data.type}")
        res = await change_on_off_alerts_change_sch(data.chat_id, data.type)
        if res['status'] == 'error':
            AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/me/setting/alerts'. Ошибка: {res['content']}")
            return {
            'status': 'error',
            'code': 500,
            'message': str(res['content'])
        }

        AppLoggers.api.info(f"Успешная обработка запроса '/v1/users/me/setting/alerts'")
        return {
            'status': 'success',
            'code': 201,
            'message': 'Данные успешно изменены'
        }

    except Exception as e:
        response.status_code = 500
        AppLoggers.api.warning(f"Ошибка обработки запроса '/v1/users/me/setting/alerts'. Ошибка: {e}", exc_info=True)
        return {
            'status': 'error',
            'code': 500,
            'message': str(e)
        }
