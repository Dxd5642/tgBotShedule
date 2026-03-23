from fastapi import APIRouter, status, Response, Query
from app.api.schemas.api_models import *
from app.services import utils  as ut
from PySide6.QtWidgets import QApplication

router = APIRouter(prefix="/v1/schedules", tags=["Schedules"])

@router.get("/groups/{group_name}", 
            response_model=APIResponse, 
            status_code=status.HTTP_200_OK, 
            summary="Получить расписание конкретной группы")
async def func_get_schedule_for_group(group_name: str, response: Response, target_date: datetime.date = Query(default=datetime.date.today()), subgroup: int = Query(default=0)) -> dict:
    """_Функция, обрабатывающая запрос на получение расписание для группы по дате_

    Args:
        group_name (str): _Имя группы, для которой ищем расписание_
        target_date (datetime.date, optional): _Дата, на которую ищем расписание_. Defaults to Query(default=datetime.date.today()).
        subgroup (int, optional): _Номер подгруппы_. Defaults to Query(default=0).

    Returns:
        json: _json файл с результатом работы функций_
    """
    try:
        # Обращаемся к функции получения расписания
        res = await ut.get_schedule_for_student_by_group_name_and_subgroup(group_name, str(subgroup), target_date)

        if res['status'] == "error":
            response.status_code = 500
            return{
                'status': 'error',
                'code': 500,
                'message': str(res['content'])
            }

        return {
            'status': 'success',
            'code': 200,
            'data': res['content'],
            'message': 'Расписание найдено'
        }



    except Exception as e:
        response.status_code = 500
        return{
                'status': 'error',
                'code': 500,
                'message': str(e)
            }


@router.get("/teachers/{teacher_name}",
            response_model=APIResponse,
            status_code=status.HTTP_200_OK,
            summary="Получить расписание для конкретного препода")
async def func_get_schedule_for_theacher(teacher_name: str, response: Response, target_date: datetime.date = Query(default=datetime.date.today())) -> dict:
    """_Функция для обработки запроса на получение расписание по имени препода_

    Args:
        teacher_name (str): _Данные препода, в частности его ФИО_
        target_date (datetime.date, optional): _Дата, на которую нужно получить расписание_. Defaults to Query(default=datetime.date.today()).

    Returns:
        _type_: _description_
    """
    try:
        res = await ut.get_schedule_for_theacher_by_teacher_name_name(teacher_name, target_date)

        if res['status'] == 'error':
            response.status_code = 500
            return {
                'status': 'error',
                'code': 500,
                'message': str(res['content'])
            }
        
        return {
            'status': 'success',
            'code': 200,
            'data': res['content'],
            'message': 'Расписание найдено!'
        }

    except Exception as e:
        response.status_code = 500
        return {
                'status': 'error',
                'code': 500,
                'message': str(e)
            }


@router.post("/my",
             response_model=APIResponse,
             status_code=status.HTTP_200_OK,
             summary="Получить расписание по ChatId")
async def func_get_schedule_for_chatid(data: UserSchReq, response: Response) -> dict:
    """_Функция для обработки запроса на получение расписания по id чата пользователя и дате_

    Args:
        data (dict): _json файл с данными об пользователе, и дате_

    Returns:
        dict: _json файл, с расписанием_
    """
    try:
        chatId = data.chat_id
        date = data.date
        engine = QApplication.instance()

        res = await ut.get_schedule_from_bd(chatId, date, engine)
        if res['status'] == 'error':
            response.status_code = 500
            return{
                'status': 'error',
                'code': 500,
                'message': str(res['content'])
            }
        
        elif res['status'] == 'fail_img':
            return{
                'status': 'success',
                'code': 200,
                'data': res['content'],
                'message': "Произошла ошибка при генерации изображения, возвращено расписание в текстом формате"
            }

        response.status_code = 200
        return {
            'status': 'success',
            'code': 200,
            'data': res['content'],
            'message': 'Расписание найдено'
        }

    except Exception as e:
        response.status_code = 500
        return{
                'status': 'error',
                'code': 500,
                'message': str(e)
            }


@router.put("/full-update",
            response_model=APIResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Запуск полного обновления расписания")
async def func_start_full_update_schedule(response: Response) -> dict:
    """_Функция для полного обновления распианния_

    Returns:
        data (dict): _Возвращает словарь с информацией об обновлении_
    """
    try:
        res = await ut.update_schedule_from_site()

        if res['status'] == 'error':
            response.status_code = 502
            return {
                'status': 'error',
                'code': 502,
                'message': str(res['content'])
            }
        
        elif res['status'] == 'no action':
            response.status_code = 204
            return {
                'status': 'success',
                'code': 204,
                'message': 'Расписание уже было недавно обновлено'
            }

        response.status_code = 201
        return {'status': 'success',
                'code': 201,
                'message': 'Расписание обновлено'
                }

    except Exception as e:
        response.status_code = 500
        return {
                'status': 'error',
                'code': 500,
                'message': str(e)
            }


@router.post("/changes",
             response_model=APIResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Запуск обновления только изменений в расписании")
async def func_start_update_changes_schedule(response: Response) -> dict:
    """_Функция для обработки запроса на обновление изменений в расписании_

    Args:
        response (Response): _Для установки кода_

    Returns:
        dict: _json объект_
    """
    try:
        res = await ut.add_changes_from_site()

        if res['status'] == 'error':
            response.status_code = 502
            return {
                'status': 'error',
                'code': 502,
                'message': str(res['content'])
            }
        
        elif res['status'] == 'no action':
            response.status_code = 204
            return {
                'status': 'success',
                'code': 204,
                'message': 'Расписание уже было недавно обновлено'
            }

        response.status_code = 201
        return {'status': 'success',
                'code': 201,
                'message': 'Расписание обновлено'
                }

    except Exception as e:
        response.status_code = 500
        return {
                'status': 'error',
                'code': 500,
                'message': str(e)
            }
