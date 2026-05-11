from datetime import date, timedelta
import uuid

from app.models.planner import StudyTask, TaskPriority, TaskSource, TaskStatus


def test_generate_plan_persists_tasks_and_replaces_pending_ai_tasks(client, session_factory, test_user) -> None:
    goal_math_response = client.post(
        "/api/v1/planner/goals",
        json={"title": "高数冲刺", "deadline": "2026-12-31", "subject": "math"},
    )
    assert goal_math_response.status_code == 201
    math_goal = goal_math_response.json()
    math_goal_id = uuid.UUID(math_goal["id"])

    goal_english_response = client.post(
        "/api/v1/planner/goals",
        json={"title": "英语阅读", "deadline": "2026-12-31", "subject": "english"},
    )
    assert goal_english_response.status_code == 201
    english_goal = goal_english_response.json()
    english_goal_id = uuid.UUID(english_goal["id"])

    today = date.today()
    tomorrow = today + timedelta(days=1)

    with session_factory() as db:
        pending_ai_task = StudyTask(
            user_id=test_user.id,
            goal_id=math_goal_id,
            title="旧的 AI 任务",
            task_date=today,
            duration_minutes=30,
            priority=TaskPriority.medium,
            status=TaskStatus.pending,
            source=TaskSource.ai,
        )
        completed_ai_task = StudyTask(
            user_id=test_user.id,
            goal_id=english_goal_id,
            title="已完成 AI 任务",
            task_date=today,
            duration_minutes=45,
            priority=TaskPriority.medium,
            status=TaskStatus.completed,
            source=TaskSource.ai,
        )
        manual_task = StudyTask(
            user_id=test_user.id,
            goal_id=math_goal_id,
            title="手动任务",
            task_date=today,
            duration_minutes=60,
            priority=TaskPriority.high,
            status=TaskStatus.pending,
            source=TaskSource.manual,
        )
        db.add_all([pending_ai_task, completed_ai_task, manual_task])
        db.commit()
        pending_ai_task_id = str(pending_ai_task.id)
        completed_ai_task_id = str(completed_ai_task.id)
        manual_task_id = str(manual_task.id)

    generate_response = client.post(
        "/api/v1/planner/generate",
        json={
            "goal_ids": [math_goal["id"], english_goal["id"]],
            "days": 2,
            "daily_minutes": 120,
        },
    )
    assert generate_response.status_code == 201
    snapshot = generate_response.json()

    assert snapshot["plan_json"]["persisted_task_count"] == 3
    assert snapshot["plan_json"]["reused_existing_ai_task_count"] == 1
    assert snapshot["plan_json"]["replaced_pending_ai_task_count"] == 1
    assert len(snapshot["plan_json"]["generated_task_ids"]) == 3

    day_one_tasks = snapshot["plan_json"]["days"][0]["tasks"]
    reused_day_one = next(task for task in day_one_tasks if task["goal_id"] == english_goal["id"])
    assert reused_day_one["task_id"] == completed_ai_task_id
    assert reused_day_one["reused_existing"] is True
    assert reused_day_one["status"] == "completed"

    tasks_response = client.get("/api/v1/planner/tasks")
    assert tasks_response.status_code == 200
    tasks = tasks_response.json()
    task_ids = {task["id"] for task in tasks}

    assert pending_ai_task_id not in task_ids
    assert completed_ai_task_id in task_ids
    assert manual_task_id in task_ids
    assert len(tasks) == 5

    generated_math_today = [
        task for task in tasks
        if task["goal_id"] == math_goal["id"] and task["task_date"] == today.isoformat() and task["source"] == "ai"
    ]
    assert len(generated_math_today) == 1
    assert generated_math_today[0]["metadata_json"]["planner_snapshot_id"] == snapshot["id"]

    generated_tomorrow = [
        task for task in tasks
        if task["task_date"] == tomorrow.isoformat() and task["source"] == "ai"
    ]
    assert len(generated_tomorrow) == 2
