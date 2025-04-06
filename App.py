import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from CSVHandler import CSVHandler
import pandas as pd
from TeamMatching import *


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Team Matching App")
        self.geometry("900x650")

        self.file_path = filedialog.askopenfilename(
            title="Select original CSV file",
            filetypes=[("CSV File", "*.csv")]
        )
        self.csv_handler = CSVHandler(file_path=self.file_path)
        self.rename_window(self.csv_handler)
        self.csv_handler.preprocess()

        open_text_btn = tk.Button(self, text="Get All Handles",
                                  command=lambda: self.open_text_window("\n".join(self.csv_handler.get_handles_list())))
        open_text_btn.pack(pady=5)

        save_fil_btn = tk.Button(self, text="Save Pre Contest CSV", command=self.open_save_window)
        save_fil_btn.pack(pady=5)

        separator = tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=10)

        tk.Label(self, text="Contest CSV (with ranks, Attended, Practice)").pack()
        import_contest_btn = tk.Button(self, text="Import Contest CSV", command=self.import_contest_csv)
        import_contest_btn.pack(pady=5)

        self.team_frame = tk.Frame(self)
        self.team_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.team_listbox = tk.Listbox(self.team_frame, width=120, height=10)
        self.team_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        action_frame = tk.Frame(self)
        action_frame.pack(pady=10)

        suggest_btn = tk.Button(action_frame, text="Suggest Team Match", command=self.suggest_match)
        suggest_btn.grid(row=0, column=0, padx=5)

        decline_btn = tk.Button(action_frame, text="Decline Suggestion", command=self.prompt_skip_member)
        decline_btn.grid(row=0, column=1, padx=5)

        reset_skips_btn = tk.Button(action_frame, text="Reset Skips", command=self.reset_skips)
        reset_skips_btn.grid(row=0, column=2, padx=5)

        split_btn = tk.Button(action_frame, text="Split Selected Team", command=self.split_selected_team)
        split_btn.grid(row=0, column=3, padx=5)

        match_by_handle_btn = tk.Button(action_frame, text="Match by Handle", command=self.match_by_handle)
        match_by_handle_btn.grid(row=0, column=4, padx=5)

        finalize_btn = tk.Button(action_frame, text="Finalize Teams (Export CSV)", command=self.finalize_teams)
        finalize_btn.grid(row=0, column=5, padx=5)

        self.team_matching = None
        self.suggested_indices = None

    def rename_window(self, csv_handler):
        window = tk.Toplevel(self)
        window.title("Rename Columns")
        available_columns = csv_handler.get_column_names()
        listboxes = {}
        for row, req_col in enumerate(CSVHandler.needed_columns):
            label = tk.Label(window, text=req_col)
            label.grid(row=row, column=0, padx=5, pady=5, sticky='w')
            lb = tk.Listbox(window, selectmode=tk.SINGLE, exportselection=False, height=min(6, len(available_columns)))
            for name in available_columns:
                lb.insert(tk.END, name)
            lb.grid(row=row, column=1, padx=5, pady=5)
            listboxes[req_col] = lb

        def submit():
            name_changes = {}
            for req_col, lb in listboxes.items():
                selection = lb.curselection()
                if selection:
                    selected_value = lb.get(selection[0])
                    name_changes[req_col] = selected_value
            csv_handler.rename_columns(name_changes)
            window.destroy()

        submit_btn = tk.Button(window, text="Submit", command=submit)
        submit_btn.grid(row=len(CSVHandler.needed_columns), column=0, columnspan=2, pady=10)
        self.wait_window(window)

    def open_text_window(self, text_content):
        new_window = tk.Toplevel(self)
        new_window.title("Text Viewer")
        text_widget = tk.Text(new_window, wrap=tk.WORD, height=10, width=50)
        text_widget.insert("1.0", text_content)
        text_widget.config(state="disabled")
        text_widget.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(text_content)
            print("Text copied to clipboard.")

        copy_btn = tk.Button(new_window, text="Copy", command=copy_to_clipboard)
        copy_btn.pack(pady=5)

    def open_save_window(self):
        file_path = filedialog.asksaveasfilename(
            title="Save file as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.csv_handler.save_pre_contest_csv(file_path)
            messagebox.showinfo("Saved", f"Pre Contest CSV saved to {file_path}")

    def import_contest_csv(self):
        contest_file = filedialog.askopenfilename(
            title="Select Contest CSV (with ranks)",
            filetypes=[("CSV File", "*.csv")]
        )
        if not contest_file:
            return
        contest_df = pd.read_csv(contest_file)
        filtered = contest_df[(contest_df["Attended"] == True) & (contest_df["Practice"] == False)]
        teams = []
        if "TeamID" in filtered.columns:
            grouped = filtered.groupby("TeamID")
            for team_id, group in grouped:
                contestants = []
                for _, row in group.iterrows():
                    try:
                        rank = float(row["Rank"])
                    except:
                        rank = 1000
                    contestants.append(Contestant(name=row["Name"], handle=row["Handle"], rank=rank))
                if len(contestants) >= 2:
                    teams.append(Team(contestants[0]))
                elif len(contestants) == 1:
                    teams.append(Team(contestants[0]))
                elif len(contestants) >= 3:
                    teams.append(Team(contestants[0], contestants[1], contestants[2]))
        else:
            for _, row in filtered.iterrows():
                try:
                    rank = float(row["Rank"])
                except:
                    rank = 1000
                teams.append(Team(Contestant(name=row["Name"], handle=row["Handle"], rank=rank)))
        if not teams:
            messagebox.showwarning("No Contestants", "No valid contestants found in the CSV.")
            return
        self.team_matching = TeamMatching(teams)
        self.refresh_team_display()

    def refresh_team_display(self):
        self.team_listbox.delete(0, tk.END)
        if self.team_matching:
            for i, team in enumerate(self.team_matching.teams):
                self.team_listbox.insert(tk.END, f"Team {i}: {team}")
        else:
            self.team_listbox.insert(tk.END, "No teams available.")

    def suggest_match(self):
        if not self.team_matching:
            messagebox.showwarning("No Teams", "Please import the contest CSV first.")
            return
        suggestion = self.team_matching.suggest_team()
        if suggestion is None:
            messagebox.showinfo("Suggestion", "No valid team suggestion found. Consider splitting teams.")
            return
        self.suggested_indices = suggestion
        suggested_str = "\n".join(str(self.team_matching.teams[i]) for i in suggestion)
        sug_win = tk.Toplevel(self)
        sug_win.title("Team Match Suggestion")
        tk.Label(sug_win, text="Suggested teams to merge:").pack(pady=5)
        tk.Message(sug_win, text=suggested_str, width=600).pack(pady=5)

        def accept():
            self.team_matching.match_by_index(self.suggested_indices)
            self.refresh_team_display()
            sug_win.destroy()

        def decline():
            sug_win.destroy()
            self.prompt_skip_member()

        btn_frame = tk.Frame(sug_win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Accept", command=accept).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Decline", command=decline).grid(row=0, column=1, padx=5)

    def prompt_skip_member(self):
        if not self.suggested_indices:
            messagebox.showinfo("No Suggestion", "No suggested teams to choose from.")
            return
        skip_win = tk.Toplevel(self)
        skip_win.title("Select Member to Skip")
        tk.Label(skip_win, text="Select a member to skip from the suggested teams:").pack(pady=5)

        member_listbox = tk.Listbox(skip_win, selectmode=tk.SINGLE, width=80)
        member_listbox.pack(padx=10, pady=10)
        mapping = {}
        idx = 0
        for team_idx in self.suggested_indices:
            team = self.team_matching.teams[team_idx]
            for m_idx, member in enumerate(team.members):
                entry = f"Team {team_idx}: {member.name} ({member.handle}), rank: {member.rank}"
                member_listbox.insert(tk.END, entry)
                mapping[idx] = (team_idx, m_idx)
                idx += 1

        def do_skip():
            selection = member_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a member to skip.")
                return
            chosen = selection[0]
            team_idx, member_idx = mapping[chosen]
            self.team_matching.skip_member(team_idx, member_idx)
            self.refresh_team_display()
            skip_win.destroy()

        tk.Button(skip_win, text="Skip Selected Member", command=do_skip).pack(pady=5)

    def reset_skips(self):
        if self.team_matching:
            self.team_matching.clear_skipped()
            self.refresh_team_display()

    def split_selected_team(self):
        if not self.team_matching:
            return
        selected = self.team_listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a team to split.")
            return
        index = selected[0]
        team = self.team_matching.teams[index]
        if len(team) == 1:
            messagebox.showinfo("Already Single", "This team has only one member.")
            return
        self.team_matching.split_team(team)
        self.refresh_team_display()

    def match_by_handle(self):
        if not self.team_matching:
            return
        handles_str = simpledialog.askstring("Match by Handle", "Enter handles (comma separated):")
        if not handles_str:
            return
        handles = [h.strip() for h in handles_str.split(",") if h.strip()]
        self.team_matching.match_by_handle(handles)
        self.refresh_team_display()

    def finalize_teams(self):
        if not self.team_matching:
            return
        rows = []
        for i, team in enumerate(self.team_matching.teams):
            for member in team.members:
                rows.append({
                    "Team": i,
                    "Name": member.name,
                    "Handle": member.handle,
                    "Rank": member.rank
                })
        final_df = pd.DataFrame(rows)
        file_path = filedialog.asksaveasfilename(
            title="Save Final Teams CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            final_df.to_csv(file_path, index=False)
            messagebox.showinfo("Saved", f"Final teams CSV saved to {file_path}")
