from talk_scheduling.helpers import pulp_max, pulp_min, pulp_or, pulp_select
from ._types import (
    Location,
    Talk,
    ScheduledTalk,
    Attendee,
    TimeSlot,
    AllowedTimes,
    TimeRange,
)

import pulp
from itertools import combinations


def gather_attendees(talks: list[Talk]) -> set[Attendee]:
    attendees = set()
    for talk in talks:
        attendees.update(talk.visitor_preferences.keys())
        attendees.add(talk.speaker)
    return attendees


def gather_all_possible_start_slots(
    locations: list[Location], allowed_times: AllowedTimes
) -> list[TimeSlot]:
    return sorted(
        {
            ts
            for location in locations
            for ts in location.allowed_times.start_slots()
            if allowed_times.includes(ts)
        }
    )


def solve_assignment(
    *, talks: list[Talk], locations: list[Location], allowed_times: AllowedTimes
) -> list[ScheduledTalk]:
    attendees = gather_attendees(talks)
    start_slots = gather_all_possible_start_slots(locations, allowed_times)

    problem = pulp.LpProblem("TalkScheduling", pulp.LpMaximize)
    pulp_solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=15)

    # y describes start slot of each talk and location
    last_slot = start_slots[-1].index
    M = last_slot + max(talk.duration for talk in talks) + 1
    eps = 1e-8
    y = pulp.LpVariable.dicts(
        "y",
        ((talk, location) for talk in talks for location in locations),
        start_slots[0].index,
        last_slot,
        cat=pulp.LpInteger,
    )
    # is_scheduled describes whether a talk is scheduled at a specific location
    is_scheduled = pulp.LpVariable.dicts(
        "is_scheduled",
        ((talk, location) for talk in talks for location in locations),
        0,
        1,
        cat=pulp.LpBinary,
    )

    # comes_before describes the ordering of talks
    start_comes_before = pulp.LpVariable.dicts(
        "comes_before",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        0,
        1,
        cat=pulp.LpBinary,
    )

    min_end_sel = pulp.LpVariable.dicts(
        "min_end_sel",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        0,
        1,
        cat=pulp.LpBinary,
    )
    max_start_sel = pulp.LpVariable.dicts(
        "max_start_sel",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        0,
        1,
        cat=pulp.LpBinary,
    )
    min_end = pulp.LpVariable.dicts(
        "min_end",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        start_slots[0].index,
        last_slot,
        cat=pulp.LpInteger,
    )
    max_start = pulp.LpVariable.dicts(
        "max_start",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        start_slots[0].index,
        last_slot,
        cat=pulp.LpInteger,
    )

    # conflicts describes the conflicting talks
    conflicts = pulp.LpVariable.dicts(
        "conflicts",
        ((talk_i, talk_j) for talk_i, talk_j in combinations(talks, 2)),
        0,
        1,
        cat=pulp.LpBinary,
    )

    # x describes whether an attendee is assigned to a specific talk
    x = pulp.LpVariable.dicts(
        "x",
        ((talk, attendee) for talk in talks for attendee in attendees),
        0,
        1,
        cat=pulp.LpBinary,
    )

    # Objective function (maximize total visitor preference)
    preference_sum = pulp.lpSum(
        talk.visitor_preferences.get(attendee, 0.1) * x[talk, attendee]
        for talk in talks
        for attendee in attendees
    )
    # 2nd Objective: Minimize latest start
    latest_end = pulp.LpVariable("latest_start", 0, last_slot, cat=pulp.LpInteger)
    for talk in talks:
        for location in locations:
            problem += y[(talk, location)] + talk.duration <= latest_end

    problem += preference_sum - 0.001 * latest_end

    # Each task must be scheduled exactly once
    for talk in talks:
        problem += (
            pulp.lpSum(is_scheduled[(talk, location)] for location in locations) == 1
        )
        for location in locations:
            problem += y[(talk, location)] <= last_slot * is_scheduled[(talk, location)]

    # Constrains for if task i start < task j start
    for talk_i, talk_j in combinations(talks, 2):
        talk_i_start = pulp.lpSum(y[(talk_i, location)] for location in locations)
        talk_j_start = pulp.lpSum(y[(talk_j, location)] for location in locations)
        pulp_min(
            problem,
            talk_i_start,
            talk_j_start,
            1 - start_comes_before[(talk_i, talk_j)],
            M=M,
        )

    # Talks may not overlap in the same location
    for location in locations:
        for talk_i, talk_j in combinations(talks, 2):
            duration_i = talk_i.duration
            duration_j = talk_j.duration
            talk_i_scheduled = is_scheduled[(talk_i, location)]
            talk_j_scheduled = is_scheduled[(talk_j, location)]
            problem += y[(talk_i, location)] + duration_i - (
                1 - talk_i_scheduled
            ) * M <= y[(talk_j, location)] + M * (
                1 - start_comes_before[(talk_i, talk_j)]
            ) + M * (1 - talk_j_scheduled)
            problem += y[(talk_j, location)] + duration_j - (
                1 - talk_j_scheduled
            ) * M <= y[(talk_i, location)] + M * start_comes_before[
                (talk_i, talk_j)
            ] + M * (1 - talk_i_scheduled)

    # Talks conflict if they overlap in time
    for talk_i, talk_j in combinations(talks, 2):
        duration_i = talk_i.duration
        duration_j = talk_j.duration
        start_i = pulp.lpSum(y[(talk_i, location)] for location in locations)
        start_j = pulp.lpSum(y[(talk_j, location)] for location in locations)
        end_i = start_i + duration_i
        end_j = start_j + duration_j
        con = conflicts[(talk_i, talk_j)]

        end_sel = min_end_sel[(talk_i, talk_j)]
        min_end_value = min_end[(talk_i, talk_j)]
        pulp_min(problem, end_i, end_j, end_sel, M=M)
        pulp_select(problem, end_i, end_j, min_end_value, end_sel, M=M)

        start_sel = max_start_sel[(talk_i, talk_j)]
        max_start_value = max_start[(talk_i, talk_j)]
        pulp_max(problem, start_i, start_j, start_sel, M=M)
        pulp_select(problem, start_i, start_j, max_start_value, start_sel, M=M)

        overlap = min_end_value - max_start_value
        pulp_max(problem, 0, overlap, con, M=M)

    # Each attendee can be only at one talk at a time
    for attendee in attendees:
        for talk_i, talk_j in combinations(talks, 2):
            problem += (
                x[(talk_i, attendee)] + x[(talk_j, attendee)]
                <= 2 - conflicts[(talk_i, talk_j)]
            )

    # Each speaker must attend their own talk
    for talk in talks:
        speaker = talk.speaker
        problem += x[talk, speaker] == 1

    or_variables = pulp.LpVariable.dicts(
        "time_range_selector",
        (
            (talk, location, time_range_index)
            for talk in talks
            for location in locations
            for time_range_index in range(location.allowed_times.number_of_ranges())
        ),
        0,
        1,
        cat=pulp.LpBinary,
    )

    for talk in talks:
        for location in locations:
            scheduled = is_scheduled[(talk, location)]
            start_time = y[(talk, location)]
            end_time = start_time + talk.duration

            or_variable = [
                or_variables[(talk, location, time_range_index)]
                for time_range_index in range(location.allowed_times.number_of_ranges())
            ]
            pulp_or(
                problem,
                *[
                    [
                        start_time >= time_range.start.index - M * (1 - scheduled),
                        end_time <= time_range.end.index + M * (1 - scheduled),
                    ]
                    for time_range in location.allowed_times.times
                ],
                or_variables=or_variable,
                number_of_true_terms=scheduled,
                M=M,
            )

    # global_or_variables = pulp.LpVariable.dicts(
    #     "global_time_range_selector",
    #     (
    #         (talk, time_range_index)
    #         for talk in talks
    #         for time_range_index in range(allowed_times.number_of_ranges())
    #     ),
    #     0,
    #     1,
    #     cat=pulp.LpBinary,
    # )

    # for talk in talks:
    #     start_time = pulp.lpSum(y[(talk, location)] for location in locations)
    #     scheduled = pulp.lpSum(is_scheduled[(talk, location)] for location in locations)
    #     end_time = start_time + talk.duration

    #     global_or_variable = [
    #         global_or_variables[(talk, time_range_index)]
    #         for time_range_index in range(allowed_times.number_of_ranges())
    #     ]
    #     pulp_or(
    #         problem,
    #         *[
    #             [
    #                 start_time >= time_range.start.index,
    #                 end_time <= time_range.end.index,
    #             ]
    #             for time_range in allowed_times.times
    #         ],
    #         or_variables=global_or_variable,
    #         number_of_true_terms=scheduled,
    #         M=M,
    #     )

    for talk in talks:
        for location in locations:
            scheduled = is_scheduled[(talk, location)]
            number_of_attendees = pulp.lpSum(
                x[talk, attendee] for attendee in attendees
            )
            problem += number_of_attendees <= location.capacity + M * (1 - scheduled)

    problem.solve(pulp_solver)

    status = pulp.LpStatus[problem.status]
    objective = pulp.value(problem.objective)

    print(f"Status: {status}")
    print(f"Objective: {objective}")
    print("Latest end", pulp.value(latest_end))
    print("Preference sum", pulp.value(preference_sum))

    for talk in talks:
        for location in locations:
            print(
                talk.title,
                location.name,
                pulp.value(is_scheduled[(talk, location)]),
                pulp.value(y[(talk, location)]),
            )

    for talk_i, talk_j in combinations(talks, 2):
        print(
            f"{talk_i.title} comes before {talk_j.title}:",
            pulp.value(start_comes_before[(talk_i, talk_j)]),
        )
        print(
            f"{talk_i.title} conflicts with {talk_j.title}:",
            pulp.value(conflicts[(talk_i, talk_j)]),
        )

    for talk in talks:
        for attendee in attendees:
            print(
                f"{attendee.name} assigned to {talk.title}:",
                pulp.value(x[talk, attendee]),
            )

    schedule: list[ScheduledTalk] = []

    for talk in talks:
        for location in locations:
            if pulp.value(is_scheduled[(talk, location)]) == 0:
                continue
            # Find the start slot for the talk at this location
            start_slot = pulp.value(y[talk, location])
            attending = [
                attendee for attendee in attendees if pulp.value(x[talk, attendee]) == 1
            ]
            schedule.append(
                ScheduledTalk(
                    talk=talk,
                    time_slot=TimeSlot(start_slot),
                    location=location,
                    attendees=attending,
                )
            )

    return schedule
