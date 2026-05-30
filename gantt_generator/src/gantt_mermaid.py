import pandas as pd


STATUS_MAP = {
    'done': 'done',
    'active': 'active',
    'critical': 'crit',
    'milestone': 'milestone',
    'pending': '',
}

VIEW_MODE_CONFIGS = {
    'Day': {
        'axisFormat': '%m-%d',
        'tickInterval': None,
        'weekday': None,
    },
    'Week': {
        'axisFormat': '%Y-%m-%d',
        'tickInterval': '1week',
        'weekday': 'monday',
    },
    'Month': {
        'axisFormat': '%Y-%m',
        'tickInterval': '1month',
        'weekday': None,
    },
}


def generate_mermaid_code(
    df: pd.DataFrame,
    project_name: str,
    view_mode: str = 'Day',
    show_progress: bool = True,
    show_today: bool = True,
) -> str:
    view_config = VIEW_MODE_CONFIGS.get(view_mode, VIEW_MODE_CONFIGS['Day'])

    lines = [
        'gantt',
        f'    title {project_name}',
        '    dateFormat YYYY-MM-DD',
        f'    axisFormat {view_config["axisFormat"]}',
    ]

    if show_today:
        lines.append('    todayMarker stroke-width:2px,stroke:#d62728,opacity:0.8')

    if view_config['tickInterval']:
        lines.append(f'    tickInterval {view_config["tickInterval"]}')
    if view_config['weekday']:
        lines.append(f'    weekday {view_config["weekday"]}')

    groups = df.groupby('group', sort=False)
    task_counter = 0

    for group_name, group_df in groups:
        lines.append(f'    section {group_name}')

        for _, row in group_df.iterrows():
            task_counter += 1
            task_id = f't{task_counter}'
            start = row['start'].strftime('%Y-%m-%d')
            end = row['end'].strftime('%Y-%m-%d')
            status = STATUS_MAP.get(str(row.get('status', 'pending')), '')
            status_prefix = f'{status}, ' if status else ''

            task_name = row['name']
            if show_progress and row.get('progress', 0) > 0:
                task_name = f'{task_name} [{row["progress"]}%]'

            lines.append(f'    {task_name} :{status_prefix}{task_id}, {start}, {end}')

    return '\n'.join(lines)
