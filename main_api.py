import argparse
from app.api.main import create_app
import uvicorn, sys

def main(args: list[str]) -> int:
    try:
        parser = argparse.ArgumentParser(description="Запуск веб-приложения для работы с расписанием")
        parser.add_argument("--host", type=str, default="127.0.0.1", help="Адресс, на котором запуститься веб-приложение")
        parser.add_argument('--port', type=int, default=8000, help="Порт, который будет прослушивать трафик для веб-приложения")
        args = parser.parse_args(args)

        app = create_app()
        uvicorn.run(app=app, host=args.host, port=args.port)
        return 0
    except Exception as e:
        # Logging
        raise SystemExit(1)



if __name__=="__main__":
    main(sys.argv[1:])
