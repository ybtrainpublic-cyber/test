from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from math import ceil

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'  # Flash 메시지를 위한 시크릿 키

EXCEL_FILE = 'Robot02.xlsx'

# --- 데이터 로딩 및 저장 함수 ---
def get_data():
    """Excel 파일에서 Robots와 Tasks 데이터를 읽어옵니다."""
    try:
        # Excel 파일의 모든 시트 이름을 가져옵니다.
        xls = pd.ExcelFile(EXCEL_FILE, engine='openpyxl')
        sheet_names = xls.sheet_names

        # 'Robots' 시트가 있으면 읽고, 없으면 빈 데이터프레임을 생성합니다.
        if 'Robots' in sheet_names:
            robots_df = pd.read_excel(xls, sheet_name='Robots')
        else:
            robots_df = pd.DataFrame(columns=['robot_id', 'robot_name', 'model'])

        # 'Tasks' 시트가 있으면 읽고, 없으면 빈 데이터프레임을 생성합니다.
        if 'Tasks' in sheet_names:
            tasks_df = pd.read_excel(xls, sheet_name='Tasks')
        else:
            tasks_df = pd.DataFrame(columns=['task_id', 'robot_id', 'task_name', 'status'])

        return robots_df, tasks_df
    except FileNotFoundError:
        # 파일이 없으면 빈 데이터프레임을 생성합니다.
        return pd.DataFrame(columns=['robot_id', 'robot_name', 'model']), pd.DataFrame(columns=['task_id', 'robot_id', 'task_name', 'status'])

def save_data(robots_df, tasks_df):
    """데이터프레임을 Excel 파일의 각 시트에 저장합니다."""
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        robots_df.to_excel(writer, sheet_name='Robots', index=False)
        tasks_df.to_excel(writer, sheet_name='Tasks', index=False)

# --- 라우트 (웹 페이지) ---

# 메인 페이지 (로봇 및 작업 목록 조회)
@app.route('/')
def index():
    # 1. 데이터 로딩
    robots_df, tasks_df = get_data()

    # 2. 검색 기능
    search_query = request.args.get('q', '').strip()
    if search_query:
        # 로봇 이름 또는 모델명으로 검색
        robot_mask = robots_df['robot_name'].str.contains(search_query, case=False, na=False) | \
                     robots_df['model'].str.contains(search_query, case=False, na=False)
        
        # 작업 이름으로 검색
        task_mask = tasks_df['task_name'].str.contains(search_query, case=False, na=False)
        
        # 검색된 작업에 해당하는 로봇 ID 가져오기
        robot_ids_from_tasks = tasks_df[task_mask]['robot_id'].unique()
        
        # 두 검색 결과를 합쳐서 해당하는 로봇 ID 필터링
        robot_ids_mask = robots_df['robot_id'].isin(robot_ids_from_tasks)
        
        # 최종적으로 보여줄 로봇들
        robots_df = robots_df[robot_mask | robot_ids_mask]

    # 3. 정렬 기능
    sort_by = request.args.get('sort', 'name_asc')
    if sort_by == 'name_asc':
        robots_df = robots_df.sort_values(by='robot_name', ascending=True)
    elif sort_by == 'name_desc':
        robots_df = robots_df.sort_values(by='robot_name', ascending=False)

    # 4. 페이지네이션 기능
    page = request.args.get('page', 1, type=int)
    PER_PAGE = 3  # 한 페이지에 3개의 로봇을 보여줌
    total_robots = len(robots_df)
    total_pages = ceil(total_robots / PER_PAGE)
    
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_robots_df = robots_df.iloc[start:end]

    # 5. 최종 데이터 가공 (페이지네이션된 로봇에 대해서만)
    robots_list = []
    for _, robot in paginated_robots_df.iterrows():
        robot_dict = robot.to_dict()
        robot_dict['tasks'] = tasks_df[tasks_df['robot_id'] == robot['robot_id']].to_dict('records')
        robots_list.append(robot_dict)
        
    return render_template('index.html', 
                           robots=robots_list,
                           page=page,
                           total_pages=total_pages,
                           search_query=search_query,
                           sort_by=sort_by)

# 로봇 추가
@app.route('/robot/add', methods=['GET', 'POST'])
def add_robot():
    if request.method == 'POST':
        robots_df, tasks_df = get_data()
        
        # 새 로봇 ID 생성 (기존 ID가 없으면 1, 있으면 최대값 + 1)
        new_id = 1 if robots_df.empty or robots_df['robot_id'].max() != robots_df['robot_id'].max() else robots_df['robot_id'].max() + 1
        
        new_robot = pd.DataFrame([{
            'robot_id': new_id,
            'robot_name': request.form['robot_name'],
            'model': request.form['model']
        }])
        
        robots_df = pd.concat([robots_df, new_robot], ignore_index=True)
        save_data(robots_df, tasks_df)
        
        flash('새로운 로봇이 추가되었습니다.')
        return redirect(url_for('index'))
        
    return render_template('robot_form.html', action='add', robot=None)

# 로봇 수정
@app.route('/robot/edit/<int:robot_id>', methods=['GET', 'POST'])
def edit_robot(robot_id):
    robots_df, tasks_df = get_data()
    robot = robots_df[robots_df['robot_id'] == robot_id].iloc[0]

    if request.method == 'POST':
        # 데이터프레임에서 해당 로봇 정보 업데이트
        robots_df.loc[robots_df['robot_id'] == robot_id, 'robot_name'] = request.form['robot_name']
        robots_df.loc[robots_df['robot_id'] == robot_id, 'model'] = request.form['model']
        save_data(robots_df, tasks_df)
        
        flash('로봇 정보가 수정되었습니다.')
        return redirect(url_for('index'))

    return render_template('robot_form.html', action='edit', robot=robot.to_dict())

# 로봇 삭제
@app.route('/robot/delete/<int:robot_id>', methods=['POST'])
def delete_robot(robot_id):
    robots_df, tasks_df = get_data()
    
    # 로봇과 관련된 작업(Task)들도 함께 삭제
    robots_df = robots_df[robots_df['robot_id'] != robot_id]
    tasks_df = tasks_df[tasks_df['robot_id'] != robot_id]
    
    save_data(robots_df, tasks_df)
    flash('로봇과 관련 작업들이 삭제되었습니다.')
    return redirect(url_for('index'))

# 작업 추가
@app.route('/task/add/<int:robot_id>', methods=['GET', 'POST'])
def add_task(robot_id):
    if request.method == 'POST':
        robots_df, tasks_df = get_data()
        
        # 새 작업 ID 생성
        new_id = 101 if tasks_df.empty or tasks_df['task_id'].max() != tasks_df['task_id'].max() else tasks_df['task_id'].max() + 1
        
        new_task = pd.DataFrame([{
            'task_id': new_id,
            'robot_id': robot_id,
            'task_name': request.form['task_name'],
            'status': request.form['status']
        }])
        
        tasks_df = pd.concat([tasks_df, new_task], ignore_index=True)
        save_data(robots_df, tasks_df)
        
        flash('새로운 작업이 추가되었습니다.')
        return redirect(url_for('index'))
        
    return render_template('task_form.html', action='add', task=None, robot_id=robot_id)

# 작업 수정
@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    robots_df, tasks_df = get_data()
    task = tasks_df[tasks_df['task_id'] == task_id].iloc[0]

    if request.method == 'POST':
        tasks_df.loc[tasks_df['task_id'] == task_id, 'task_name'] = request.form['task_name']
        tasks_df.loc[tasks_df['task_id'] == task_id, 'status'] = request.form['status']
        save_data(robots_df, tasks_df)
        
        flash('작업 정보가 수정되었습니다.')
        return redirect(url_for('index'))

    return render_template('task_form.html', action='edit', task=task.to_dict(), robot_id=task['robot_id'])

# 작업 삭제
@app.route('/task/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    robots_df, tasks_df = get_data()
    
    tasks_df = tasks_df[tasks_df['task_id'] != task_id]
    
    save_data(robots_df, tasks_df)
    flash('작업이 삭제되었습니다.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # openpyxl이 설치되어 있는지 확인
    try:
        import openpyxl
    except ImportError:
        print("openpyxl 라이브러리가 필요합니다. 'pip install openpyxl' 명령어로 설치해주세요.")
        exit()
    
    # 파일이 없으면 초기 데이터로 생성
    if not os.path.exists(EXCEL_FILE):
        print(f"'{EXCEL_FILE}'을 찾을 수 없습니다. 초기 데이터로 파일을 생성합니다.")
        initial_robots = pd.DataFrame({
            'robot_id': [1, 2],
            'robot_name': ['로봇A', '로봇B'],
            'model': ['Model-X', 'Model-Y']
        })
        initial_tasks = pd.DataFrame({
            'task_id': [101, 102, 103],
            'robot_id': [1, 1, 2],
            'task_name': ['부품 조립', '품질 검사', '자재 운반'],
            'status': ['완료', '진행중', '대기']
        })
        save_data(initial_robots, initial_tasks)
        print("파일 생성 완료.")

    app.run(debug=True)