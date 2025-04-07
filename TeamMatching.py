class Contestant:
    def __init__(self, name, handle, rank):
        self.name = name
        self.handle = handle
        self.rank = rank

    def __str__(self):
        return f"{self.name} ({self.handle}), rank: {self.rank}"


class Team:
    def __init__(self, contestant1: Contestant, contestant2: Contestant = None, contestant3: Contestant = None):
        self.members = [contestant1]
        if contestant2:
            self.members.append(contestant2)
        if contestant3:
            self.members.append(contestant3)

    def __len__(self):
        return len(self.members)

    def get_team_rank(self):
        return min(cont.rank for cont in self.members)

    def __lt__(self, other) -> bool:
        if len(self) == 3:
            return False
        if len(other) == 3:
            return True
        return self.get_team_rank() < other.get_team_rank()

    def __str__(self):
        team_str = " | ".join(str(member) for member in self.members)
        if len(self) == 3:
            team_str += "  [FULL]"
        return team_str


class TeamMatching:
    def __init__(self, teams: list[Team], handles):
        self.teams = sorted(teams)
        self.skipped = []  # (team_index, contestant) pairs skipped
        self.handles = set(handles)

    def suggest_team(self):
        if len(self.teams) < 2 or len(self.teams[0]) == 3 or len(self.teams[1]) == 3:
            print("Sorry, can't match, please reset skipped teams")
            return None
        team_indices = []
        size = 0
        for i, t in enumerate(self.teams):
            if size + len(t) <= 3:
                size += len(t)
                team_indices.append(i)
            if size == 3:
                break
        if size < 3:
            print("Consider splitting teams")
            return None
        return team_indices

    def clear_skipped(self):
        for (_, skipped_member) in self.skipped:
            self.teams.append(Team(skipped_member))
        self.skipped = []
        self.teams = sorted(self.teams)

    def split_team(self, team: Team):
        if team in self.teams:
            self.teams.remove(team)
            for contestant in team.members:
                self.teams.append(Team(contestant))
            self.clear_skipped()

    def match_by_index(self, indices: list[int]):
        indices = sorted(indices, reverse=True)
        merged_members = []
        for index in indices:
            merged_members.extend(self.teams[index].members)
            self.teams.pop(index)
        new_team = Team(*merged_members)
        self.teams.append(new_team)
        self.clear_skipped()
        self.teams = sorted(self.teams)

    def match_by_handle(self, handles: list[str]):
        indices = []
        for handle in handles:
            for i, team in enumerate(self.teams):
                for cont in team.members:
                    if cont.handle.strip().lower() == handle.strip().lower():
                        if i not in indices:
                            indices.append(i)
                        break
        if len(indices) < 2:
            print("At least two different contestants must be selected for matching.")
            return
        self.match_by_index(indices)

    def skip_member(self, team_index: int, member_index: int):
        team = self.teams[team_index]
        skipped_member = team.members.pop(member_index)
        self.skipped.append((team_index, skipped_member))
        if len(team) == 0:
            self.teams.pop(team_index)
        self.teams = sorted(self.teams)

    def match_handle_pairs(self, pairs):
        matched = set()
        for pair in pairs:
            if pair[0] == pair[1]:
                continue
            if pair[0] > pair[1]:
                pair = (pair[1], pair[0])
            if pair in matched:
                continue
            matched.add(pair)
            if pair[0] in self.handles and pair[1] in self.handles:
                self.match_by_handle(pair)