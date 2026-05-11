import uuid

from app.models.practice import PracticeItem



def _submission_from_answer(answer_json):
    if isinstance(answer_json, dict):
        keywords = answer_json.get("keywords", [])
        return " ".join(keywords)
    return answer_json



def test_progress_endpoints_round_trip(client) -> None:
    record_response = client.post(
        "/api/v1/progress/records",
        json={
            "record_type": "study",
            "subject": "math",
            "duration_minutes": 45,
            "score": 92,
            "reference_type": "manual",
        },
    )
    assert record_response.status_code == 201

    mastery_response = client.post(
        "/api/v1/progress/mastery",
        json={
            "knowledge_point": "函数极限",
            "subject": "math",
            "mastery_score": 78,
            "accuracy_rate": 80,
        },
    )
    assert mastery_response.status_code == 200
    assert mastery_response.json()["knowledge_point"] == "函数极限"

    review_response = client.post(
        "/api/v1/progress/reviews",
        json={
            "knowledge_point": "函数极限",
            "subject": "math",
            "scheduled_for": "2026-04-08",
            "status": "pending",
            "review_payload": {"source": "manual"},
        },
    )
    assert review_response.status_code == 201

    overview_response = client.get("/api/v1/progress/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["stats"]["total_learning_records"] == 1
    assert overview["stats"]["total_study_minutes"] == 45
    assert overview["stats"]["due_review_count"] == 1

    records_response = client.get("/api/v1/progress/records", params={"subject": "math"})
    assert records_response.status_code == 200
    assert records_response.json()[0]["record_type"] == "study"

    mastery_list_response = client.get("/api/v1/progress/mastery", params={"subject": "math"})
    assert mastery_list_response.status_code == 200
    assert mastery_list_response.json()[0]["knowledge_point"] == "函数极限"

    reviews_list_response = client.get("/api/v1/progress/reviews", params={"status": "pending", "due_only": True})
    assert reviews_list_response.status_code == 200
    assert len(reviews_list_response.json()) == 1



def test_practice_attempt_updates_progress_and_wrong_questions(client, session_factory) -> None:
    generate_response = client.post(
        "/api/v1/practice/generate",
        json={
            "subject": "math",
            "knowledge_points": ["函数极限", "连续性"],
            "item_count": 4,
            "difficulty": "medium",
            "item_types": ["single", "fill", "short", "multiple"],
        },
    )
    assert generate_response.status_code == 201
    practice_set = generate_response.json()
    set_id = uuid.UUID(practice_set["id"])
    assert len(practice_set["items"]) == 4

    with session_factory() as db:
        items = (
            db.query(PracticeItem)
            .filter(PracticeItem.set_id == set_id)
            .order_by(PracticeItem.created_at.asc())
            .all()
        )
        answers = []
        for index, item in enumerate(items):
            if index == len(items) - 1:
                submitted = "错误答案"
            else:
                submitted = _submission_from_answer(item.answer_json)
            answers.append({"item_id": str(item.id), "answer_json": submitted})

    submit_response = client.post(
        f"/api/v1/practice/sets/{set_id}/attempts",
        json={"answers": answers, "duration_minutes": 25},
    )
    assert submit_response.status_code == 201
    attempt = submit_response.json()
    attempt_id = attempt["id"]
    assert attempt["status"] == "graded"
    assert len(attempt["answers"]) == 4
    assert any(answer["is_correct"] is False for answer in attempt["answers"])

    attempt_detail_response = client.get(f"/api/v1/practice/attempts/{attempt_id}")
    assert attempt_detail_response.status_code == 200
    assert attempt_detail_response.json()["id"] == attempt_id

    wrong_questions_response = client.get("/api/v1/practice/wrong-questions", params={"subject": "math"})
    assert wrong_questions_response.status_code == 200
    wrong_questions = wrong_questions_response.json()
    assert len(wrong_questions) == 1
    assert wrong_questions[0]["practice_set_id"] == str(set_id)

    overview_response = client.get("/api/v1/progress/overview")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["stats"]["total_learning_records"] == 1
    assert overview["stats"]["total_study_minutes"] == 25

    mastery_response = client.get("/api/v1/progress/mastery", params={"subject": "math"})
    assert mastery_response.status_code == 200
    assert len(mastery_response.json()) >= 1

    records_response = client.get("/api/v1/progress/records", params={"subject": "math"})
    assert records_response.status_code == 200
    assert records_response.json()[0]["reference_type"] == "practice_set"
