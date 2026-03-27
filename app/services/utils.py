import pandas as pd
from datetime import datetime
import requests
from io import BytesIO
from PySide6.QtWidgets import QApplication

from app.core.config import setting

from app.services import create_image_schedule
from app.core import database_utils as dbu 
from bs4 import BeautifulSoup
import re, httpx
import json


def func_for_check_result(data: dict, name_file=(setting.BASE_DIR / 'result')):
    with open(f'{name_file}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def noramizer_teacher_name(teacher_name: str):
    """
    Нормализация имени преподввателя
    """
    teacher_name = teacher_name.title().split()
    if len(teacher_name) == 1:
        return teacher_name[0]
    
    elif len(teacher_name) == 2:
        return f"{teacher_name[0]} {teacher_name[1][:2]} {teacher_name[1][-2:]}"

    else:
        return " ".join(teacher_name)



async def get_site_html(url: str) -> str:
    """Функция, возвращающая html код сайта по url"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(headers=headers, follow_redirects=True, verify=False) as client:
            response = await client.get(url, timeout=20.0)

            if response.status_code == 200:
                return {'status': 'success', 'content': response.text}
            else:
                print(f"Ошибка досnтупа: {response.status_code}")
                return {'status': 'error', 'content': f"Ошибка досnтупа: {response.status_code}"}
        
    except Exception as e:
        return {'status': 'error', 'content': e}



async def parsing_school_site() -> dict:
    """
    Функция, которая будет парсить сайт колледжа, и доставать ссылки на excel с расписанием
    """
    try:
        url = setting.SCHOOL_SHEDULE_SITE
        html_content = await get_site_html(url)
        if html_content["status"] == 'error':
            return {'status': 'error', 'content': html_content["content"]}
        

        soup = BeautifulSoup(html_content["content"], 'html.parser')
        results = []

        links = soup.find_all('a', href=True)

        for link in links:
            url = link['href']
            text_tag = link.find('p', class_='docs-pvz')

            if text_tag:
                title = text_tag.get_text(strip=True)
                download_url = re.sub(r'/edit.*', '/export?format=xlsx', url)

                results.append({
                    'title': title,
                    'url': download_url,
                    'is_change': 'ИЗМЕНЕНИЯ' in title.upper()
                })
            
        return {'status': 'success', 'content': results}


    except Exception as e:
        return {'status': 'error', 'content': e}



async def check_last_schedule_update(action_id: int, name_date: str) -> bool:
    try:
        res = await dbu.get_note_action(action_id, name_date)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        if res['content'] == 'no notes':
            return {'status': 'success', 'content': False}
        
        else:
            return {'status': 'success', 'content': True}

    except Exception as e:
        return {'status': 'error', 'content': e}


# ============== Функция для парсинга и обработки главного расписания =================

async def correct_lesson_nums(df: pd.DataFrame, lesson_col_index: int = 0) -> dict:
    """
    Функция, для корректировки нумерации уроков
    """
    try:
        df = df.copy()
        last_num = 0
        rows_since_last_num = 0 # Счетчик строк внутри одного блока номера

        for i in range(len(df)):
            # 1. Получаем значение ячейки с номером
            val = str(df.iloc[i, lesson_col_index]).strip().lower()
            
            # 2. Анализируем содержимое всей строки (всех групп)
            row_values = [str(x).strip().lower() for x in df.iloc[i, :]]
            
            # Проверяем наличие реальных данных (предмет, препод) во всех колонках правее номера
            has_any_data = any(v not in ["nan", "", "none"] for v in row_values[lesson_col_index + 1:])
            
            # Проверяем наличие маркеров подгрупп (1. / 2. / 1) / 2) )
            has_subgroup_marker = any(re.match(r'^[12]\s?[\.\)]', v) for v in row_values[lesson_col_index + 1:])

            # Если нашли заголовок дня или шапку таблицы - сбрасываем всё
            if "день -" in val or "№" in val:
                last_num = 0
                rows_since_last_num = 0
                continue

            if val.isdigit() and val != "0":
                # Нашли явный номер - это начало блока
                last_num = int(val)
                rows_since_last_num = 1
                df.iloc[i, lesson_col_index] = str(last_num)
            elif has_any_data:
                rows_since_last_num += 1
                
                # Если это маркер подгруппы -> это продолжение того же урока (строка 3 или 4)
                # МЫ НЕ ПИШЕМ СЮДА НОМЕР, чтобы твой парсер не счел это новым уроком
                if has_subgroup_marker:
                    df.iloc[i, lesson_col_index] = "" 
                
                # Если это 3-я или более строка в блоке и нет маркеров подгрупп
                # Значит, это новый урок, который забыли пронумеровать
                elif rows_since_last_num > 2:
                    if last_num > 0:
                        last_num += 1
                        df.iloc[i, lesson_col_index] = str(last_num)
                        rows_since_last_num = 1
                    else:
                        last_num = 1
                        df.iloc[i, lesson_col_index] = str(last_num)
                        rows_since_last_num = 1
                else:
                    # Это 2-я строка (преподаватель)
                    # Оставляем ПУСТЫМ, чтобы твой цикл 'while end_index' включил эту строку в текущий урок
                    df.iloc[i, lesson_col_index] = ""
            else:
                # Если строка абсолютно пустая - сбрасываем счетчик строк блока
                rows_since_last_num = 0
                
        return {'status': 'success', 'content': df} 
    
    except Exception as e:
        return {'status': 'error', 'content': e}



async def parse_college_schedule(xl: pd.ExcelFile, shn: str) -> list:
    """
    Функция для парсинга данных с Excel документа
    """
    df = pd.read_excel(xl, header=None, sheet_name=shn, dtype=str)

    # df = await correct_lesson_nums(df)

    # if df['status'] == 'error':
    #     return {'status': 'error', 'content': df['content']}

    # df = df['content']

    result = []
    current_day = ""
    groups_row = []
    
    i = 0
    while i < len(df):
        row_values = [str(val).strip() if pd.notna(val) else "" for val in df.iloc[i]]
        first_cell = row_values[0]

        if "День -" in first_cell:
            current_day = first_cell.replace("День - ", "").strip()
            i += 1
            continue

        if first_cell == "№":
            groups_row = row_values
            i += 1
            continue

        if first_cell.isdigit():
            lesson_num = first_cell
            start_index = i
            
            end_index = i + 1
            while end_index < len(df):
                next_first_cell = str(df.iloc[end_index, 0]).strip()
                if next_first_cell.isdigit() or "День -" in next_first_cell or next_first_cell == "№":
                    break
                end_index += 1
            

            for col_idx in range(1, len(groups_row) - 1, 2):
                group_name = groups_row[col_idx]
                if not group_name or group_name == "":
                    continue

                combined_content = []
                rooms = []
                
                for r in range(start_index, end_index):
                    subject_val = str(df.iloc[r, col_idx]).strip()
                    room_val = str(df.iloc[r, col_idx + 1]).strip()
                    
                    if subject_val and subject_val != "nan":
                        combined_content.append(subject_val)
                    if room_val and room_val != "nan":
                        rooms.append(room_val)

                if combined_content:
                    
                    full_text = " / ".join(combined_content)
                    unique_rooms = ", ".join(list(dict.fromkeys(rooms)))

                    result.append({
                        "day": current_day,
                        "group": group_name,
                        "lesson_number": lesson_num,
                        "raw_data": combined_content,
                        "full_subject_teacher": full_text,
                        "room": unique_rooms
                    })
            
            i = end_index
        else:
            i += 1
    return result



async def parsing_data_from_remote_excel(excel_url: str = None) -> dict:
    """
    Функция для парсинга excel файлы из ссылки
    """
    try:
        if not isinstance(excel_url, str):
            return {'status': 'error', 'content': f'Ошибка в пути к файлу^ {excel_url}'}
        
        response = requests.get(excel_url)
        
        if response.status_code != 200:
            return {'status': 'error', 'content': 'Не удается цельно скачать Excel файл'}


        xls = pd.ExcelFile(BytesIO(response.content))
        sheets = xls.sheet_names
        

        list_groups = set()
        list_teachers = set()
        list_lesson_group = set()
        list_lessons = []

        for sheet in sheets:
            data = await parse_college_schedule(xls, sheet)

            for obj in data:                
                list_groups.add((obj['group'], datetime.today().strftime('%Y-%m-%d'),))

                # if obj['group'] == 'КП 25-09-3' and obj['day'].replace(" ", "").split(",")[1] == "10.03.2026":
                #     print(obj)

                date_string = obj['day'].replace(" ", "").split(",")[1]
                date_object = datetime.strptime(date_string, "%d.%m.%Y")
                formatted_date = date_object.strftime("%Y-%m-%d")

                if len(obj['raw_data']) == 2:
                    subgroup = 0
                    subject = obj['raw_data'][0].strip()
                    if obj['raw_data'][0].strip()[0].isdigit():
                        subgroup = obj['raw_data'][0].strip()[0]
                        subject = obj['raw_data'][0].strip()[2:]
                    else:
                        subject = obj['raw_data'][0].strip()


                    list_teachers.add((noramizer_teacher_name(obj['raw_data'][1]), datetime.today().strftime('%Y-%m-%d')))
                    list_lesson_group.add((obj['group'], subject,))

                    list_lessons.append(
                        (
                            int(obj['lesson_number']),
                            subject.strip(),
                            obj['group'],
                            subgroup,
                            noramizer_teacher_name(obj['raw_data'][1]).strip(),
                            obj['room'] if obj['room'] != "" else "-",
                            obj['day'].replace(" ", "").split(",")[0],
                            formatted_date,
                            datetime.today().strftime('%Y-%m-%d')
                        )
                    )

                elif len(obj['raw_data']) == 4:
                    subgroup1 = 0
                    subject1 = obj['raw_data'][0].strip()
                    if obj['raw_data'][0].strip()[0].isdigit():
                        subgroup1 = obj['raw_data'][0].strip()[0]
                        subject1 = obj['raw_data'][0].strip()[2:]
                    else:
                        subject1 = obj['raw_data'][0].strip()

                    subgroup2 = 0
                    subject2 = obj['raw_data'][2].strip()
                    if obj['raw_data'][2].strip()[0].isdigit():
                        subgroup2 = obj['raw_data'][2].strip()[0]
                        subject2 = obj['raw_data'][2].strip()[2:]
                    else:
                        subject2 = obj['raw_data'][2].strip()

                    list_teachers.add((noramizer_teacher_name(obj['raw_data'][1]), datetime.today().strftime('%Y-%m-%d'),))
                    list_lesson_group.add((obj['group'], subject1,))

                    list_teachers.add((noramizer_teacher_name(obj['raw_data'][3]), datetime.today().strftime('%Y-%m-%d'),))
                    list_lesson_group.add((obj['group'], subject2,))


                    if len(obj['room'].split(",")) == 1:
                        room1 = obj['room'].split(",")[0]
                        room2 = "-"
                    elif len(obj['room'].split(",")) == 2:
                        room1 = obj['room'].split(",")[0]
                        room2 = obj['room'].split(",")[1]
                    elif len(obj['room'].split(",")) == 0:
                        room1 = "-"
                        room2 = "-"

                    list_lessons.append(
                        (
                            int(obj['lesson_number']),
                            subject1.strip(),
                            obj['group'],
                            subgroup1,
                            noramizer_teacher_name(obj['raw_data'][1]).strip(),
                            room1,
                            obj['day'].replace(" ", "").split(",")[0],
                            formatted_date,
                            datetime.today().strftime('%Y-%m-%d')
                        )
                    )

                    list_lessons.append(
                        (
                            int(obj['lesson_number']),
                            subject2.strip(),
                            obj['group'],
                            subgroup2,
                            noramizer_teacher_name(obj['raw_data'][3]).strip(),
                            room2,
                            obj['day'].replace(" ", "").split(",")[0],
                            formatted_date,
                            datetime.today().strftime('%Y-%m-%d')
                        )
                    )

                                  

        res1 = await dbu.update_groups(list_groups)
        if res1['status'] == 'error':
            return {'status': 'error', 'content': {'name_func': "update_groups", 'error_text': res1['content']}}
        res2 = await dbu.update_teachers(list_teachers)
        if res2['status'] == 'error':
            return {'status': 'error', 'content': {'name_func': "update_teachers", 'error_text': res2['content']}}
        res3 = await dbu.update_lessons_group(list_lesson_group)
        if res3['status'] == 'error':
            return {'status': 'error', 'content': {'name_func': "update_lessons_group", 'error_text': res3['content']}}
        res4 = await dbu.update_lessons(list_lessons)
        if res4['status'] == 'error':
            return {'status': 'error', 'content': {'name_func': "update_lessons", 'error_text': res4['content']}}

        return {'status': 'success'}

        
    except Exception as e:
        print(e)
        return {'status': 'error', 'content': e}
    


async def update_schedule_from_site() -> dict:
    """
    Функция, которая будет вызываться каждую неделю наверное, парсить все основное расписание с документа, и сразу отправлять все в бд
    """
    try:
        url_on_excels = await parsing_school_site()
        if url_on_excels['status'] == 'error':
            return {'status': 'error', 'content': url_on_excels['content']}
                
        url_on_excels = url_on_excels['content']
        url_on_excels = [s for s in url_on_excels if not s['is_change']]
        parsed_schedules = []

        
        for s in url_on_excels:
            match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', s['title'])
            if match:
                date_str = match.group(0)
                date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                
                s['parsed_date'] = date_obj
                parsed_schedules.append(s)
        
        if not parsed_schedules:
            return {'status': 'error', 'content': 'Даты не подходящие!'}

        latest = sorted(parsed_schedules, key=lambda x: x['parsed_date'], reverse=True)[0]
        url_latest = latest['url']

        # last_update = await get_note_action(1)
        # if last_update['status'] == 'error':
        #     return {'status': 'error', 'content': last_update['content']}
        
        # if last_update['content'] == 'no notes':
        #     pass


        # else:
        #     last_update = last_update['content']
        #     date_on_site = datetime.strptime(latest['title'].split(' ')[3], '%d.%m.%Y')
        #     date_on_site = datetime.strftime(date_on_site, '%Y.%m.%d')

        #     print(last_update['date'], date_on_site)

        #     if max(last_update['date'], date_on_site) is last_update['date']:

        check = await check_last_schedule_update(1, str(re.search(r'(\d{2})\.(\d{2})\.(\d{4})', latest['title']).group(0)))
        if check['status'] == 'error':
            return{'status': 'error', "content": res['content']}
        else:
            if check['content']:
                return {'status': 'no action'}


        res = await parsing_data_from_remote_excel(url_latest)

        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        res = await add_note_action_in_bd(1, str(re.search(r'(\d{2})\.(\d{2})\.(\d{4})', latest['title']).group(0)))
        
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        return {'status': 'success'}
        

    except Exception as e:
        return {"status": 'error', 'content': e}

# =====================================================================================




# ============== Функция для парсинга и ообработки ежедневного расписания =============

def fix_lessons(val) -> str:
    if isinstance(val, pd.Timestamp) or hasattr(val, 'month'):
        return f"{val.day}-{val.month}"
    str_val = str(val)
    if '-' in str_val and ' ' in str_val:
        try:
            temp_dt = pd.to_datetime(str_val)
            return f"{temp_dt.day}-{temp_dt.month}"
        except:
            pass
    return str_val



def get_first_word(text) -> str:
    if pd.isna(text) or text == '-':
        return text
    
    return str(text).split('\n')[0]



def get_second_word(text) -> str:
    if pd.isna(text) or text == '-':
        return text
    
    if len(str(text).split('\n')) > 1:
        return str(text).split('\n')[1]
    
    return "-"



def get_last_word(text) -> str:
    if pd.isna(text) or text == '-':
        return text
    
    if len(str(text).split('\n')) > 1:
        return str(text).split('\n')[2]
    
    return "-"



def check_room(text) -> str:
    """
    Проверяет запись с номером кабинета
    """
    if text is None or text == "" or str(text) == "nan":
        return "-"
    
    return text



def get_subg(text: str) -> str:
    subgroup = 0
    text = str(text).split('\n')
    text = text[0].strip()
    if text == "" or text is None or text == "nan":
        return '0'
    elif text[0].isdigit():
        subgroup = text[0]
        return str(subgroup)
    else:
        return str(subgroup)



async def parce_changes_schedule(xl: pd.ExcelFile, shn: str) -> dict:
    """
    Функция, которая будет читать Excel документ и обрабатывать его, возвращая массив с группами
    """
    try:
        df = pd.read_excel(xl, sheet_name=shn, dtype=str, header=None)
        header_mask = df.isin(['Группа', '№ урока']).any(axis=1)
        header_indices = df.index[header_mask].tolist()
        if not header_indices:
            return {'status': 'error', 'content': "Не удалось найти заголовки"}
        
        header_idx = header_indices[0]
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx + 1:].reset_index(drop=True)
        df = df.dropna(how="all", axis=1).dropna(how='all', axis=0)

        df['№ урока'] = df['№ урока'].apply(fix_lessons)
        df['Группа'] = df['Группа'].ffill()
        df['Тип изменения'] = df['Изменения'].apply(get_first_word)
        df['Новый предмет'] = df['Изменения'].apply(get_second_word)
        df['Преподаватель'] = df['Изменения'].apply(get_last_word)
        df['Кабинет'] = df['Кабинет'].apply(check_room)
        df['last_subg'] = df['По расписанию'].apply(get_subg)
        df = df.drop('По расписанию', axis=1)
        df = df.drop('Изменения', axis=1)

        data = []
        for _, row in df.iterrows():
            data.append(
                (row['Группа'], row['№ урока'], row['Тип изменения'], row['Новый предмет'], row['Преподаватель'], row['Кабинет'], row['last_subg'])
            )

        return {'status': 'success', 'content': data}
        

    except Exception as e:
        print(e)
        return {'status': 'error', 'content': str(e)}



async def add_changes_from_site() -> dict:
    """
    Функция, которая будет брать изменения в расписании с сайта, парсить, обрабатывать, добавлять в бд и возвращать группы и преподов, чьё расписание поменяли
    """
    try:
        urls_on_excels = await parsing_school_site()
        if urls_on_excels['status'] == "error":
            return {'status': 'error', 'content': urls_on_excels['content']}
        
        urls_on_excels = urls_on_excels['content']
        urls_on_excels = [s for s in urls_on_excels if s['is_change']]
        url = urls_on_excels[0]['url']

        response = requests.get(url)
        xl = pd.ExcelFile(BytesIO(response.content))
        shs = xl.sheet_names
        shs.sort()
        print(shs)
        tmp_shs = []
        for i in shs:
            day, mouth, year = i.split(".")

            if len(day) != 2:
                print("День не нормализован")
                if day == "0":
                    continue
                else:
                    print("День нормализован")
                    day = "0" + day

            if len(mouth) != 2:
                print("Месяц не нормализован")
                if mouth == "0":
                    continue
                else:
                    print("Месяц нормализован")
                    mouth = "0" + mouth

            if len(year) != 4:
                print("Год не нормализован")
                if year == '202' or year == '026' or year == "226":
                    print("Год нормализован")
                    year = '2026'
                else:
                    continue
            
            res_date = ".".join((day, mouth, year))
            tmp_shs.append(res_date)

        tmp_shs.sort()
        shs = tmp_shs
        print(shs)
        count_updates = 0
        for last_date in shs:
            check = await check_last_schedule_update(2, last_date)
            if check['status'] == 'error':
                return{'status': 'error', "content": check['content']}
            else:
                if check['content']:
                    continue
            
            data = await parce_changes_schedule(xl, last_date)
            if data['status'] == 'error':
                return {'status': 'error', 'content': data['content']}
            # Отмена = 0
            # Будет = 1
            # Замена кабинета = 2
            data = data['content']
            out_data = [] # Структура: (Дата изменения расписания, Название группы, Подгруппа, Тип изменения, Номер урока, Название пары, Кабинет, Препод, Дата внесения изменений в бд)
            list_changes_for_groups = []
            list_changes_for_teachers = []

            for item in data:
                list_changes_for_groups.append(item[0])
                
                if item[4] != "-":
                    list_changes_for_teachers.append(item[4])

                type_change = 0

                if item[2].lower() == 'отмена': type_change = 0
                elif item[2].lower() == 'будет' or item[2].lower() == 'замена': type_change = 1
                elif item[2].lower() == 'замена кабинета': type_change = 2
                else: type_change = -1

                subgroup = 0
                subject = ""
                if item[3].strip()[0].isdigit():
                    subgroup = item[3].strip()[0]
                    subject = item[3].strip()[2:]
                else:
                    subject = item[3].strip()

                less_nums = item[1].split('-')
                if len(less_nums) == 1:
                    out_data.append(
                        (last_date, item[0], subgroup, type_change, int(item[1]), subject, item[5], item[4], datetime.today().strftime('%Y-%m-%d'), item[6])
                    )
                else:
                    for n in range(int(less_nums[0]), int(less_nums[1]) + 1):
                        out_data.append(
                        (last_date, item[0], subgroup, type_change, n, subject, item[5], item[4], datetime.today().strftime('%Y-%m-%d'), item[6])
                    )
                
            list_changes_for_groups = list(set(list_changes_for_groups))
            list_changes_for_teachers = list(set(list_changes_for_teachers))

            full_data = {"date": last_date, "groups": list_changes_for_groups, 'theachers': list_changes_for_teachers}
            func_for_check_result(full_data, f'list_date_{last_date}')


            res = await dbu.change_lessons_change(out_data)
            if res['status'] == 'error':
                return {'status': 'error', 'content': res['content']}
                
            res = await add_note_action_in_bd(2, last_date)
            if res['status'] == 'error':
                    return {'status': 'error', 'content': res['content']}
            
            count_updates += 1
            
        if count_updates == 0:
            return {'status': 'no action'}
        
        return {'status': 'success'}
    

    except Exception as e:
        return {'status': 'error', 'content': e}

# =====================================================================================




# ========================== Добавить запись об изменениях в бд =======================

async def add_note_action_in_bd(type_action: int, last_date: str) -> dict:
    """
    Функция, для добавления в бд записи об определенных действиях системы
    1 = Изменение всего расписания
    2 = Какие либо изменения в расписании
    """
    try:
        res = await dbu.add_note_action(type_action, last_date)
        if res["status"] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'content': e}
    


async def get_note_action_in_bd(type_action: int) -> dict:
    """
    Функция, для запроса из бд записи об определенных действиях системы
    1 = Изменение всего расписания
    2 = Какие либо изменения в расписании
    """
    try:
        res = await dbu.get_note_action(type_action)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
            
        return {'status': 'success', 'content': res}
    except Exception as e:
        return {'status': 'error', 'content': e}

# =================================== Добавление расписания звонков ===================

async def add_times_less_for_days(data: dict) -> dict:
    """
    Функция, для добавления в бд расписания звонков занятий
    """
    try:
        day_type_name = data['day_code']
        params = []
        for i in data['lessons']:
            l_num = i['lesson_number']
            l_s = i['lesson_start']
            l_e = i['lesson_end']

            params.append((day_type_name, l_num, l_s, l_e))

        res = await dbu.add_times_less_for_day(params)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        return {'status': 'success'}

    except Exception as e:
        return {'status': 'error', 'content': e}

# =====================================================================================





# ================================ Инициализация БД ===================================

async def initialization_database() -> dict:
    """
    Функция для инициализации и заполнения базы данных
    Инициализируются таблицы, созадется дефолтное расписание звонков
    """
    try:
        res = await dbu.init_databse()
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        lessons_bud = {
                    'day_code': 1,
                        'lessons': 
                [
                    {
                        'lesson_number': '1',
                        'lesson_start': '8:15',   
                        'lesson_end': '9:00'
                    },
                    {
                        'lesson_number': '2',
                        'lesson_start': '9:00',   
                        'lesson_end': '9:45'
                    },
                    {
                        'lesson_number': '3',
                        'lesson_start': '9:55',   
                        'lesson_end': '10:40'
                    },
                    {
                        'lesson_number': '4',
                        'lesson_start': '10:40',   
                        'lesson_end': '11:25'
                    },
                    {
                        'lesson_number': '5',
                        'lesson_start': '12:00',   
                        'lesson_end': '12:45'
                    },
                    {
                        'lesson_number': '6',
                        'lesson_start': '12:45',   
                        'lesson_end': '13:30'
                    },
                    {
                        'lesson_number': '7',
                        'lesson_start': '13:45',   
                        'lesson_end': '14:30'
                    },
                    {
                        'lesson_number': '8',
                        'lesson_start': '14:30',   
                        'lesson_end': '15:15'
                    },
                    {
                        'lesson_number': '9',
                        'lesson_start': '15:40',   
                        'lesson_end': '16:25'
                    },
                    {
                        'lesson_number': '10',
                        'lesson_start': '16:25',   
                        'lesson_end': '17:10'
                    },
                    {
                        'lesson_number': '11',
                        'lesson_start': '17:20',   
                        'lesson_end': '18:05'
                    },
                    {
                        'lesson_number': '12',
                        'lesson_start': '18:05',   
                        'lesson_end': '18:50'
                    },
                ]
        }
        res = await add_times_less_for_days(lessons_bud)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        lessons_s = {
            'day_code': 2,
            'lessons': [
                {
                    'lesson_number': '1',
                    'lesson_start': '8:15',   
                    'lesson_end': '9:00'
                },
                {
                    'lesson_number': '2',
                    'lesson_start': '9:00',   
                    'lesson_end': '9:45'
                },
                {
                    'lesson_number': '3',
                    'lesson_start': '9:50',   
                    'lesson_end': '10:35'
                },
                {
                    'lesson_number': '4',
                    'lesson_start': '10:35',   
                    'lesson_end': '11:20'
                },
                {
                    'lesson_number': '5',
                    'lesson_start': '11:35',   
                    'lesson_end': '12:20'
                },
                {
                    'lesson_number': '6',
                    'lesson_start': '12:20',   
                    'lesson_end': '13:05'
                },
                {
                    'lesson_number': '7',
                    'lesson_start': '13:20',   
                    'lesson_end': '14:05'
                },
                {
                    'lesson_number': '8',
                    'lesson_start': '14:05',   
                    'lesson_end': '14:50'
                },
                {
                    'lesson_number': '9',
                    'lesson_start': '15:05',   
                    'lesson_end': '15:50'
                },
                {
                    'lesson_number': '10',
                    'lesson_start': '15:50',   
                    'lesson_end': '16:35'
                },
                {
                    'lesson_number': '11',
                    'lesson_start': '16:40',   
                    'lesson_end': '17:25'
                },
                {
                    'lesson_number': '12',
                    'lesson_start': '17:25',   
                    'lesson_end': '18:10'
                },
            ]
        }
        res = await add_times_less_for_days(lessons_s)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}


        return {"status": 'success'}

    except Exception as e:
        return {'status': 'error', 'content': e}

# =====================================================================================

# ==================================== Получить расписание ============================
async def get_schedule_from_bd(chat_id: str, date: str, engine: QApplication) -> dict:
    """Функция, для получения расписания из БД, по id чата"""
    try:
        res = await dbu.get_info_user(chat_id)
        if res['status'] == 'error':
            return {'status': 'error', 'content': res['content']}
        
        
        type_res = res['content'][8]
        sch_img_res = ""
                        
        res = res['content'] # (id, name, second_name, username, role, group_id, subgroup, teacher_name_id, type_away_schedule)
        schedule = {}

        if res[4] == 0: # Студент
            schedule = await dbu.get_schedule_for_student_by_group_and_subgroup(res[5], str(res[6]), date)
            if schedule['status'] == 'error':
                return {'status': 'error', 'content': schedule['content']}
        
        elif res[4] == 1: # Препод
            schedule = await dbu.get_schedule_for_theacher_by_teacher_name(res[7], date)
            if schedule['status'] == 'error':
                return {'status': 'error', 'content': schedule['content']}
            
        # func_for_check_result(schedule)

        if type_res == 0:
            return {'status': 'success', 'content': {"type_schedule": 'text', 'schedule': schedule['content']}}
        
        else:
            sch_img = await create_image_schedule.save_schedule_image(data=schedule, role=res[4], app=engine)
            if sch_img['status'] == 'error':
                print(sch_img['content'])
                return {'status': 'fail_img', 'content': schedule['content']}
            
            sch_img_res = sch_img['content']

            return {'status': 'success', 'content':  {"type_schedule": 'img', 'schedule': sch_img_res}}

        
    except Exception as e:
        return {'status': 'error', 'content': e}

# =====================================================================================


if __name__ == "__main__":
    raise RuntimeWarning("Не предназначен для самостоятельного запуска")
