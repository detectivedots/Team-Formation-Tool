import pandas as pd


class CSVHandler:
    df = pd.DataFrame()
    needed_columns = ["Has teammate", "Member 1 name", "Member 1 handle", "Member 2 name", "Member 2 handle"]

    def __init__(self, file_path):
        self.df = pd.read_csv(file_path)

    def get_column_names(self):
        return list(self.df.columns)

    def rename_columns(self, name_changes: dict):
        self.df = self.df.rename(columns=dict(zip(name_changes.values(), name_changes.keys())))

    def preprocess(self):
        self.df = self.df[self.needed_columns]
        self.df["Has teammate"] = (self.df["Has teammate"] == "فردين")

        def clean_handle(handle: str):
            if not isinstance(handle, str) or handle.strip() == '':
                return ""
            return handle.strip().split("/profile/")[-1].lower()

        self.df['Member 1 handle'] = self.df['Member 1 handle'].astype("object")
        self.df['Member 2 handle'] = self.df['Member 2 handle'].astype("object")
        self.df['Member 1 handle'] = self.df['Member 1 handle'].apply(clean_handle)
        self.df['Member 2 handle'] = self.df['Member 2 handle'].apply(clean_handle)

    def get_handles_list(self):
        return list(set(self.df['Member 1 handle']) | set(self.df['Member 2 handle']))

    def save_pre_contest_csv(self, path):
        df1 = self.df[["Member 1 name", "Member 1 handle"]].copy()
        df1.columns = ["Name", "Handle"]
        df1["TeamID"] = self.df.index
        df1["Attended"] = False
        df1["Practice"] = False
        df1["Seat"] = 0
        df1["Rank"] = 0

        df2 = self.df[self.df['Has teammate']][["Member 2 name", "Member 2 handle"]].copy()
        df2.columns = ["Name", "Handle"]
        df2["TeamID"] = self.df[self.df['Has teammate']].index
        df2["Attended"] = False
        df2["Practice"] = False
        df2["Seat"] = 0
        df2["Rank"] = 0

        save_df = pd.concat([df1, df2], ignore_index=True)
        save_df = save_df.drop_duplicates(subset=["Handle"])
        save_df.to_csv(path, index=False)

    def get_initial_teams(self):
        return list(zip(self.df[self.df["Has teammate"]]["Member 1 handle"],
                        self.df[self.df["Has teammate"]]["Member 2 handle"]))
