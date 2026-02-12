from argparse import Namespace

from scripts.simulate_batch import random_recommendation, run_simulation, seed_demo_data


def test_random_recommendation_returns_reachable_candidate() -> None:
    seed_demo_data()
    choice = random_recommendation(
        source_id="C_LOCAL_A",
        speciality="maternal",
        severity="medium",
        rng=__import__("random").Random(7),
    )
    assert choice is not None
    assert choice.destination_id in {"H_DISTRICT_1", "H_REGIONAL_1"}


def test_random_policy_simulation_produces_valid_distribution() -> None:
    args = Namespace(
        patients=30,
        source="C_LOCAL_A",
        speciality="maternal",
        severity="medium",
        policy="random",
        wait_increment=2,
        recovery_interval=5,
        recovery_amount=1,
        seed_demo=True,
        seed_complex=False,
        fallback_policy="none",
        fallback_overload_penalty=30.0,
        shock_every=0,
        shock_wait_add=0,
        shock_capacity_drop=0,
        random_seed=123,
    )
    report = run_simulation(args)

    assert report["patients_total"] == 30
    assert report["patients_success"] > 0
    assert set(report["destination_distribution"].keys()).issubset({"H_DISTRICT_1", "H_REGIONAL_1"})
    assert "entropy_norm" in report
    assert "hhi" in report
