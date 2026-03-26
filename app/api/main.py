from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from PySide6.QtWidgets import QApplication
from app.api.router import router as main_router
from app.api.v1 import users, schedules
from app.api.schemas.api_models import *
from app.services.utils import initialization_database
from app.core.config import setting
import os, sys

BASE_DIR = setting.BASE_DIR
DATABASE_PATH = setting.DATABASE_PATH

def create_app() -> FastAPI:
    """_Функция для запуска сервера работы с бд_

    Args:
        host (str) = _Адресс, на котором будет запущен сервер_
        port (int) = _Порт, на котором будет запущен сервер_
        
    """
    
    async def lifespan(app: FastAPI):
        print("Запуск сервера...")
        if os.path.exists(DATABASE_PATH):
            print("База данных уже создана")
        else:
            print("Инициализация базы данных...")
            res = await initialization_database()
            if res['status'] == 'error':
                print(f"При инициализации базы данных произошла ошибка: {res['content']}")
            print("База данных успешно инициализирована!")

        yield

        print("Остановка сервера...")
    
    engineimg = QApplication.instance() or QApplication(sys.argv + ['-platform', 'offscreen'])
    app = FastAPI(title="Api для работы с бд", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_headers=['*'],
        allow_origins=['*'],
        allow_methods=['*']
    )

    app.include_router(main_router)
    app.include_router(users.router)
    app.include_router(schedules.router)


    return app

app = create_app()
