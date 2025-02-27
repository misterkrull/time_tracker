from dataclasses import InitVar, dataclass, field


@dataclass
class Session:
    id: int | None = None
    start_time: int = 0
    duration: int = 0
    activity_durations: list[int] = field(default_factory=list)
    activity_count: InitVar[int] = 0

    def __post_init__(self, activity_count: int):
        if not self.activity_durations:
            self.activity_durations = [0] * activity_count

    @property
    def activity_duration_total(self):
        return sum(self.activity_durations)
