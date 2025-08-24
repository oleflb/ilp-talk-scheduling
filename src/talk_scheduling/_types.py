from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class TimeSlot:
    index: int


@dataclass(kw_only=True, frozen=True)
class Attendee:
    name: str


@dataclass(kw_only=True)
class Talk:
    title: str
    speaker: Attendee
    duration: int  # Number of time slots
    visitor_preferences: dict[Attendee, int]

    def __hash__(self):
        return hash(
            (
                self.title,
                self.speaker,
                self.duration,
                frozenset(self.visitor_preferences.items()),
            )
        )


@dataclass(kw_only=True, frozen=True)
class TimeRange:
    start: TimeSlot
    end: TimeSlot

    def start_slots(self) -> list[TimeSlot]:
        return [TimeSlot(index) for index in range(self.start.index, self.end.index)]

    def includes(self, slot: TimeSlot) -> bool:
        return self.start.index <= slot.index < self.end.index


@dataclass(kw_only=True)
class AllowedTimes:
    times: list[TimeRange]

    def start_slots(self) -> list[TimeSlot]:
        return sorted(
            {slot for time_range in self.times for slot in time_range.start_slots()}
        )
    
    def number_of_ranges(self) -> int:
        return len(self.times)

    def includes(self, slot: TimeSlot) -> bool:
        return any(time_range.includes(slot) for time_range in self.times)

    def __hash__(self):
        return hash(tuple(self.times))


@dataclass(kw_only=True, frozen=True)
class Location:
    name: str
    capacity: int
    allowed_times: AllowedTimes


@dataclass(kw_only=True, frozen=True)
class ScheduledTalk:
    talk: Talk
    time_slot: TimeSlot
    location: Location
    attendees: list[Attendee]
