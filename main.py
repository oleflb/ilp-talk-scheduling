from talk_scheduling import (
    solve_assignment,
    Location,
    Talk,
    Attendee,
    AllowedTimes,
    TimeRange,
    TimeSlot,
    ScheduledTalk,
)

import plotly.express as px
import plotly.graph_objects as go


def plot_schedule(schedule: list[ScheduledTalk]) -> go.Figure:
    fig = go.Figure()
    for talk in schedule:
        location = talk.location.name
        start_time = talk.time_slot.index
        end_time = start_time + talk.talk.duration
        title = talk.talk.title

        fig.add_bar(
            x=[location],
            y=[end_time - start_time],
            base=start_time,
            name=title,
            orientation="v",
            text=f"{title} - {talk.talk.speaker.name}<br>Attendees: {
                ', '.join(person.name for person in talk.attendees)}",
            hoverinfo="text",
            opacity=0.8,
        )
    fig.update_layout(
        barmode="stack",
        title="Conference Schedule",
        xaxis_title="Location",
        yaxis_title="Time Slot",
    )
    return fig


def main():
    locations = [
        Location(
            name="Room A",
            capacity=10,
            allowed_times=AllowedTimes(
                times=[TimeRange(start=TimeSlot(5), end=TimeSlot(7))]
            ),
        ),
        Location(
            name="Room B",
            capacity=4,
            allowed_times=AllowedTimes(
                times=[TimeRange(start=TimeSlot(0), end=TimeSlot(4)), TimeRange(start=TimeSlot(10), end=TimeSlot(50))]
            ),
        ),
        Location(
            name="Room C",
            capacity=20,
            allowed_times=AllowedTimes(
                times=[TimeRange(start=TimeSlot(0), end=TimeSlot(10))]
            ),
        ),
    ]
    talks = [
        Talk(
            title="Talk 1",
            speaker=Attendee(name="Alice"),
            duration=2,
            visitor_preferences={
                Attendee(name="Bob"): 1, Attendee(name="Charlie"): 2},
        ),
        Talk(
            title="Talk 2",
            speaker=Attendee(name="Alice"),
            duration=3,
            visitor_preferences={
                Attendee(name="Bob"): 1, Attendee(name="Charlie"): 2},
        ),
        Talk(
            title="Talk 3",
            speaker=Attendee(name="Dave"),
            duration=3,
            visitor_preferences={Attendee(name="Eve"): 10, Attendee(name="Charlie"): 5},
        ),
    ]
    allowed_times = AllowedTimes(
        times=[TimeRange(start=TimeSlot(0), end=TimeSlot(4)), TimeRange(start=TimeSlot(6), end=TimeSlot(50))])

    schedule = solve_assignment(
        talks=talks, locations=locations, allowed_times=allowed_times
    )
    # print(schedule)
    fig = plot_schedule(schedule)
    fig.show()


if __name__ == "__main__":
    main()
