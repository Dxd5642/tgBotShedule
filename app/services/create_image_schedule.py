from PySide6.QtGui import QImage, QPainter, QTextDocument, QColor
from PySide6.QtCore import QBuffer, QIODevice, QByteArray
import io, base64
from app.core.config import setting


async def qimage_to_bytes(qimage):
    try:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        qimage.save(buffer, "PNG")
        buffer.close()
        return {'status': 'success', 'content': io.BytesIO(byte_array.data())}
    except Exception as e:
        return {'status': 'error', 'content': str(e)}


async def generate_html_rows(lessons, role):
    try:
        pairs = {}
        for i in range(1, 7):
            pair_lessons = [l for l in lessons if (i*2-1) <= l['lesson_number'] <= (i*2)]
            pairs[i] = sorted(pair_lessons, key=lambda x: x['lesson_number'])

        rows_html = ""
        for pair_num, p_lessons in pairs.items():
            l1_num, l2_num = pair_num * 2 - 1, pair_num * 2
            l1 = next((l for l in p_lessons if l['lesson_number'] == l1_num), None)
            l2 = next((l for l in p_lessons if l['lesson_number'] == l2_num), None)


            should_merge = (
                l1 and l2 and 
                l1['lesson_name'] == l2['lesson_name'] and 
                l1['room'] == l2['room'] and
                l1['subgroup'] == l2['subgroup']
            )

            if should_merge:
                rows_html += f"""
                <tr>
                    <td rowspan="2">{pair_num}</td>
                    <td>{l1_num}</td>
                    <td rowspan="2">{l1['lesson_name']}{'<br> Подгруппа: ' + str(l1['subgroup']) if l1['subgroup'] != 0 else ''}</td>
                    <td rowspan="2">{l1['teacher_name'] if role == 0 else l1['name_group']}</td>
                    <td rowspan="2">{l1['room']}</td>
                    <td rowspan="2">{l1['lesson_time_start']} - {l2['lesson_time_end']}</td>
                </tr>
                <tr>
                    <td>{l2_num}</td>
                </tr>
                """
            else:
                def format_lesson(l, num):
                    if l:
                        sub = '<br> Подгруппа: ' + str(l['subgroup']) if l['subgroup'] != 0 else ''
                        return f"<td>{num}</td><td>{l['lesson_name']}{sub}</td><td>{l['teacher_name'] if role == 0 else l1['name_group']}</td><td>{l['room']}</td><td>{l['lesson_time_start']}-{l['lesson_time_end']}</td>"
                    return f"<td>{num}</td><td></td><td></td><td></td><td></td>"

                rows_html += f"<tr><td rowspan='2'>{pair_num}</td>{format_lesson(l1, l1_num)}</tr>"
                rows_html += f"<tr>{format_lesson(l2, l2_num)}</tr>"

        return {'status': 'success', 'content': rows_html}
    except Exception as e:
        return {'status': 'error', 'content': str(e)}


async def save_schedule_image(data, role=0, app=None):
    try:
        for_some_sch = data['content']['group'] if role == 0 else data['content']['teacher_name']
        rows = await generate_html_rows(data['content']['lessons'], role)
        if rows['status'] == 'error':
            return {'status': 'error', 'content': rows['content']}
        
        rows = rows['content']

        day_date = ".".join(data['content']['date'].split("-")[::-1])
        day_name = data['content']['day_name']

        full_html = f"""
        <head>
            <meta charset="UTF-8">
            <style>
                * {{ color: black; }}
                table {{ 
                    width: 1110px; 
                    min-width: 1110px;
                    border-collapse: collapse; 
                    font-family: Arial, sans-serif; 
                    text-align: center;
                    background-color: white;
                    table-layout: fixed;
                    word-wrap: break-word;
                }}
                th, td {{ 
                    border: 2px solid black; 
                    padding: 8px; 
                    height: 30px; 
                    font-size: 18px; 
                    color: black; 
                    text-align: center;
                    vertical-align: middle;
                }}
                .header-title {{ font-size: 22px; font-weight: bold; }}
                .pairs{{font-size: 2px}}

            </style>
        </head>
        <body style="width: 1100px; height: 770px; margin: 0; background: white;">
            <table>
                <thead>
                    <tr><th class="header-title" colspan="6" style="background-color: #7084B9; color: white; border: 1px solid black">Расписание занятий для {for_some_sch} | {day_date} ({day_name})</th></tr>
                    <tr>
                        <th class="col-pair" style="background-color: #7084B9; color: white; border: 2px solid black">№ пары</th>
                        <th class="col-num" style="background-color: #7084B9; color: white; border: 2px solid black">№ урока</th>
                        <th class="col-class" style="background-color: #7084B9; color: white; border: 2px solid black">Предмет</th>
                        <th style="background-color: #7084B9; color: white; border: 2px solid black">{'Преподаватель' if role==0 else 'Группа'}</th>
                        <th style="background-color: #7084B9; color: white; border: 2px solid black">Кабинет</th>
                        <th style="background-color: #7084B9; color: white; border: 2px solid black">Время</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        """

        doc = QTextDocument()

        doc.setPageSize(QImage(1110, 780, QImage.Format_ARGB32).size())
        doc.setHtml(full_html)

        content_height = int(doc.size().height()) + 10

        image = QImage(1110, content_height, QImage.Format_ARGB32)
        image.fill(QColor("white")) 

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        
        doc.drawContents(painter)
        painter.end()

        output_path = setting.BASE_DIR / "img_shedule.png"

        if image.save(output_path):
           print(f"Картинка успешно создана: {output_path}")
        else:
            print("Не удалось сохранить изображение")

        image = await qimage_to_bytes(image)
        if image['status'] == 'error':
            return {'status': 'error', 'content': image['content']}
        
        img_bytes = image['content'].getvalue()
        base64_str = base64.b64encode(img_bytes).decode('utf-8')

        return {'status': 'success', 'content': base64_str}

    except Exception as e:
        return {'status': 'error', 'content': str(e)}
    
    
