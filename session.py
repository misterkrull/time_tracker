from dataclasses import dataclass, field


@dataclass
class Subsession:
    start_time: int
    activity_id: int
    end_time: int = 0

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time if self.end_time > self.start_time else 0

    def is_active(self) -> bool:
        return self.end_time == 0


@dataclass
class Session:
    id: int | None = None
    start_time: int = 0
    end_time: int = 0
    subsessions: list[Subsession] = field(default_factory=list)

    def __post_init__(self):
        if self.end_time == 0:
            self.end_time = self.start_time

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    def is_active(self) -> bool:
        if self.id is None:
            return False
        return self.start_time == self.end_time

    def get_activity_duration(self, activity_id: int) -> int:
        return sum(subs.duration for subs in self.subsessions if subs.activity_id == activity_id)
