import sqlite3
import aiosqlite
from datetime import datetime, date
from app.core.config import setting

DB_PATH = setting.DATABASE_PATH



def get_day_name(date_str: str) -> str:
    days = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье"
    }
    # Превращаем '06.03.2026' в объект даты
    dt = datetime.strptime(date_str, '%d.%m.%Y')
    # dt.weekday() вернет число от 0 до 6
    return days[dt.weekday()]

# ===============================================================

async def init_databse() -> dict:
    """
    Инициализирует базу данных, создает необходимые таблицы
    Выполняется один раз, при запуске сервиса
    """
    try:
        if (DB_PATH).exists():
            return {'status': 'success'}
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Groups(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_group TEXT UNIQUE,
                    date_add DATE
                       )
        """)
        conn.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teachers(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT UNIQUE,
                    date_add Date
                       )
        """)
        conn.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT,
                    second_name TEXT,
                    tg_username TEXT UNIQUE,
                    chat_id TEXT UNIQUE,
                    role INTEGER DEFAULT 0,
                    group_id INTEGER DEFAULT NULL,
                    subgroup INTEGER DEFAULT NULL,
                    teacher_name_id INTEGER DEFAULT NULL,
                    date_add DATE,
                    on_alerts_change_sch INTEGER DEFAULT 1,
                    type_away_schedule INTEGER DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES Groups (id) ON DELETE SET NULL,
                    FOREIGN KEY (teacher_name_id) REFERENCES Teachers (id) ON DELETE SET NULL
                       )
        """)
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Group_lesson_names(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER,
                    lesson_name TEXT,
                    FOREIGN KEY (group_id) REFERENCES Groups (id) ON DELETE CASCADE,
                    UNIQUE(group_id, lesson_name)
                     )
        """)
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Types_time_day(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name UNIQUE
                     )
                    """)
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Times_lessons_for_day(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_day_id INTEGER,
                    lesson_number INTEGER,
                    time_start TEXT,
                    time_end TEXT,
                    FOREIGN KEY (type_day_id) REFERENCES Types_time_day (id) ON DELETE CASCADE
                     )
        """)
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Lessons(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_number INTEGER,
                    lesson_name_id INTEGER,
                    group_name_id INTEGER,
                    subgroup INTEGER DEFAULT 0,
                    teacher_name_id INTEGER,
                    room_number TEXT,
                    day_name TEXT,
                    day_date DATE,
                    is_modified INTEGER DEFAULT 0,
                    date_update DATE,
                    FOREIGN KEY (lesson_name_id) REFERENCES Group_lesson_names (id) ON DELETE CASCADE,
                    FOREIGN KEY (group_name_id) REFERENCES Groups (id) ON DELETE CASCADE,
                    FOREIGN KEY (teacher_name_id) REFERENCES Teachers (id) ON DELETE SET NULL
                     )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_lessons_for_students ON Lessons (group_name_id, day_date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lessons_for_teachers ON Lessons (teacher_name_id);")
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Actions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT UNIQUE
                     )
        """)
        conn.commit()

        conn.execute("""INSERT INTO Actions (action) VALUES (?)""",("Глобальное обновление всего расписания",))
        conn.commit()

        conn.execute("""INSERT INTO Actions (action) VALUES (?)""",("Мелкие изменение в расписании",))
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Date_actions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE,
                    time TEXT,
                    action_id INTEGER,
                    last_date_name DATE,
                    FOREIGN KEY (action_id) REFERENCES Actions (id) ON DELETE CASCADE
                     )
        """)

        conn.commit()

        conn.execute("""INSERT INTO Types_time_day (type_name) VALUES ("Будние дни")""")
        conn.commit()
        conn.execute("""INSERT INTO Types_time_day (type_name) VALUES ("Суббота")""")
        conn.commit()
        conn.execute("""INSERT INTO Types_time_day (type_name) VALUES ("Праздник (Сокращение пар на 10 мин)")""")
        conn.commit()
        conn.execute("""INSERT INTO Types_time_day (type_name) VALUES ("Праздник (Сокращение пар на 15 мин)")""")
        conn.commit()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Days(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     date DATE UNIQUE,
                     type_day_id INTEGER DEFAULT 1,
                     FOREIGN KEY (type_day_id) REFERENCES Types_time_day (id) ON DELETE SET NULL
                     )
        """)
        conn.commit()


        conn.close()

        return {'status': 'success'}

    except EOFError as e:
        return {'status': 'error', 'content': e}
    

async def update_groups(data: list) -> dict:
    """
    Функция для заполнения таблицы Groups, выполняется ассинхронно
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            data_to_insert = [(item[0], item[1],) for item in data]

            await db.executemany(
                "INSERT OR IGNORE INTO Groups (name_group, date_add) VALUES (?, ?)",
                data_to_insert
            )

            await db.commit()
            return {"status": 'success'}

    except Exception as e:
        return {"status": 'error', 'content': e}


async def update_teachers(data: list) -> dict:
    """
    Функция для заполнения таблицы Teachers, выполняется ассинхронно
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            data_to_insert = [(item[0], item[1]) for item in data]

            await db.executemany(
                "INSERT OR IGNORE INTO Teachers (full_name, date_add) VALUES (?, ?)",
                data_to_insert
            )

            await db.commit()
            return {"status": 'success'}

    except Exception as e:
        return {"status": 'error', 'content': e}


async def update_lessons_group(lessons_list: list) -> dict:
    """
    Функция для заполнения таблицы Group_lesson_names, выполняется ассинхронно, возвращает ошибку, если значения пустые
    """

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            sql = """
            INSERT OR IGNORE INTO Group_lesson_names (group_id, lesson_name)
            SELECT id, ? FROM Groups WHERE name_group = ?
            """
            
            data_to_insert = [(item[1], item[0]) for item in lessons_list]
            
            await db.executemany(sql, data_to_insert)
            
            await db.commit()
            return {"status": 'success'}


    except Exception as e:
        return {"status": "error", 'content': e}
    

async def update_lessons(lessons_list: list) -> dict:
    """
    Функция для заполнения бд всеми парами и уроками, которые были спарсены
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            sql ="""
            INSERT INTO Lessons (
                lesson_number, 
                lesson_name_id, 
                group_name_id, 
                subgroup, 
                teacher_name_id, 
                room_number, 
                day_name, 
                day_date,
                date_update
            )
            VALUES(
                ?, -- lesson_number
                (SELECT id FROM Group_lesson_names WHERE lesson_name = ? AND group_id = (SELECT id FROM Groups WHERE name_group = ? LIMIT 1) LIMIT 1),
                (SELECT id FROM Groups WHERE name_group = ? LIMIT 1),
                ?, -- subgroup
                (SELECT id FROM Teachers WHERE full_name = ? LIMIT 1),
                ?, -- room_number
                ?, -- day_name
                ?, -- day_date
                ? -- date_update
                )
            """
            params = [(i[0], i[1], i[2], i[2], i[3], i[4], i[5], i[6], i[7], i[8]) for i in lessons_list]

            await db.executemany(sql, params)
            await db.commit()

            sql = """
            INSERT OR IGNORE INTO Days (date, type_day_id) VALUES (?, ?);
            """
            params = [(i[7], (2 if str(i[6]).lower() == 'суббота' else 1)) for i in lessons_list]
            await db.executemany(sql, params)
            await db.commit()

            return {'status': 'success'}
            


    except Exception as e:
        return {'status': 'error', 'content': e}


async def get_lessons_by_group_and_day(group: str, day: str) -> dict:
    """
    Функция для получения всех пар определенной группы в определенный день
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            sql = ("""
            SELECT 
                g.name_group,
                l.subgroup,
                l.lesson_number,
                gln.lesson_name,
                t.full_name,
                l.room_number,
                l.subgroup,
                l.day_name
            FROM Lessons l
                JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                JOIN Groups g ON l.group_name_id = g.id
                LEFT JOIN Teachers t ON l.teacher_name_id = t.id
            WHERE g.name_group = ? 
                AND l.day_date = ?
            ORDER BY l.lesson_number, l.subgroup;
            """)

            async with db.execute(sql, (group, day,)) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return {'status': 'success', 'content': 'Занятий не найдено!'}

                schedule = []
                for row in rows:
                    subj = row['lesson_name']
                    if row['subgroup'] != 0:
                        subj += f" ({row['subgroup']} подгр.)"
                    
                    schedule.append({
                        "group_name": row['name_group'],
                        "subgroup": row['subgroup'],
                        "lesson_number": row['lesson_number'],
                        "lesson_name": row["lesson_name"],
                        "teacher_name": row['full_name'],
                        'room_number': row['room_number'],
                        "day_name": row['day_name']
                    })
                
                return {'status': 'success', 'content': schedule}


    except Exception as e:
        return {'status': 'error', 'content': e}


async def get_lessons_for_teacher(teacher_name: str, day: str) -> dict:
    """
    Функция для получения всех пар для учителя, по имени учителя и дате
    """
    try:
        
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            sql = ("""
            SELECT 
                t.full_name,
                l.lesson_number,
                gln.lesson_name,
                g.name_group,
                l.subgroup,
                l.room_number,
                l.day_name,
                l.subgroup
            FROM Lessons l
                JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                JOIN Groups g ON l.group_name_id = g.id
                LEFT JOIN Teachers t ON l.teacher_name_id = t.id
            WHERE t.full_name = ? 
                AND l.day_date = ?
            ORDER BY l.lesson_number, l.subgroup;
            """)

            async with db.execute(sql, (teacher_name, day,)) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return {'status': 'success', 'content': 'Занятий не найдено!'}

                schedule = []
                for row in rows:
                    subj = row['lesson_name']
                    if row['subgroup'] != 0:
                        subj += f" ({row['subgroup']} подгр.)"
                    
                    schedule.append({
                        "teacher_name": row['full_name'],
                        "lesson_number": row['lesson_number'],
                        "lesson_name": row["lesson_name"],
                        "group_name": row['name_group'],
                        "subgroup": row['subgroup'],
                        'room_number': row['room_number'],
                        "day_name": row['day_name']
                    })
                
                return {'status': 'success', 'content': schedule}

    except EOFError as e:
        return {'status': 'error', 'content': e}

# ======================= Изменения в бд =========================

async def change_lessons_change(lessons_list: list) -> dict:
    """
    Функция, для внесения изменений в расписании
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            for item in lessons_list:
                # Распаковываем новую структуру
                sched_date_raw, group, sub, type_ch, num, lesson, room, teacher, db_date, last_subg = item
                
                if type_ch == -1: continue

                # Конвертируем '06.03.2026' -> '2026-03-06'
                sched_date = datetime.strptime(sched_date_raw, '%d.%m.%Y').strftime('%Y-%m-%d')
                day_name = get_day_name(sched_date_raw)

                # 1. ОТМЕНА (Тип 0) — Полное удаление
                if type_ch == 0:
                    sql_delete = """
                    DELETE FROM Lessons 
                    WHERE group_name_id = (SELECT id FROM Groups WHERE name_group = ? LIMIT 1)
                    AND lesson_number = ? 
                    AND subgroup = ? 
                    AND day_date = ?
                    """
                    await db.execute(sql_delete, (group, num, int(last_subg), sched_date))



                # 2. БУДЕТ / ЗАМЕНА ПРЕДМЕТА (Тип 1)
                elif type_ch == 1: # БУДЕТ
                    short_lesson_name = lesson.strip()
                    await db.execute("""
                        DELETE FROM Lessons 
                        WHERE day_date = ? AND group_name_id = (SELECT id FROM Groups WHERE name_group = ? LIMIT 1)
                        AND lesson_number = ? AND subgroup = ?
                    """, (sched_date, group, num, int(last_subg)))


                    sql = """
                    INSERT OR REPLACE INTO Lessons (
                        group_name_id, subgroup, is_modified, lesson_number, 
                        lesson_name_id, room_number, teacher_name_id, day_date, day_name, date_update
                    )
                    VALUES (
                        (SELECT id FROM Groups WHERE name_group = ? LIMIT 1),
                        ?, 1, ?, 
                        (SELECT id FROM Group_lesson_names 
                        WHERE (lesson_name = ? OR lesson_name LIKE ? || '%') 
                        AND group_id = (SELECT id FROM Groups WHERE name_group = ? LIMIT 1) 
                        LIMIT 1),
                        ?, 
                        (SELECT id FROM Teachers WHERE full_name = ? LIMIT 1), 
                        ?, ?, ?
                    )
                    """
                    params = (
                        group.strip(), 
                        int(sub),        
                        num,             
                        short_lesson_name, 
                        short_lesson_name,
                        group.strip(),          
                        room,            
                        teacher.strip(), 
                        sched_date, 
                        day_name,
                        db_date,
                    )
                    await db.execute(sql, params)
                    
                # 3. ЗАМЕНА КАБИНЕТА (Тип 2)
                elif type_ch == 2:
                    sql_update_room = """
                    UPDATE Lessons SET 
                        room_number = ?, 
                        is_modified = 1 -- Также помечаем как измененную
                    WHERE group_name_id = (SELECT id FROM Groups WHERE name_group = ? LIMIT 1)
                    AND lesson_number = ? 
                    AND subgroup = ? 
                    AND day_date = ?
                    """

                    await db.execute(sql_update_room, (room, group.strip(), num, int(last_subg), sched_date))

            await db.commit()
            return {'status': 'success'}

    except EOFError as e:
        return {'status': 'error', 'content': e}

# ================================================================

# ============================= Добавить и забрать запись последнего действия в бд ==========================

async def add_note_action(type_action: int, last_date: str) -> dict:
    """
    Функция, добавляющая в бд запись последнего действия
    """
    try:
        date_today = (datetime.today()).strftime('%Y-%m-%d')
        time_now = f"{datetime.now().hour}:{datetime.now().minute}"

        last_date = "-".join(last_date.split(".")[::-1])
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO Date_actions (date, time, action_id, last_date_name) VALUES (?, ?, ?, ?)", (date_today, time_now, type_action, last_date,))
            await db.commit()

        return {'status': 'success'}
    except EOFError as e:
        print(e)
        return {'status': 'error', 'content': e}



async def get_note_action(type_action: int, last_date_update: str) -> dict:
    """
    Функция, забирающая из бд запись последнего действия
    """
    try:  
        last_date = "-".join(last_date_update.split(".")[::-1])
        async with aiosqlite.connect(DB_PATH) as db:
            sql = """
            SELECT * FROM Date_actions 
            WHERE action_id = ? AND last_date_name = ?
            ORDER BY date DESC, id DESC 
            LIMIT 1
            """
            async with db.execute(sql, (type_action, last_date,)) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return {'status': 'success', 'content': 'no notes'}
                
                rows = rows[0]
                
                res = {
                    'date': rows[1],
                    'time': rows[2],
                    'last_date_name': rows[3]
                }

        return {'status': 'success', 'content': res}
    except Exception as e:
        print(e)
        return {'status': 'error', 'content': e}

# ================================================================

# ===================== Добавление расписания звонков ============

async def add_type_name_days(type_name: str) -> dict:
    """
    Функция, для добавления в бд название типа дня для расписания звонков (пока что не понадобится)
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO Types_time_day (type_name) VALUES (?)",(type_name,))
            await db.commit()

            return {'status': 'success'}

    except Exception as e:
        return {"status": 'error', 'content': e}



async def add_times_less_for_day(data: list) -> dict:
    """
    Функция, для добавления в бд рапсисания звонков для соответствующего дня
    """
    try: 
        async with aiosqlite.connect(DB_PATH) as db:
            sql ="""
        INSERT INTO Times_lessons_for_day (type_day_id, lesson_number, time_start, time_end)
        VALUES (?, ?, ?, ?)
        """

            await db.executemany(sql, data)
            await db.commit()

            return {'status': 'success'}

    except Exception as e:
        return {'status': 'error', 'content': e}

# ================================================================



# ========================== Получить данные пользователя ========

async def get_info_user(chat_id: str) -> dict:
    """
    Получаем из БД данные пользователя по id его чата
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            sql = """
            SELECT id, first_name, second_name, tg_username, role, group_id, subgroup, teacher_name_id, type_away_schedule FROM
            Users WHERE chat_id = ? LIMIT 1
            """
            async with db.execute(sql, (chat_id,)) as cur:
                row = await cur.fetchall()

                if not row:
                    return {'status': 'error', 'content': 'Пользователь не найден'}
            
            return {'status': 'success', 'content': row[0]}


    except Exception as e:
        return {'status': 'error', 'content': e}



async def get_schedule_for_student_by_group_and_subgroup(group_id: str, subgroup: str, date: str) -> dict:
    """
    Функция, для получения расписания из БД на основе группы и подгруппы человека
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            if subgroup == '0':
                sql = """
                SELECT
                    g.name_group,
                    l.lesson_number,
                    gln.lesson_name,
                    tlfd.time_start,
                    tlfd.time_end,
                    l.subgroup,
                    l.room_number,
                    t.full_name,
                    l.day_name
                FROM Lessons l
                    LEFT JOIN Groups g ON l.group_name_id = g.id
                    LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                    LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                    LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
                WHERE
                    l.group_name_id = ?
                    AND l.day_date = ?
                ORDER BY l.lesson_number, l.subgroup; 
                """
                params = (group_id, date,)
            else:
                sql = """
                SELECT
                    g.name_group,
                    l.lesson_number,
                    gln.lesson_name,
                    tlfd.time_start,
                    tlfd.time_end,
                    l.subgroup,
                    l.room_number,
                    t.full_name,
                    l.day_name
                FROM Lessons l
                    LEFT JOIN Groups g ON l.group_name_id = g.id
                    LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                    LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                    LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
                WHERE
                    l.group_name_id = ?
                    AND l.day_date = ?
                    AND (l.subgroup = 0 OR l.subgroup = ?)
                ORDER BY l.lesson_number, l.subgroup; 
                """
                params = (group_id, date, subgroup,)
            async with db.execute(sql, params) as cur:
                rows = await cur.fetchall()
                lessons = []

                for row in rows:
                    less = {
                        'lesson_number': row['lesson_number'],
                        'lesson_name': row['lesson_name'],
                        'lesson_time_start': row['time_start'],
                        'lesson_time_end': row['time_end'],
                        'subgroup': row['subgroup'],
                        'room': row['room_number'],
                        'teacher_name': row['full_name']
                    }

                    lessons.append(less)

                res = {
                    'group': rows[0]['name_group'],
                    'date': date,
                    'day_name': rows[0]['day_name'],
                    'lessons': lessons
                }

                return {'status': 'success', 'content': res}

    except EOFError as e:
        return {'status': 'error', 'content': e}



async def get_schedule_for_student_by_group_name_and_subgroup(group_name: str, subgroup: str, date: str) -> dict:
    """
    Функция, для получения расписания из БД на основе группы и подгруппы человека
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            if subgroup == '0':
                sql = """
                SELECT
                    g.name_group,
                    l.lesson_number,
                    gln.lesson_name,
                    tlfd.time_start,
                    tlfd.time_end,
                    l.subgroup,
                    l.room_number,
                    t.full_name,
                    l.day_name
                FROM Lessons l
                    LEFT JOIN Groups g ON l.group_name_id = g.id
                    LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                    LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                    LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
                WHERE
                    g.name_group = ?
                    AND l.day_date = ?
                ORDER BY l.lesson_number, l.subgroup; 
                """
                params = (group_name, date,)
            else:
                sql = """
                SELECT
                    g.name_group,
                    l.lesson_number,
                    gln.lesson_name,
                    tlfd.time_start,
                    tlfd.time_end,
                    l.subgroup,
                    l.room_number,
                    t.full_name,
                    l.day_name
                FROM Lessons l
                    LEFT JOIN Groups g ON l.group_name_id = g.id
                    LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                    LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                    LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
                WHERE
                    g.name_group = ?
                    AND l.day_date = ?
                    AND (l.subgroup = 0 OR l.subgroup = ?)
                ORDER BY l.lesson_number, l.subgroup; 
                """
                params = (group_name, date, subgroup,)
            async with db.execute(sql, params) as cur:
                rows = await cur.fetchall()
                
                if not rows:
                    return {'status': 'error', 'content': 'Расписание не найдено!'}
                
                lessons = []

                for row in rows:
                    less = {
                        'lesson_number': row['lesson_number'],
                        'lesson_name': row['lesson_name'],
                        'lesson_time_start': row['time_start'],
                        'lesson_time_end': row['time_end'],
                        'subgroup': row['subgroup'],
                        'room': row['room_number'],
                        'teacher_name': row['full_name']
                    }

                    lessons.append(less)

                res = {
                    'group': rows[0]['name_group'],
                    'date': date,
                    'day_name': rows[0]['day_name'],
                    'lessons': lessons
                }


                return {'status': 'success', 'content': res}

    except Exception as e:
        return {'status': 'error', 'content': e}



async def get_schedule_for_theacher_by_teacher_name(teacher_name_id: str, date: str) -> dict:
    """
    Функция, для получения расписания для учителя, по имени учителя
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            sql = """
            SELECT 
                t.full_name,
                l.lesson_number,
                gln.lesson_name,
                tlfd.time_start,
                tlfd.time_end,
                g.name_group, 
                l.subgroup,
                l.room_number
            FROM Lessons l
                LEFT JOIN Groups g ON l.group_name_id = g.id
                LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
            WHERE
                l.teacher_name_id = ? 
                AND l.day_date = ?
            ORDER BY l.lesson_number, l.subgroup
            """
            async with db.execute(sql, (teacher_name_id, date,)) as cur:
                rows = await cur.fetchall()
                lessons = []

                for row in rows:
                    less = {
                        'lesson_number': row['lesson_number'],
                        'lesson_name': row['lesson_name'],
                        'lesson_time_start': row['time_start'],
                        'lesson_time_end': row['time_end'],
                        'name_group': row['name_group'],
                        'subgroup': row['subgroup'],
                        'room': row['room_number']
                    }

                    lessons.append(less)

                res = {
                    'teacher_name': rows[0]['full_name'],
                    'date': date,
                    'lessons': lessons
                }


                return {'status': 'success', 'content': res}


    except Exception as e:
        return {'status': 'error', 'content': e}



async def get_schedule_for_theacher_by_teacher_name_name(teacher_name: str, date: str) -> dict:
    """
    Функция, для получения расписания для учителя, по имени учителя
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row
            sql = """
            SELECT 
                t.full_name,
                l.lesson_number,
                gln.lesson_name,
                tlfd.time_start,
                tlfd.time_end,
                g.name_group, 
                l.subgroup,
                l.room_number
            FROM Lessons l
                LEFT JOIN Groups g ON l.group_name_id = g.id
                LEFT JOIN Group_lesson_names gln ON l.lesson_name_id = gln.id
                LEFT JOIN Teachers t ON l.teacher_name_id = t.id
                LEFT JOIN Days d ON l.day_date = d.date
                    LEFT JOIN Times_lessons_for_day tlfd ON d.type_day_id = tlfd.type_day_id AND tlfd.lesson_number = l.lesson_number
            WHERE
                t.full_name = ? 
                AND l.day_date = ?
            ORDER BY l.lesson_number, l.subgroup
            """
            async with db.execute(sql, (teacher_name, date,)) as cur:
                rows = await cur.fetchall()
                lessons = []

                for row in rows:
                    less = {
                        'lesson_number': row['lesson_number'],
                        'lesson_name': row['lesson_name'],
                        'lesson_time_start': row['time_start'],
                        'lesson_time_end': row['time_end'],
                        'name_group': row['name_group'],
                        'subgroup': row['subgroup'],
                        'room': row['room_number']
                    }

                    lessons.append(less)

                res = {
                    'teacher_name': rows[0]['full_name'],
                    'date': date,
                    'lessons': lessons
                }


                return {'status': 'success', 'content': res}


    except Exception as e:
        return {'status': 'error', 'content': e}



async def change_type_response_schedule(chat_id: str, type: int) -> dict:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            sql = """
            UPDATE Users SET type_away_schedule = ? WHERE chat_id = ?
            """
            await db.execute(sql, (type, chat_id,))
            await db.commit()

            return {'status': 'success'}

    except Exception as e:
        return {'status': 'error', 'content': e}



async def change_on_off_alerts_change_sch(chat_id: str, type: int) -> dict:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            sql = """
            UPDATE Users SET on_alerts_change_sch  = ? WHERE chat_id = ?
            """
            await db.execute(sql, (type, chat_id,))
            await db.commit()

            return {'status': 'success'}

    except Exception as e:
        return {'status': 'error', 'content': e}

# ================================================================

# ====================== Создать нового пользователя =============

async def create_new_user_for_tg(
        first_name: str, second_name: str, tg_username:str, chat_id: str,
        role: int, subgroup: int, group_name: str = None,  theacher_name: str = None
) -> dict:
    date_add = date.today()

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if role == 0:
                sql = """
                INSERT INTO Users (
                    first_name,
                    second_name,
                    tg_username,
                    chat_id,
                    role,
                    group_id,
                    subgroup,
                    date_add
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    (SELECT id FROM Groups WHERE name_group = ? LIMIT 1),
                    ?,
                    ?
                )
                """
                params = (first_name, second_name, tg_username, chat_id, role, group_name, subgroup, date_add)
            
            elif role == 1:
                sql = """
                INSERT INTO Users (
                    first_name,
                    second_name,
                    tg_username,
                    chat_id,
                    role,
                    teacher_name_id ,
                    date_add
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    (SELECT id FROM Teachers WHERE full_name = ? LIMIT 1),
                    ?
                )
                """
                params = (first_name, second_name, tg_username, chat_id, role, theacher_name, date_add)
            await db.execute(sql, params)
            await db.commit()

            return {'status': 'success'}
        
    except Exception as e:
        return {'status': 'error', 'content': e}

# ================================================================
