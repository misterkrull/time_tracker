from dataclasses import InitVar, dataclass, field


@dataclass
class Session:
    id: int | None = None
    start_time: int = 0
    end_time: int = 0
    activity_durations: list[int] = field(default_factory=list)
    activity_count: InitVar[int] = 0

    def __post_init__(self, activity_count: int):
        if not self.activity_durations:
            self.activity_durations = [0] * activity_count

        if self.end_time == 0:
            self.end_time = self.start_time

    @property
    def activity_duration_total(self) -> int:
        return sum(self.activity_durations)

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    def is_active(self) -> bool:
        return self.start_time == self.end_time
