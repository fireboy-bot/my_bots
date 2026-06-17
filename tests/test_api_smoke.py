"""
Smoke-тесты Flask API (День 4 — WORK_COMPASS).
Проверяем контракт эндпоинтов, не полный паритет с Telegram.
"""

import json

from web.api_server import storage


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "chislyandia-web-adapter"


def test_profile_not_found(client):
    r = client.get("/api/player/888888888/profile")
    assert r.status_code == 200
    assert r.get_json().get("error")


def test_profile_alias_progress(client, seeded_user, user_id):
    for path in (f"/api/player/{user_id}/profile", f"/api/game/progress/{user_id}"):
        r = client.get(path)
        assert r.status_code == 200
        data = r.get_json()
        assert data["user_id"] == user_id
        assert data["score_balance"] == 500
        assert "unlocked_zones" in data


def test_get_worlds(client, seeded_user, user_id):
    r = client.get(f"/api/game/worlds/{user_id}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["user_id"] == user_id
    worlds = data.get("worlds", [])
    assert len(worlds) >= 4
    addition = next(w for w in worlds if w["id"] == "addition")
    assert addition["unlocked"] is True
    locked = [w for w in worlds if not w["unlocked"]]
    assert len(locked) >= 1


def test_get_task_locked_world(client, seeded_user, user_id):
    r = client.get(f"/api/game/task?user_id={user_id}&world=logic_world")
    assert r.status_code == 403


def test_level_start_and_progress(client, seeded_user, user_id):
    r = client.post(
        "/api/game/level/start",
        data=json.dumps({"user_id": user_id, "world": "addition"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["task"]["id"]
    assert data["run_progress"]["current"] == 1
    assert data["run_progress"]["total"] == 10

    task = data["task"]
    r_answer = client.post(
        "/api/game/answer",
        data=json.dumps(
            {
                "user_id": user_id,
                "answer": task["correct_answer"],
                "task_id": task["id"],
                "island_id": "addition",
                "operation_type": task.get("operation_type", "2digit_add"),
            }
        ),
        content_type="application/json",
    )
    assert r_answer.status_code == 200
    result = r_answer.get_json()
    assert result["correct"] is True
    assert result.get("next_task") or result.get("run_progress")
    chaos = result.get("chaos_state")
    assert chaos is not None


def test_level_run_reduces_chaos_on_correct(client, seeded_user, user_id):
    user = storage.get_user(user_id)
    user["chaos_energy"] = 60
    user["consecutive_errors"] = 2
    user["rift_stage"] = 1
    storage.save_user(user_id, user)
    r = client.post(
        "/api/game/level/start",
        data=json.dumps({"user_id": user_id, "world": "addition"}),
        content_type="application/json",
    )
    task = r.get_json()["task"]
    r_answer = client.post(
        "/api/game/answer",
        data=json.dumps(
            {
                "user_id": user_id,
                "answer": task["correct_answer"],
                "task_id": task["id"],
                "island_id": "addition",
                "operation_type": task.get("operation_type", "2digit_add"),
            }
        ),
        content_type="application/json",
    )
    chaos = r_answer.get_json()["chaos_state"]
    assert chaos["chaos_energy"] == 50
    assert chaos["consecutive_errors"] == 0


def test_level_complete_unlocks_next_island(client, seeded_user, user_id):
    import core.level_run as level_run

    original = level_run.ISLAND_TASK_COUNT
    level_run.ISLAND_TASK_COUNT = 2
    try:
        r = client.post(
            "/api/game/level/start",
            data=json.dumps({"user_id": user_id, "world": "addition"}),
            content_type="application/json",
        )
        task = r.get_json()["task"]

        for _ in range(2):
            r_answer = client.post(
                "/api/game/answer",
                data=json.dumps(
                    {
                        "user_id": user_id,
                        "answer": task["correct_answer"],
                        "task_id": task["id"],
                        "island_id": "addition",
                        "operation_type": task.get("operation_type", "2digit_add"),
                    }
                ),
                content_type="application/json",
            )
            result = r_answer.get_json()
            if result.get("island_complete"):
                break
            task = result.get("next_task") or task

        assert result.get("island_complete") is True
        assert result.get("boss_pending", {}).get("id") == "null_void"
        assert result.get("unlocked_zone") is None
        profile = client.get(f"/api/player/{user_id}/profile").get_json()
        assert "subtraction" not in profile.get("unlocked_zones", [])
    finally:
        level_run.ISLAND_TASK_COUNT = original


def test_boss_start_and_defeat(client, seeded_user, user_id):
    import core.level_run as level_run

    original = level_run.ISLAND_TASK_COUNT
    level_run.ISLAND_TASK_COUNT = 1
    try:
        client.post(
            "/api/game/level/start",
            data=json.dumps({"user_id": user_id, "world": "addition"}),
            content_type="application/json",
        )
        r = client.post(
            "/api/game/boss/start",
            data=json.dumps({"user_id": user_id, "boss_id": "null_void"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        boss = r.get_json()
        task = boss["task"]

        for _ in range(12):
            r_answer = client.post(
                "/api/game/answer",
                data=json.dumps(
                    {
                        "user_id": user_id,
                        "answer": task["correct_answer"],
                        "task_id": task["id"],
                        "expected_answer": task["correct_answer"],
                        "island_id": "null_void",
                        "operation_type": "boss",
                    }
                ),
                content_type="application/json",
            )
            result = r_answer.get_json()
            if result.get("boss_defeated"):
                break
            task = result.get("next_task") or task

        assert result.get("boss_defeated") is True
        profile = client.get(f"/api/player/{user_id}/profile").get_json()
        assert "null_void" in profile.get("defeated_bosses", [])
        assert "subtraction" in profile.get("unlocked_zones", [])
    finally:
        level_run.ISLAND_TASK_COUNT = original


def test_get_task_requires_user_id(client):
    r = client.get("/api/game/task")
    assert r.status_code == 400


def test_get_task_and_answer_correct(client, seeded_user, user_id):
    r_task = client.get(f"/api/game/task?user_id={user_id}&world=addition")
    assert r_task.status_code == 200
    task = r_task.get_json()
    assert task.get("id")
    assert task.get("correct_answer")

    profile_before = client.get(f"/api/player/{user_id}/profile").get_json()
    balance_before = profile_before["score_balance"]

    r_answer = client.post(
        "/api/game/answer",
        data=json.dumps(
            {
                "user_id": user_id,
                "answer": task["correct_answer"],
                "task_id": task["id"],
                "island_id": task.get("island", "addition"),
                "operation_type": task.get("operation_type", "2digit_add"),
            }
        ),
        content_type="application/json",
    )
    assert r_answer.status_code == 200
    result = r_answer.get_json()
    assert result["correct"] is True
    assert result["new_balance"] > balance_before


def test_transfer_task_has_real_question(client, seeded_user, user_id):
    """После 2 ошибок transfer-задача должна содержать нормальный вопрос, не «Задача addition_N»."""
    r_task = client.get(f"/api/game/task?user_id={user_id}&world=addition")
    task = r_task.get_json()

    payload = {
        "user_id": user_id,
        "answer": "__wrong__",
        "task_id": task["id"],
        "island_id": "addition",
        "operation_type": task.get("operation_type", "2digit_add"),
    }

    for _ in range(2):
        r = client.post(
            "/api/game/check_answer",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert r.status_code == 200
        result = r.get_json()
        assert result["correct"] is False

    transfer = result.get("transfer_task")
    assert transfer is not None
    question = transfer.get("question", "")
    assert question
    assert not question.startswith("Задача addition_")
    assert "+" in question or "×" in question or "÷" in question or "-" in question


def test_answer_wrong_penalty(client, seeded_user, user_id):
    r_task = client.get(f"/api/game/task?user_id={user_id}&world=addition")
    task = r_task.get_json()
    balance_before = client.get(f"/api/player/{user_id}/profile").get_json()["score_balance"]

    try:
        correct_num = int(float(str(task["correct_answer"]).replace(",", ".")))
        wrong_answer = str(correct_num + 99999)
    except (ValueError, TypeError):
        wrong_answer = "__definitely_wrong__"

    r_answer = client.post(
        "/api/game/check_answer",
        data=json.dumps(
            {
                "user_id": user_id,
                "answer": wrong_answer,
                "task_id": task["id"],
                "island_id": "addition",
            }
        ),
        content_type="application/json",
    )
    assert r_answer.status_code == 200
    result = r_answer.get_json()
    assert result["correct"] is False
    assert result["new_balance"] < balance_before


def test_bank_deposit_and_withdraw(client, seeded_user, user_id):
    r_dep = client.post(
        f"/api/bank/{user_id}/deposit",
        data=json.dumps({"amount": 100}),
        content_type="application/json",
    )
    assert r_dep.status_code == 200
    dep = r_dep.get_json()
    assert dep["success"] is True

    bank = client.get(f"/api/bank/{user_id}").get_json()
    assert bank["bank_balance"] == 100
    assert bank["balance"] == 400

    r_wd = client.post(f"/api/bank/{user_id}/withdraw")
    assert r_wd.status_code == 200
    wd = r_wd.get_json()
    assert wd["success"] is True
    assert wd["total"] == 100

    bank_after = client.get(f"/api/bank/{user_id}").get_json()
    assert bank_after["bank_balance"] == 0
    assert bank_after["balance"] == 500


def test_castle_info(client, seeded_user, user_id):
    r = client.get(f"/api/castle/{user_id}")
    assert r.status_code == 200
    data = r.get_json()
    assert "bonuses_active" in data
    assert "decoration_upgrades" in data


def test_artifacts_list(client, seeded_user, user_id):
    r = client.get(f"/api/artifacts/{user_id}")
    assert r.status_code == 200
    assert isinstance(r.get_json(), dict)


def test_alchemy_locked_recipe(client, seeded_user, user_id):
    r = client.post(
        f"/api/alchemy/{user_id}/craft",
        data=json.dumps({"item_id": "bravery_potion"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is False
    assert "открыт" in data["message"].lower()


def test_alchemy_craft_success(client, user_id):
    uid = int(user_id)
    user = storage.get_or_create_user(uid, username="pytest", first_name="PyTest")
    user["score_balance"] = 500
    user["total_score"] = 500
    user["unlocked_zones"] = ["addition", "subtraction"]
    user["inventory"] = []
    storage.save_user(uid, user)

    r = client.post(
        f"/api/alchemy/{user_id}/craft",
        data=json.dumps({"item_id": "bravery_potion"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert "bravery_potion" in storage.get_user(uid).get("inventory", [])
    assert data.get("new_balance") == 350
