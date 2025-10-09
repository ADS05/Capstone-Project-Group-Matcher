class Student:
    def __init__(
        self,
        name: str,
        email: str,
        project_ranks: list[int],
        teammate_ranks: list[str],
        skills: dict[str, int],
        availability: float,
        workstyle: str,
        meeting_pref: str
    ):
        self.name = name
        self.email = email
        self.project_ranks = project_ranks
        self.teammate_ranks = teammate_ranks
        self.skills = skills
        self.availability = availability
        self.workstyle = workstyle
        self.meeting_pref = meeting_pref

    def __repr__(self):
        return f"Student({self.name}, Projects={self.project_ranks}, Skills={self.skills})"